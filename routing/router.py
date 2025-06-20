from __future__ import annotations

import heapq
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import os

from dex_protocols.base import BaseDEXProtocol
from exceptions import DexError, PriceManipulationError
from models.trade_requests import EnhancedTradeRequest
import config
from slippage_protection import (
    SlippageParams,
    SlippageProtectionEngine,
    calculate_dynamic_slippage,
    MIN_TOLERANCE_PERCENT,
)
from logger import get_logger
from observability.metrics import SLIPPAGE_APPLIED, SLIPPAGE_VIOLATIONS


@dataclass
class _Edge:
    """Graph edge representing a swap option."""

    token_out: str
    protocol: BaseDEXProtocol
    cost: float


logger = get_logger("router")


class Router:
    """Aggregate multiple DEX protocol adapters with multi-hop logic."""

    def __init__(self, protocols: Iterable[BaseDEXProtocol], ttl: int = 30) -> None:
        self.protocols: List[BaseDEXProtocol] = list(protocols)
        self._graph: Dict[str, List[_Edge]] = {}
        self._cache: Dict[
            Tuple[str, str, int],
            Tuple[List[BaseDEXProtocol], List[str], float],
        ] = {}
        self._ttl = ttl
        self.slippage_engine = None
        if config.DYNAMIC_SLIPPAGE_ENABLED:
            api = os.getenv("MARKET_DATA_URL")
            params = SlippageParams(config.SLIPPAGE_TOLERANCE_PERCENT, api)
            self.slippage_engine = SlippageProtectionEngine(params)
        self._build_graph()

    def add_protocol(self, protocol: BaseDEXProtocol) -> None:
        """Register a new protocol adapter."""
        self.protocols.append(protocol)

    def _current_block(self) -> int:
        try:
            return self.protocols[0].web3_service.web3.eth.block_number
        except Exception:  # noqa: BLE001
            return 0

    def _shortest_path(
        self, token_in: str, token_out: str
    ) -> Tuple[List[BaseDEXProtocol], List[str]]:
        dist: Dict[str, float] = {token_in: 0.0}
        prev: Dict[str, Tuple[str, BaseDEXProtocol]] = {}
        queue: List[Tuple[float, str]] = [(0.0, token_in)]
        while queue:
            cost, token = heapq.heappop(queue)
            if token == token_out:
                break
            for edge in self._graph.get(token, []):
                new_cost = cost + edge.cost
                if new_cost < dist.get(edge.token_out, float("inf")):
                    dist[edge.token_out] = new_cost
                    prev[edge.token_out] = (token, edge.protocol)
                    heapq.heappush(queue, (new_cost, edge.token_out))
        if token_out not in prev:
            raise DexError("no route")
        tokens: List[str] = [token_out]
        protocols: List[BaseDEXProtocol] = []
        curr = token_out
        while curr != token_in:
            prev_token, proto = prev[curr]
            tokens.append(prev_token)
            protocols.append(proto)
            curr = prev_token
        tokens.reverse()
        protocols.reverse()
        return protocols, tokens

    def _build_graph(self) -> None:
        """Construct the token graph from protocol pool data."""
        for proto in self.protocols:
            pools = getattr(proto, "pools", [])
            try:
                gas_price = proto.web3_service.web3.eth.gas_price
            except Exception:  # noqa: BLE001
                gas_price = 0.0
            gas_cost = gas_price * getattr(proto, "gas_limit", 0)
            for token_a, token_b, fee in pools:
                cost = float(fee) + float(gas_cost)
                self._graph.setdefault(token_a, []).append(_Edge(token_b, proto, cost))
                self._graph.setdefault(token_b, []).append(_Edge(token_a, proto, cost))

    async def get_best_route(
        self, token_in: str, token_out: str, amount_in: int
    ) -> Tuple[List[BaseDEXProtocol], List[str]]:
        """Return protocols and route with the lowest total cost."""
        if amount_in <= 0 or not token_in or not token_out:
            raise DexError("invalid parameters")
        block = self._current_block()
        key = (token_in, token_out, block)
        cached = self._cache.get(key)
        if cached and cached[2] > time.time():
            return cached[0], cached[1]
        protocols, route = self._shortest_path(token_in, token_out)
        self._cache[key] = (protocols, route, time.time() + self._ttl)
        return protocols, route

    async def get_best_quote(
        self, token_in: str, token_out: str, amount_in: int
    ) -> float:
        """Return the estimated output amount for the optimal path."""
        protocols, route = await self.get_best_route(token_in, token_out, amount_in)
        amt = float(amount_in)
        for idx, proto in enumerate(protocols):
            amt = await proto.get_quote(route[idx], route[idx + 1], int(amt))
        return amt

    def find_triangular_cycles(
        self,
    ) -> List[Tuple[List[BaseDEXProtocol], List[str], float]]:
        """Return all token cycles ``A->B->C->A`` with costs."""
        cycles: List[Tuple[List[BaseDEXProtocol], List[str], float]] = []
        seen: set[Tuple[str, str, str]] = set()
        for token_a, edges_ab in self._graph.items():
            for edge_ab in edges_ab:
                token_b = edge_ab.token_out
                if token_b == token_a:
                    continue
                for edge_bc in self._graph.get(token_b, []):
                    token_c = edge_bc.token_out
                    if token_c in {token_a, token_b}:
                        continue
                    for edge_ca in self._graph.get(token_c, []):
                        if edge_ca.token_out != token_a:
                            continue
                        key = tuple(sorted([token_a, token_b, token_c]))
                        if key in seen:
                            continue
                        seen.add(key)
                        cycles.append(
                            (
                                [edge_ab.protocol, edge_bc.protocol, edge_ca.protocol],
                                [token_a, token_b, token_c, token_a],
                                edge_ab.cost + edge_bc.cost + edge_ca.cost,
                            )
                        )
        return cycles

    async def _dynamic_slippage(
        self, proto: BaseDEXProtocol, hop: List[str], amount: int
    ) -> float:
        try:
            info = await proto.get_liquidity_info(hop[0], hop[1], amount)
            if self.slippage_engine:
                market = await self.slippage_engine.get_market_conditions()
                self.slippage_engine.analyze_market_conditions(market)
                return calculate_dynamic_slippage(info.price_impact, market.volatility)
            return info.price_impact
        except Exception as exc:  # noqa: BLE001
            logger.warning("Slippage data unavailable: %s", exc)
            return 0.0

    async def execute_swap(self, amount_in: int, token_in: str, token_out: str) -> str:
        """Execute sequential swaps along the optimal path."""
        protocols, route = await self.get_best_route(token_in, token_out, amount_in)
        amt = amount_in
        tx = ""
        for idx, proto in enumerate(protocols):
            hop = [route[idx], route[idx + 1]]
            remaining = amt
            total_out = 0
            while remaining > 0:
                part = remaining
                slip = 0.0
                for _ in range(4):
                    slip = await self._dynamic_slippage(proto, hop, part)
                    tolerance = (
                        self.slippage_engine.params.tolerance_percent
                        if self.slippage_engine
                        else config.SLIPPAGE_TOLERANCE_PERCENT
                    )
                    if slip <= tolerance or part <= 1:
                        break
                    part //= 2
                if slip < MIN_TOLERANCE_PERCENT:
                    raise DexError("slippage below minimum")
                hop_str = " -> ".join(hop)
                logger.info(
                    "Executing hop via %s: %s",
                    proto.__class__.__name__,
                    hop_str,
                )
                expected_out = await proto.get_quote(hop[0], hop[1], part)
                amount_out_min = SlippageProtectionEngine.calculate_protected_slippage(
                    int(expected_out)
                )
                slip_pct = (
                    (int(expected_out) - amount_out_min) * 100 / int(expected_out)
                    if expected_out
                    else 0.0
                )
                SLIPPAGE_APPLIED.observe(slip_pct)
                try:
                    SlippageProtectionEngine.validate_transaction_slippage(
                        int(expected_out), amount_out_min
                    )
                except PriceManipulationError as exc:
                    SLIPPAGE_VIOLATIONS.inc()
                    raise DexError(str(exc)) from exc
                tx = await proto.execute_swap(part, hop, amount_out_min)
                total_out += expected_out
                remaining -= part
            amt = int(total_out)
        return tx

    async def execute_trade(self, req: "EnhancedTradeRequest") -> str:
        """Execute a trade from a validated request."""
        token_in, token_out = req.token_pair
        return await self.execute_swap(int(req.amount), token_in, token_out)
