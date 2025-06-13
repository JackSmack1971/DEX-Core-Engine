from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass
class Asset:
    """Represent a portfolio asset."""

    symbol: str
    amount: float
    price: float

    @property
    def value(self) -> float:
        return self.amount * self.price


@dataclass
class Portfolio:
    """Collection of assets."""

    assets: Dict[str, Asset] = field(default_factory=dict)

    def total_value(self) -> float:
        return sum(asset.value for asset in self.assets.values())
