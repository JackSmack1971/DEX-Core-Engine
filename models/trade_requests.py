from __future__ import annotations

from typing import Any, Dict, Tuple

from pydantic import BaseModel, Field, field_validator
from web3 import Web3

import config

SUPPORTED_TOKENS = {config.TOKEN0_ADDRESS, config.TOKEN1_ADDRESS}


class EnhancedTradeRequest(BaseModel):
    """Validated trade request payload."""

    token_pair: Tuple[str, str] = Field(..., description="Token addresses")
    amount: float = Field(..., gt=0, description="Trade amount")
    price: float = Field(..., gt=0, description="Expected price")
    metadata: Dict[str, Any] | None = None

    @field_validator("token_pair")
    @classmethod
    def _check_pair(cls, value: Tuple[str, str]) -> Tuple[str, str]:
        if len(value) != 2:
            raise ValueError("token_pair must contain two addresses")
        token_in, token_out = value
        for token in (token_in, token_out):
            if token not in SUPPORTED_TOKENS:
                raise ValueError("unsupported token")
            if not Web3.is_address(token):
                raise ValueError("invalid token address")
        if token_in == token_out:
            raise ValueError("tokens must differ")
        return Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)


__all__ = ["EnhancedTradeRequest", "SUPPORTED_TOKENS"]
