# /usr/bin/env python3
# strategy.py
"""
Implements the trading strategy for the bot.

This module contains the logic for identifying and acting upon
trading opportunities based on market conditions.
"""

import asyncio
from typing import List

from risk_manager import RiskManager

import config
from dex_handler import DEXHandler
from exceptions import StrategyError
from logger import get_logger, set_correlation_id

logger = get_logger("strategy")


class ArbitrageStrategy:
    """
    A simple arbitrage strategy between two DEXs.

    This strategy checks for price differences for a token pair
    between two DEXs and executes a trade if a profitable
    opportunity is identified.
    """

    def __init__(self, dex_handlers: List[DEXHandler], risk_manager: RiskManager | None = None):
        """
        Initializes the arbitrage strategy.

        Args:
            dex_handlers: A list of two configured DEXHandler instances.
        """
        if len(dex_handlers) != 2:
            raise StrategyError("ArbitrageStrategy requires exactly two DEXs.")
        self.dex1 = dex_handlers[0]
        self.dex2 = dex_handlers[1]
        self.token0 = config.TOKEN0_ADDRESS  # e.g., WETH
        self.token1 = config.TOKEN1_ADDRESS  # e.g., DAI
        self.risk = risk_manager or RiskManager()

    def _check_profitability(self, price1: float, price2: float) -> None:
        """
        Analyzes prices and executes a trade if profitable.

        Args:
            price1: Price of TOKEN1 on DEX1, in terms of TOKEN0.
            price2: Price of TOKEN1 on DEX2, in terms of TOKEN0.
        """
        # A simple model: buy on the cheaper DEX, assume we can sell on the other
        # A real implementation needs to calculate the full cycle profitability
        profit_margin = abs(price1 - price2)

        # A very basic gas cost estimation (in DAI)
        # In practice, this should query live gas prices and estimate tx cost
        estimated_gas_cost_in_dai = 50.0

        logger.info(
            "Price DEX1: %.2f DAI | Price DEX2: %.2f DAI | Margin: %.2f DAI",
            price1,
            price2,
            profit_margin,
        )

        if profit_margin > (estimated_gas_cost_in_dai + config.PROFIT_THRESHOLD):
            logger.info("Profitable opportunity found! Margin: $%.2f", profit_margin)
            size = self.risk.position_size(1.0, profit_margin / price1)
            logger.info("Risk-approved size: %.4f", size)
            # e.g., await self.dex1.execute_swap(...)
            logger.warning("--- EXECUTION LOGIC DISABLED IN THIS EXAMPLE ---")
        else:
            logger.info("No profitable opportunity found. Standing by.")

    async def run(self) -> None:
        """
        Starts the main trading loop for the strategy.
        """
        logger.info("--- Starting Arbitrage Trading Bot ---")
        logger.info("Monitoring %s / %s pair.", self.token0, self.token1)
        logger.info("DEX 1 Router: %s", self.dex1.router_address)
        logger.info("DEX 2 Router: %s", self.dex2.router_address)
        logger.info("-" * 40)

        while True:
            try:
                set_correlation_id()
                # Get price of 1 WETH in DAI on both exchanges
                price_dex1 = await self.dex1.get_price(self.token0, self.token1)
                price_dex2 = await self.dex2.get_price(self.token0, self.token1)

                if price_dex1 > 0 and price_dex2 > 0:
                    self._check_profitability(price_dex1, price_dex2)
                else:
                    logger.warning("Could not retrieve prices from one or both DEXs.")

            except Exception as e:
                logger.error("An error occurred: %s", e)

            logger.info("Waiting for %s seconds...", config.POLL_INTERVAL_SECONDS)
            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
