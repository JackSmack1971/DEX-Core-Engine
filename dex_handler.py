# /usr/bin/env python3
# dex_handler.py
"""
Handles interactions with Decentralized Exchange (DEX) smart contracts.

This module provides an abstraction for querying prices and executing
swaps on DEXs that follow the Uniswap V2 protocol.
"""

import time
from typing import List, Dict, Any, Final

from web3.contract import Contract
from web3.exceptions import ContractLogicError

import config
from web3_service import Web3Service

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

    def get_price(
        self,
        token_in_address: str,
        token_out_address: str,
        amount_in: int = 10**18  # Default to 1 ETH/WETH
    ) -> float:
        """
        Gets the current price for a token pair.

        Args:
            token_in_address: Address of the input token.
            token_out_address: Address of the output token.
            amount_in: The amount of input token to query the price for.

        Returns:
            The amount of output tokens received for the input amount,
            or 0.0 if the query fails.
        """
        try:
            path = [token_in_address, token_out_address]
            amounts_out = self.contract.functions.getAmountsOut(
                amount_in, path
            ).call()
            # Assuming the output token has 18 decimals, a common standard
            return amounts_out[1] / (10**18)
        except (ContractLogicError, ValueError):
            # Handle cases where the liquidity pool might not exist
            return 0.0

    def execute_swap(
        self,
        amount_in_wei: int,
        path: List[str]
    ) -> str:
        """
        Executes a swap from ETH to a specified token.

        Args:
            amount_in_wei: The amount of ETH (in Wei) to swap.
            path: The token swap path, starting with WETH.

        Returns:
            The transaction hash of the executed swap.
        """
        amount_out_min = 0  # For simplicity; a real bot should calculate this
        to_address = self.web3_service.account.address
        deadline = int(time.time()) + 60 * 5  # 5 minutes from now

        tx_params = self.contract.functions.swapExactETHForTokens(
            amount_out_min,
            path,
            to_address,
            deadline
        ).build_transaction({
            'from': to_address,
            'value': amount_in_wei,
            'gas': 250000, # Set a reasonable gas limit
            'gasPrice': self.web3_service.web3.eth.gas_price
        })

        receipt = self.web3_service.sign_and_send_transaction(tx_params)
        return receipt['transactionHash'].hex()
