"""Advanced arbitrage engine handling multiple arbitrage types."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List

from cross_chain import BridgeProvider
from dex_protocols.base import BaseDEXProtocol

from routing import Router
from strategies.base import BaseStrategy, StrategyConfig
from logger import get_logger


class ArbitrageType(Enum):
    """Supported arbitrage opportunity types."""

    SIMPLE = "simple"
    TRIANGULAR = "triangular"
    FLASH_LOAN = "flash_loan"
    CROSS_CHAIN = "cross_chain"


@dataclass
class ArbitrageOpportunity:
    """Details about a detected opportunity."""

    opportunity_type: ArbitrageType
    path: List[str]
    profit: float


class OpportunityDetector:
    """Scan token pairs via ``Router`` for arbitrage opportunities."""

    def __init__(
        self,
        router: Router,
        tokens: Iterable[str],
        amount: float = 1.0,
        providers: Iterable[BridgeProvider] | None = None,
    ) -> None:
        self.router = router
        self.tokens = list(tokens)
        self.providers = list(providers or [])
        self.amount = amount
        self.logger = get_logger("opportunity_detector")

    async def _check_slippage(self, price: float, amount: float) -> bool:
        if not self.router.slippage_engine:
            return True
        try:
            await self.router.slippage_engine.check(price, amount)
            return True
        except Exception:  # noqa: BLE001
            return False

    async def _evaluate_cycle(
        self,
        protocols: List[BaseDEXProtocol],
        path: List[str],
        base_cost: float,
    ) -> ArbitrageOpportunity | None:
        amt = self.amount
        for idx, proto in enumerate(protocols):
            quote = await proto.get_quote(path[idx], path[idx + 1], int(amt))
            if not await self._check_slippage(quote, amt):
                return None
            amt = quote
        total_cost = base_cost
        for provider in self.providers:
            try:
                total_cost += await provider.get_price(path[-1], path[0])
            except Exception as exc:  # noqa: BLE001
                self.logger.error("bridge price error: %s", exc)
        profit = amt - self.amount - total_cost
        if profit > 0:
            return ArbitrageOpportunity(ArbitrageType.TRIANGULAR, path, profit)
        return None

    async def scan(self) -> List[ArbitrageOpportunity]:
        """Return a list of opportunities between all token pairs."""
        opportunities: List[ArbitrageOpportunity] = []
        for token_in in self.tokens:
            for token_out in self.tokens:
                if token_in == token_out:
                    continue
                try:
                    out1 = await self.router.get_best_quote(token_in, token_out, int(self.amount))
                    out2 = await self.router.get_best_quote(token_out, token_in, int(out1))
                    profit = out2 - self.amount
                    if profit > 0:
                        opportunities.append(
                            ArbitrageOpportunity(
                                ArbitrageType.SIMPLE,
                                [token_in, token_out, token_in],
                                profit,
                            )
                        )
                except Exception as exc:  # noqa: BLE001
                    self.logger.error("scan error: %s", exc)
        for protocols, path, cost in self.router.find_triangular_cycles():
            try:
                opp = await self._evaluate_cycle(protocols, path, cost)
                if opp:
                    opportunities.append(opp)
            except Exception as exc:  # noqa: BLE001
                self.logger.error("cycle eval error: %s", exc)
        return opportunities


class ArbitrageEngine(BaseStrategy):
    """Strategy engine that executes various arbitrage types."""

    def __init__(
        self,
        router: Router,
        strategy_config: StrategyConfig | None = None,
        risk_manager: Any | None = None,
        tokens: Iterable[str] | None = None,
    ) -> None:
        cfg = strategy_config or StrategyConfig(name="arbitrage_engine")
        super().__init__(router, cfg, risk_manager)
        self.tokens = list(tokens or [])
        self.detector = OpportunityDetector(router, self.tokens)

    async def analyze_market(self) -> Dict[str, Any]:
        opportunities = await self.detector.scan()
        return {"opportunities": opportunities}

    async def generate_signals(self, market_data: Dict[str, Any]) -> List[ArbitrageOpportunity]:
        return market_data.get("opportunities", [])

    async def execute_trades(self, signals: List[ArbitrageOpportunity]) -> List[str]:
        tx_hashes: List[str] = []
        for opp in signals:
            try:
                if opp.opportunity_type == ArbitrageType.SIMPLE:
                    tx = await self.router.execute_swap(int(self.detector.amount), opp.path[0], opp.path[1])
                else:
                    self.logger.warning("Engine type %s not implemented", opp.opportunity_type.value)
                    tx = "0x0"
                tx_hashes.append(tx)
            except Exception as exc:  # noqa: BLE001
                self.logger.error("trade failed: %s", exc)
        return tx_hashes

    async def run(self) -> None:  # pragma: no cover - thin wrapper
        await self.start()


__all__ = [
    "ArbitrageType",
    "ArbitrageOpportunity",
    "OpportunityDetector",
    "ArbitrageEngine",
]
