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
from exceptions import DexError, PriceManipulationError, ServiceUnavailableError
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
from tokens.detect import (
    ERC20_ABI,
    TokenInspectionError,
    TokenType,
    detect_token_type,
    gas_multiplier,
    get_token_balance,
)
from slippage_protection import SlippageProtectionEngine
from logger import get_logger
from observability.decorators import log_and_measure
from observability.metrics import (
    TRADE_COUNT,
    TRADE_SUCCESS,
    SLIPPAGE_APPLIED,
    SLIPPAGE_VIOLATIONS,
)

logger = get_logger("dex_handler")

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

    @log_and_measure("dex_handler", warn_ms=500)
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

    @log_and_measure("dex_handler", warn_ms=5000)
    async def _do_swap(
        self, amount_in_wei: int, path: List[str], amount_out_min: int
    ) -> str:
        to_address = self.web3_service.account.address
        token_out = path[-1]
        deadline = int(time.time()) + 300
        contract = self.web3_service.get_contract(token_out, ERC20_ABI)
        try:
            token_type = await detect_token_type(contract)
        except TokenInspectionError:
            token_type = TokenType.ERC20
        multiplier = gas_multiplier(token_type)
        balance_before = await get_token_balance(contract, to_address)
        tx_params = (
            self.contract.functions.swapExactETHForTokens(
                amount_out_min, path, to_address, deadline
            ).build_transaction(
                {
                    "from": to_address,
                    "value": amount_in_wei,
                    "gas": int(250000 * multiplier),
                    "gasPrice": self.web3_service.web3.eth.gas_price,
                }
            )
        )
        receipt = await self.web3_service.sign_and_send_transaction(tx_params)
        balance_after = await get_token_balance(contract, to_address)
        if balance_after <= balance_before:
            raise DexError("token balance check failed")
        return receipt["transactionHash"].hex()
    async def execute_swap(
        self,
        amount_in_wei: int,
        path: List[str]
    ) -> str:
        """Execute swap with circuit breaker and retry logic."""
        try:
            amounts = await asyncio.to_thread(
                self.contract.functions.getAmountsOut(amount_in_wei, path).call
            )
            expected_out = int(amounts[-1])
            amount_out_min = SlippageProtectionEngine.calculate_protected_slippage(
                expected_out
            )
            slippage_pct = (
                (expected_out - amount_out_min) * 100 / expected_out
                if expected_out
                else 0.0
            )
            SLIPPAGE_APPLIED.observe(slippage_pct)
            try:
                SlippageProtectionEngine.validate_transaction_slippage(
                    expected_out, amount_out_min
                )
            except PriceManipulationError as exc:
                SLIPPAGE_VIOLATIONS.inc()
                raise DexError(str(exc)) from exc
            tx_hash = await self._circuit.call(
                retry_async,
                self._do_swap,
                amount_in_wei,
                path,
                amount_out_min,
            )
            TRADE_COUNT.inc()
            TRADE_SUCCESS.inc()
            return tx_hash
        except ServiceUnavailableError as exc:
            logger.error("Swap circuit open: %s", exc)
            raise DexError("service unavailable") from exc
        except (TransactionFailedError, TransactionTimeoutError) as exc:
            logger.error("Swap execution failed: %s", exc)
            raise DexError(str(exc)) from exc

