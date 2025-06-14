from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from web3.contract import Contract

from dex_protocols.base import BaseDEXProtocol, LiquidityInfo
from exceptions import DexError
from observability.metrics import SLIPPAGE_APPLIED, SLIPPAGE_VIOLATIONS
from tokens.detect import (
    ERC20_ABI,
    TokenInspectionError,
    TokenType,
    detect_token_type,
    gas_multiplier,
    get_token_balance,
)
from web3_service import Web3Service


CURVE_POOL_ABI: List[Dict[str, Any]] = [
    {
        "inputs": [
            {"name": "i", "type": "int128"},
            {"name": "j", "type": "int128"},
            {"name": "dx", "type": "uint256"},
        ],
        "name": "get_dy",
        "outputs": [{"name": "dy", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "i", "type": "int128"},
            {"name": "j", "type": "int128"},
            {"name": "dx", "type": "uint256"},
            {"name": "min_dy", "type": "uint256"},
        ],
        "name": "exchange",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class Curve(BaseDEXProtocol):
    """Adapter for Curve pools."""

    def __init__(
        self,
        web3_service: Web3Service,
        pool_address: str,
        token_index: Dict[str, int],
        gas_limit: int = 250000,
    ) -> None:
        super().__init__()
        self.web3_service = web3_service
        self.pool: Contract = web3_service.get_contract(pool_address, CURVE_POOL_ABI)
        self.token_index = {k.lower(): v for k, v in token_index.items()}
        self.gas_limit = gas_limit

    def _idx(self, token: str) -> int:
        try:
            return self.token_index[token.lower()]
        except KeyError as exc:  # noqa: BLE001
            raise DexError("unknown token") from exc

    async def _get_quote(self, token_in: str, token_out: str, amount_in: int) -> float:
        try:
            func = self.pool.functions.get_dy(
                self._idx(token_in), self._idx(token_out), amount_in
            ).call
            amount_out = await asyncio.to_thread(func)
            return float(amount_out)
        except DexError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Curve quote error: %s", exc)
            raise DexError("quote failed") from exc

    async def _execute_swap(
        self, amount_in: int, route: List[str], amount_out_min: int
    ) -> str:
        try:
            token_out = route[-1]
            contract = self.web3_service.get_contract(token_out, ERC20_ABI)
            try:
                token_type = await detect_token_type(contract)
            except TokenInspectionError:
                token_type = TokenType.ERC20
            multiplier = gas_multiplier(token_type)
            balance_before = await get_token_balance(
                contract, self.web3_service.account.address
            )

            i, j = self._idx(route[0]), self._idx(token_out)
            tx = self.pool.functions.exchange(i, j, amount_in, amount_out_min).build_transaction(
                {
                    "from": self.web3_service.account.address,
                    "gas": int(self.gas_limit * multiplier),
                    "gasPrice": self.web3_service.web3.eth.gas_price,
                }
            )
            receipt = await self.web3_service.sign_and_send_transaction(tx)
            balance_after = await get_token_balance(
                contract, self.web3_service.account.address
            )
            actual_out = balance_after - balance_before
            if actual_out < amount_out_min:
                SLIPPAGE_VIOLATIONS.inc()
            slip_pct = (
                (amount_out_min - actual_out) * 100 / amount_out_min
                if actual_out < amount_out_min and amount_out_min
                else 0.0
            )
            SLIPPAGE_APPLIED.observe(max(slip_pct, 0.0))
            if actual_out <= 0:
                raise DexError("token balance check failed")
            return receipt["transactionHash"].hex()
        except DexError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Curve swap error: %s", exc)
            raise DexError("swap failed") from exc

    async def _get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> List[str]:
        self._idx(token_in)
        self._idx(token_out)
        return [token_in, token_out]

    async def get_liquidity_info(
        self, token_in: str, token_out: str, amount_in: int
    ) -> LiquidityInfo:
        small = await self._get_quote(token_in, token_out, 1)
        large = await self._get_quote(token_in, token_out, amount_in)
        expected = small * amount_in
        impact = 0.0 if expected == 0 else abs(expected - large) / expected * 100
        return LiquidityInfo(liquidity=float(amount_in) * 10, price_impact=impact)


__all__ = ["Curve"]
