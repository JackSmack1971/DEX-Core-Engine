from __future__ import annotations

import asyncio
import time
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


BALANCER_VAULT_ABI: List[Dict[str, Any]] = [
    {
        "inputs": [
            {"internalType": "uint8", "name": "kind", "type": "uint8"},
            {"internalType": "tuple[]", "name": "swaps", "type": "tuple[]"},
            {"internalType": "address[]", "name": "assets", "type": "address[]"},
        ],
        "name": "queryBatchSwap",
        "outputs": [
            {"internalType": "int256[]", "name": "assetDeltas", "type": "int256[]"}
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "tuple", "name": "singleSwap", "type": "tuple"},
            {"internalType": "tuple", "name": "funds", "type": "tuple"},
            {"internalType": "uint256", "name": "limit", "type": "uint256"},
            {"internalType": "uint256", "name": "deadline", "type": "uint256"},
        ],
        "name": "swap",
        "outputs": [
            {"internalType": "uint256", "name": "amountOut", "type": "uint256"}
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


class Balancer(BaseDEXProtocol):
    """Adapter for Balancer vault swaps."""

    def __init__(
        self,
        web3_service: Web3Service,
        vault_address: str,
        pool_id: str,
        gas_limit: int = 250000,
    ) -> None:
        super().__init__()
        self.web3_service = web3_service
        self.pool_id = pool_id
        self.gas_limit = gas_limit
        self.vault: Contract = web3_service.get_contract(
            vault_address, BALANCER_VAULT_ABI
        )

    async def _get_quote(self, token_in: str, token_out: str, amount_in: int) -> float:
        swaps = [
            {
                "poolId": self.pool_id,
                "assetInIndex": 0,
                "assetOutIndex": 1,
                "amount": amount_in,
                "userData": b"",
            }
        ]
        assets = [token_in, token_out]
        try:
            func = self.vault.functions.queryBatchSwap(0, swaps, assets).call
            deltas = await asyncio.to_thread(func)
            return float(-deltas[1])
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Balancer quote error: %s", exc)
            raise DexError("quote failed") from exc

    async def _execute_swap(
        self, amount_in: int, route: List[str], amount_out_min: int
    ) -> str:
        token_in, token_out = route[0], route[-1]
        single_swap = {
            "poolId": self.pool_id,
            "kind": 0,
            "assetIn": token_in,
            "assetOut": token_out,
            "amount": amount_in,
            "userData": b"",
        }
        funds = {
            "sender": self.web3_service.account.address,
            "recipient": self.web3_service.account.address,
            "fromInternalBalance": False,
            "toInternalBalance": False,
        }
        try:
            contract = self.web3_service.get_contract(token_out, ERC20_ABI)
            try:
                token_type = await detect_token_type(contract)
            except TokenInspectionError:
                token_type = TokenType.ERC20
            multiplier = gas_multiplier(token_type)
            balance_before = await get_token_balance(
                contract, self.web3_service.account.address
            )

            tx = self.vault.functions.swap(
                single_swap, funds, amount_out_min, int(time.time()) + 300
            ).build_transaction(
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
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Balancer swap error: %s", exc)
            raise DexError("swap failed") from exc

    async def _get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> List[str]:
        return [token_in, token_out]

    async def get_liquidity_info(
        self, token_in: str, token_out: str, amount_in: int
    ) -> LiquidityInfo:
        small = await self._get_quote(token_in, token_out, 1)
        large = await self._get_quote(token_in, token_out, amount_in)
        expected = small * amount_in
        impact = 0.0 if expected == 0 else abs(expected - large) / expected * 100
        return LiquidityInfo(liquidity=float(amount_in) * 10, price_impact=impact)


__all__ = ["Balancer"]
