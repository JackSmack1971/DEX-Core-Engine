"""Registry for managing available strategies."""

from __future__ import annotations

from typing import Callable, Dict, List, Type

from strategies.base import BaseStrategy
from strategies.arbitrage import ArbitrageStrategy
from strategies.arbitrage_engine import ArbitrageEngine


class StrategyRegistry:
    """Registry for available strategy classes."""

    def __init__(self) -> None:
        self._strategies: Dict[str, Type[BaseStrategy]] = {}
        self._factories: Dict[str, Callable[..., BaseStrategy]] = {}
        self.register("arbitrage", ArbitrageStrategy)
        self.register("arbitrage_engine", ArbitrageEngine)

    def register(
        self,
        name: str,
        strategy_class: Type[BaseStrategy],
        factory: Callable[..., BaseStrategy] | None = None,
    ) -> None:
        self._strategies[name] = strategy_class
        if factory:
            self._factories[name] = factory

    def create_strategy(self, name: str, **kwargs: object) -> BaseStrategy:
        if name not in self._strategies:
            raise KeyError(f"strategy {name} not registered")
        if factory := self._factories.get(name):
            return factory(**kwargs)
        return self._strategies[name](**kwargs)

    def list_strategies(self) -> List[str]:
        return list(self._strategies.keys())

__all__ = ["StrategyRegistry", "ArbitrageStrategy", "ArbitrageEngine"]
