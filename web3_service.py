# web3_service.py
# /usr/bin/env python3

"""
Service layer for interacting with the Ethereum blockchain.

This module encapsulates all web3.py calls, providing a simplified
interface for connecting to a node, creating contract instances,
and sending signed transactions.
"""

import time
from typing import Any, Dict, List, Optional

from web3 import Web3, HTTPProvider
from web3.contract import Contract
try:
    from web3.middleware import geth_poa_middleware
except ImportError:  # web3 v7
    from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware as geth_poa_middleware
from web3.types import TxParams, TxReceipt
from web3.exceptions import TimeExhausted


class TransactionFailedError(Exception):
    """Custom exception for failed on-chain transactions."""
    pass


class TransactionTimeoutError(Exception):
    """Raised when a transaction does not get mined within the expected time."""
    pass


class Web3Service:
    """A service to handle all Ethereum blockchain interactions."""

    def __init__(self, rpc_url: str, private_key: str):
        """
        Initializes the connection to the Ethereum node.

        Args:
            rpc_url: The HTTP provider URL for the Ethereum node.
            private_key: The private key for signing transactions.
        """
        self.web3 = Web3(HTTPProvider(rpc_url))
        # Inject middleware for POA chains like Polygon, Rinkeby, etc.
        self.web3.middleware_onion.inject(geth_poa_middleware, layer=0)

        if not self.web3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node.")

        self.account = self.web3.eth.account.from_key(private_key)
        self.web3.eth.default_account = self.account.address

    def get_contract(self, address: str, abi: List[Dict]) -> Contract:
        """
        Loads a smart contract instance from its address and ABI.

        Args:
            address: The checksummed address of the smart contract.
            abi: The Application Binary Interface (ABI) of the contract.

        Returns:
            A web3.py Contract object ready for interaction.
        """
        checksum_address = self.web3.to_checksum_address(address)
        return self.web3.eth.contract(address=checksum_address, abi=abi)

    def sign_and_send_transaction(
        self, transaction: TxParams, timeout: int = 120, retries: int = 3
    ) -> TxReceipt:
        """Sign and send a transaction with retry and timeout logic."""
        if "nonce" not in transaction:
            transaction["nonce"] = self.web3.eth.get_transaction_count(self.account.address)

        for attempt in range(retries):
            signed = self.web3.eth.account.sign_transaction(transaction, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed.rawTransaction)
            try:
                receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            except TimeExhausted:
                if attempt == retries - 1:
                    raise TransactionTimeoutError(f"Transaction {tx_hash.hex()} timed out")
                time.sleep(1)
                transaction["nonce"] = self.web3.eth.get_transaction_count(self.account.address)
                continue
            if receipt["status"] == 0:
                raise TransactionFailedError(
                    f"Transaction {tx_hash.hex()} failed."
                )
            return receipt
        raise TransactionTimeoutError("Max retries exceeded")  # pragma: no cover
