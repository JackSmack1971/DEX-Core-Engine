# /usr/bin/env python3
# strategy.py
"""
Implements the trading strategy for the bot.

This module contains the logic for identifying and acting upon
trading opportunities based on market conditions.
"""

import asyncio

from risk_manager import RiskManager

import config
from routing import Router
from logger import get_logger, set_correlation_id

logger = get_logger("strategy")


class ArbitrageStrategy:
    """
    A simple arbitrage strategy between two DEXs.

    This strategy checks for price differences for a token pair
    between two DEXs and executes a trade if a profitable
    opportunity is identified.
    """

    def __init__(
        self, router: Router, risk_manager: RiskManager | None = None
    ) -> None:
        """Initialize the arbitrage strategy."""
        self.router = router
        self.token0 = config.TOKEN0_ADDRESS  # e.g., WETH
        self.token1 = config.TOKEN1_ADDRESS  # e.g., DAI
        self.risk = risk_manager or RiskManager()

    def _check_profitability(
        self, start_amount: float, end_amount: float
    ) -> None:
        """Analyze quotes and log if a trade is profitable."""
        profit_margin = end_amount - start_amount
        logger.info(
            "Cycle start %.6f end %.6f profit %.6f",
            start_amount,
            end_amount,
            profit_margin,
        )
        if profit_margin > config.PROFIT_THRESHOLD:
            logger.info(
                "Profitable opportunity found! Margin: %.6f", profit_margin
            )
            size = self.risk.position_size(start_amount, profit_margin)
            logger.info("Risk-approved size: %.4f", size)
            logger.warning("--- EXECUTION LOGIC DISABLED IN THIS EXAMPLE ---")
        else:
            logger.info("No profitable opportunity found. Standing by.")

    async def run(self) -> None:
        """
        Starts the main trading loop for the strategy.
        """
        logger.info("--- Starting Arbitrage Trading Bot ---")
        logger.info("Monitoring %s / %s pair.", self.token0, self.token1)
        logger.info(
            "Router initialized with %d protocols",
            len(self.router.protocols),
        )
        logger.info("-" * 40)

        while True:
            try:
                set_correlation_id()
                start_amount = 1.0
                token1_amt = await self.router.get_best_quote(
                    self.token0, self.token1, start_amount
                )
                end_amount = await self.router.get_best_quote(
                    self.token1, self.token0, token1_amt
                )
                self._check_profitability(start_amount, end_amount)

            except Exception as e:
                logger.error("An error occurred: %s", e)

            logger.info(
                "Waiting for %s seconds...",
                config.POLL_INTERVAL_SECONDS,
            )
            await asyncio.sleep(config.POLL_INTERVAL_SECONDS)
