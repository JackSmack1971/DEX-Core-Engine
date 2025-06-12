# /usr/bin/env python3
# strategy.py
"""
Implements the trading strategy for the bot.

This module contains the logic for identifying and acting upon
trading opportunities based on market conditions.
"""

import time
from typing import List

import config
from dex_handler import DEXHandler


class ArbitrageStrategy:
    """
    A simple arbitrage strategy between two DEXs.

    This strategy checks for price differences for a token pair
    between two DEXs and executes a trade if a profitable
    opportunity is identified.
    """

    def __init__(self, dex_handlers: List[DEXHandler]):
        """
        Initializes the arbitrage strategy.

        Args:
            dex_handlers: A list of two configured DEXHandler instances.
        """
        if len(dex_handlers) != 2:
            raise ValueError("ArbitrageStrategy requires exactly two DEXs.")
        self.dex1 = dex_handlers[0]
        self.dex2 = dex_handlers[1]
        self.token0 = config.TOKEN0_ADDRESS  # e.g., WETH
        self.token1 = config.TOKEN1_ADDRESS  # e.g., DAI

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

        print(
            f"Price DEX1: {price1:.2f} DAI | "
            f"Price DEX2: {price2:.2f} DAI | "
            f"Margin: {profit_margin:.2f} DAI"
        )

        if profit_margin > (estimated_gas_cost_in_dai + config.PROFIT_THRESHOLD):
            print(f"Profitable opportunity found! Margin: ${profit_margin:.2f}")
            # In a real bot, the swap execution logic would be called here.
            # e.g., self.dex1.execute_swap(...)
            print("--- EXECUTION LOGIC DISABLED IN THIS EXAMPLE ---")
        else:
            print("No profitable opportunity found. Standing by.")

    def run(self) -> None:
        """
        Starts the main trading loop for the strategy.
        """
        print("--- Starting Arbitrage Trading Bot ---")
        print(f"Monitoring {self.token0} / {self.token1} pair.")
        print(f"DEX 1 Router: {self.dex1.router_address}")
        print(f"DEX 2 Router: {self.dex2.router_address}")
        print("-" * 40)

        while True:
            try:
                # Get price of 1 WETH in DAI on both exchanges
                price_dex1 = self.dex1.get_price(self.token0, self.token1)
                price_dex2 = self.dex2.get_price(self.token0, self.token1)

                if price_dex1 > 0 and price_dex2 > 0:
                    self._check_profitability(price_dex1, price_dex2)
                else:
                    print("Could not retrieve prices from one or both DEXs.")

            except Exception as e:
                print(f"An error occurred: {e}")

            print(f"Waiting for {config.POLL_INTERVAL_SECONDS} seconds...")
            time.sleep(config.POLL_INTERVAL_SECONDS)
