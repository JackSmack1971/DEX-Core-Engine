"""Batch multiple swap operations into a single multicall."""

from __future__ import annotations

from typing import Any, Dict, List

from web3.contract import Contract
from web3.exceptions import ContractLogicError

import config
from exceptions import BatcherError, DexError, ServiceUnavailableError
from logger import get_logger
from utils.circuit_breaker import CircuitBreaker
from utils.retry import retry_async
from web3_service import (
    TransactionFailedError,
    TransactionTimeoutError,
    Web3Service,
)

MULTICALL_ABI: List[Dict[str, Any]] = [
    {
        "inputs": [
            {"internalType": "bytes[]", "name": "data", "type": "bytes[]"}
        ],
        "name": "multicall",
        "outputs": [
            {"internalType": "bytes[]", "name": "results", "type": "bytes[]"}
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]

logger = get_logger("batcher")


class Batcher:
    """Assemble and execute batched swaps atomically."""

    def __init__(self, web3_service: Web3Service, address: str) -> None:
        self.web3_service = web3_service
        self.contract: Contract = web3_service.get_contract(
            address, MULTICALL_ABI
        )
        self.base_gas_limit = config.GAS_LIMIT
        self._circuit = CircuitBreaker()

    async def execute(self, calls: List[bytes], reorder: bool = False) -> str:
        """Execute all calls in a single transaction."""
        if not calls:
            raise DexError("no calls provided")
        data = sorted(calls, key=len) if reorder else calls
        gas_limit = max(self.base_gas_limit, self.base_gas_limit * len(data))
        tx = self.contract.functions.multicall(data).build_transaction(
            {
                "from": self.web3_service.account.address,
                "gas": gas_limit,
                "gasPrice": self.web3_service.web3.eth.gas_price,
            }
        )
        try:
            receipt = await self._circuit.call(
                retry_async, self.web3_service.sign_and_send_transaction, tx
            )
            return receipt["transactionHash"].hex()
        except ServiceUnavailableError as exc:
            logger.error("Batch circuit open: %s", exc)
            raise BatcherError("service unavailable") from exc
        except (
            TransactionFailedError,
            TransactionTimeoutError,
            ContractLogicError,
        ) as exc:
            logger.error("Batch execution failed: %s", exc)
            raise BatcherError(str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.error("Batch execution error: %s", exc)
            raise BatcherError(str(exc)) from exc
