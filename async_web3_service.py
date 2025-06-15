from __future__ import annotations

"""Asynchronous Web3 service with secure key handling."""

import asyncio
import random
from typing import Any, Dict, List

from eth_account import Account
from web3 import AsyncHTTPProvider, AsyncWeb3
from web3.exceptions import TimeExhausted
from web3.middleware import proof_of_authority
from web3.middleware.signing import SignAndSendRawMiddlewareBuilder
from web3.types import TxParams, TxReceipt

from logger import get_logger
from security import SecureKeyManager, secure_zero_memory

logger = get_logger("async_web3_service")


class TransactionFailedError(Exception):
    """Custom exception for failed on-chain transactions."""


class TransactionTimeoutError(Exception):
    """Raised when a transaction does not get mined in time."""


class AsyncWeb3Service:
    """Handle async Ethereum interactions with secure key management."""

    def __init__(self, web3: AsyncWeb3, account: Account) -> None:
        self.web3 = web3
        self.account = account
        self.web3.eth.default_account = account.address

    @classmethod
    async def create(cls, rpc_url: str, encrypted_private_key: str) -> "AsyncWeb3Service":
        web3 = AsyncWeb3(AsyncHTTPProvider(rpc_url))
        web3.middleware_onion.inject(proof_of_authority.ExtraDataToPOAMiddleware, layer=0)
        if not await web3.is_connected():
            raise ConnectionError("Failed to connect to Ethereum node.")
        key_manager = SecureKeyManager()
        key = key_manager.decrypt_private_key(encrypted_private_key)
        try:
            account = Account.from_key(key)
        finally:
            secure_zero_memory(bytearray(key, "utf-8"))
        middleware = SignAndSendRawMiddlewareBuilder.build(account, web3)
        web3.middleware_onion.add(middleware.async_wrap_make_request, name="sign_send")
        return cls(web3, account)

    async def get_contract(self, address: str, abi: List[Dict[str, Any]]):
        checksum = self.web3.to_checksum_address(address)
        return self.web3.eth.contract(address=checksum, abi=abi)

    async def sign_and_send_transaction(
        self, transaction: TxParams, timeout: int = 120, retries: int = 3
    ) -> TxReceipt:
        if "from" not in transaction:
            transaction["from"] = self.account.address
        if "nonce" not in transaction:
            transaction["nonce"] = await self.web3.eth.get_transaction_count(self.account.address)
        fee = await self.web3.eth.fee_history(1, "latest")
        base_fee = fee["baseFeePerGas"][0]
        priority = await self.web3.eth.max_priority_fee
        transaction.setdefault("maxPriorityFeePerGas", priority)
        transaction.setdefault("maxFeePerGas", base_fee + priority * 2)
        for attempt in range(retries):
            tx_hash = await self.web3.eth.send_transaction(transaction)
            try:
                receipt = await self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
            except TimeExhausted as exc:
                if attempt == retries - 1:
                    logger.error("Transaction %s timed out", tx_hash.hex())
                    raise TransactionTimeoutError(str(exc))
                delay = min(0.1 * 2**attempt, 30) + random.uniform(0, 0.05)
                await asyncio.sleep(delay)
                transaction["nonce"] = await self.web3.eth.get_transaction_count(self.account.address)
                continue
            if receipt["status"] == 0:
                logger.error("Transaction %s failed", tx_hash.hex())
                raise TransactionFailedError(f"Transaction {tx_hash.hex()} failed")
            return receipt
        raise TransactionTimeoutError("Max retries exceeded")
