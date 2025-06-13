from __future__ import annotations

from typing import Iterable, List, Tuple

from dex_protocols.base import BaseDEXProtocol
from exceptions import DexError
from logger import get_logger

logger = get_logger("router")


class Router:
    """Aggregate multiple DEX protocol adapters."""

    def __init__(self, protocols: Iterable[BaseDEXProtocol]):
        self.protocols: List[BaseDEXProtocol] = list(protocols)

    def add_protocol(self, protocol: BaseDEXProtocol) -> None:
        """Register a new protocol adapter."""
        self.protocols.append(protocol)

    async def get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> Tuple[BaseDEXProtocol, List[str]]:
        """Return adapter and route with the highest quoted amount."""
        best: Tuple[BaseDEXProtocol, List[str], float] | None = None
        for proto in self.protocols:
            try:
                route = await proto.get_best_route(token_in, token_out, amount_in)
                if not route:
                    continue
                quote = await proto.get_quote(token_in, token_out, amount_in)
                if quote > 0 and (best is None or quote > best[2]):
                    best = (proto, route, quote)
            except DexError:
                continue
        if best is None:
            raise DexError("no liquidity available")
        return best[0], best[1]

    async def get_best_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> float:
        """Return the highest output amount for the swap."""
        proto, _ = await self.get_best_route(token_in, token_out, amount_in)
        return await proto.get_quote(token_in, token_out, amount_in)

    async def execute_swap(
        self, amount_in: int, token_in: str, token_out: str
    ) -> str:
        """Execute swap on the best protocol for the pair."""
        proto, route = await self.get_best_route(token_in, token_out, amount_in)
        logger.info(
            "Executing swap via %s: %s", proto.__class__.__name__, " -> ".join(route)
        )
        return await proto.execute_swap(amount_in, route)
