from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, Dict, List

from web3.contract import Contract

from logger import get_logger

logger = get_logger("token_detect")


class TokenInspectionError(Exception):
    """Raised when token inspection fails."""


class TokenType(Enum):
    ERC20 = "erc20"
    ERC777 = "erc777"
    FEE_ON_TRANSFER = "fee_on_transfer"
    REBASING = "rebasing"


ERC20_ABI: List[Dict[str, Any]] = [
    {
        "name": "balanceOf",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "balance", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

_GAS_MULTIPLIER = {
    TokenType.ERC20: 1.0,
    TokenType.ERC777: 1.1,
    TokenType.FEE_ON_TRANSFER: 1.2,
    TokenType.REBASING: 1.3,
}


def gas_multiplier(token_type: TokenType) -> float:
    """Return gas multiplier for ``token_type``."""
    return _GAS_MULTIPLIER.get(token_type, 1.0)


def _has_function(contract: Contract, name: str) -> bool:
    try:
        contract.get_function_by_name(name)
        return True
    except ValueError:
        return False


async def detect_token_type(contract: Contract) -> TokenType:
    """Inspect ``contract`` and return its token type."""
    if contract is None:
        raise TokenInspectionError("contract required")
    try:
        if _has_function(contract, "granularity"):
            return TokenType.ERC777
        if _has_function(contract, "rebase"):
            return TokenType.REBASING
        if _has_function(contract, "fee") or _has_function(contract, "fees"):
            return TokenType.FEE_ON_TRANSFER
    except Exception as exc:  # noqa: BLE001
        logger.error("Detection failed: %s", exc)
    return TokenType.ERC20


async def get_token_balance(contract: Contract, address: str) -> int:
    """Return token balance for ``address``."""
    if contract is None or not address:
        raise TokenInspectionError("invalid arguments")
    try:
        func = contract.functions.balanceOf(address).call
        result = await asyncio.to_thread(func)
        return int(result)
    except Exception as exc:  # noqa: BLE001
        raise TokenInspectionError(str(exc)) from exc


__all__ = [
    "TokenType",
    "detect_token_type",
    "get_token_balance",
    "ERC20_ABI",
    "gas_multiplier",
]
