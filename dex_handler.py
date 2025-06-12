# /usr/bin/env python3
# dex_handler.py
"""
Handles interactions with Decentralized Exchange (DEX) smart contracts.

This module provides an abstraction for querying prices and executing
swaps on DEXs that follow the Uniswap V2 protocol.
"""

import time
import asyncio
from typing import Any, Dict, Final, List

from web3.contract import Contract
from web3.exceptions import ContractLogicError

import config
from web3_service import (
    Web3Service,
    TransactionFailedError,
    TransactionTimeoutError,
)
from exceptions import DexError, ServiceUnavailableError
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
from logger import logger

# A minimal ABI for the Uniswap V2 Router is sufficient for our needs.
UNISWAP_V2_ROUTER_ABI: Final[List[Dict[str, Any]]] = [
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"}
        ],
        "name": "getAmountsOut",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "amountOutMin", "type": "uint256"},
            {"internalType": "address[]", "name": "path", "type": "address[]"},
            {"internalType": "address", "name": "to", "type": "address"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"}
        ],
        "name": "swapExactETHForTokens",
        "outputs": [
            {"internalType": "uint256[]", "name": "amounts", "type": "uint256"}
        ],
        "stateMutability": "payable",
        "type": "function"
    }
]


class DEXHandler:
    """Handles price queries and swaps on a specific DEX."""

    def __init__(self, web3_service: Web3Service, router_address: str):
        """
        Initializes the handler for a specific DEX router.

        Args:
            web3_service: The configured Web3Service instance.
            router_address: The address of the DEX router contract.
        """
        self.web3_service = web3_service
        self.router_address = router_address
        self.contract: Contract = web3_service.get_contract(
            router_address, UNISWAP_V2_ROUTER_ABI
        )
        self._circuit = CircuitBreaker()

    async def _query_price(
        self, token_in_address: str, token_out_address: str, amount_in: int
    ) -> float:
        path = [token_in_address, token_out_address]
        amounts_out = await asyncio.to_thread(
            self.contract.functions.getAmountsOut(amount_in, path).call
        )
        return amounts_out[1] / (10**18)

    async def get_price(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: int = 10**18,
    ) -> float:
        """Get price with circuit breaker and retry logic."""
        try:
            return await self._circuit.call(
                retry_async,
                self._query_price,
                token_in_address,
                token_out_address,
                amount_in,
            )
        except ServiceUnavailableError as exc:
            logger.error("Price circuit open: %s", exc)
            return 0.0
        except (ContractLogicError, ValueError) as exc:
            logger.warning("Price query failed: %s", exc)
            return 0.0

    async def _do_swap(self, amount_in_wei: int, path: List[str]) -> str:
        amount_out_min = 0
        to_address = self.web3_service.account.address
        deadline = int(time.time()) + 60 * 5
        tx_params = self.contract.functions.swapExactETHForTokens(
            amount_out_min,
            path,
            to_address,
            deadline,
        ).build_transaction(
            {
                "from": to_address,
                "value": amount_in_wei,
                "gas": 250000,
                "gasPrice": self.web3_service.web3.eth.gas_price,
            }
        )
        receipt = self.web3_service.sign_and_send_transaction(tx_params)
        return receipt["transactionHash"].hex()

    async def execute_swap(
        self,
        amount_in_wei: int,
        path: List[str]
    ) -> str:
        """Execute swap with circuit breaker and retry logic."""
        try:
            return await self._circuit.call(
                retry_async,
                self._do_swap,
                amount_in_wei,
                path,
            )
        except ServiceUnavailableError as exc:
            logger.error("Swap circuit open: %s", exc)
            raise DexError("service unavailable") from exc
        except (TransactionFailedError, TransactionTimeoutError) as exc:
            logger.error("Swap execution failed: %s", exc)
            raise DexError(str(exc)) from exc

