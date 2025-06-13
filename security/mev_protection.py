"""MEV protection utilities with transaction simulation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import httpx
from web3 import Web3
from web3.types import TxParams

import config
from exceptions import PriceManipulationError
from logger import get_logger
from utils.retry import retry_async

logger = get_logger("mev_protection")


@dataclass
class MEVProtectionConfig:
    """Settings for MEV protection."""

    enabled: bool = True
    flashbots_url: Optional[str] = None
    fork_rpc_url: Optional[str] = None
    deviation_threshold: float = 0.05


async def _simulate_price(tx: TxParams, rpc_url: str) -> float:
    web3 = Web3(Web3.HTTPProvider(rpc_url))

    def call() -> bytes:
        return web3.eth.call(tx)

    result = await asyncio.to_thread(call)
    return float(int.from_bytes(result, "big"))


def _check_deviation(expected: float, actual: float, threshold: float) -> None:
    if expected <= 0:
        raise ValueError("expected price must be positive")
    deviation = abs(actual - expected) / expected
    if deviation > threshold:
        raise PriceManipulationError(
            f"Price deviation {deviation:.2%} exceeds threshold"
        )


async def _submit_flashbots(tx: TxParams, endpoint: str) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        response = await retry_async(client.post, endpoint, json={"tx": tx})
    response.raise_for_status()
    return response.text


async def protect_transaction(tx: TxParams, expected_price: float) -> Optional[str]:
    cfg = MEVProtectionConfig(
        enabled=config.MEV_PROTECTION_ENABLED,
        flashbots_url=config.FLASHBOTS_URL,
        fork_rpc_url=config.FORK_RPC_URL,
        deviation_threshold=config.DEVIATION_THRESHOLD,
    )
    if not cfg.enabled:
        return None
    if cfg.fork_rpc_url:
        try:
            price = await retry_async(_simulate_price, tx, cfg.fork_rpc_url)
            _check_deviation(expected_price, price, cfg.deviation_threshold)
        except PriceManipulationError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.error("Simulation failed: %s", exc)
            return None
    if cfg.flashbots_url:
        try:
            return await _submit_flashbots(tx, cfg.flashbots_url)
        except Exception as exc:  # noqa: BLE001
            logger.error("Flashbots submission failed: %s", exc)
    return None


__all__ = ["protect_transaction", "MEVProtectionConfig"]
