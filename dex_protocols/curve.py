from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from web3.contract import Contract

from dex_protocols.base import BaseDEXProtocol
from exceptions import DexError
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

    async def _execute_swap(self, amount_in: int, route: List[str]) -> str:
        try:
            i, j = self._idx(route[0]), self._idx(route[-1])
            tx = self.pool.functions.exchange(i, j, amount_in, 0).build_transaction(
                {
                    "from": self.web3_service.account.address,
                    "gas": self.gas_limit,
                    "gasPrice": self.web3_service.web3.eth.gas_price,
                }
            )
            receipt = await self.web3_service.sign_and_send_transaction(tx)
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


__all__ = ["Curve"]
