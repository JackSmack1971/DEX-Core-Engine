# /usr/bin/env python3
# main.py
"""
Main entry point for the Ethereum Trading Bot.

This script initializes all necessary components and starts the
selected trading strategy.
"""

from typing import List
import asyncio

import config
from web3_service import Web3Service
from dex_handler import DEXHandler
from strategy import ArbitrageStrategy
from exceptions import ConfigurationError, DexError, StrategyError
from logger import logger, set_correlation_id


def main() -> None:
    """
    Sets up and runs the trading bot.
    """
    set_correlation_id()
    logger.info("Initializing Ethereum Trading Bot...")

    try:
        # 1. Initialize Web3 Service
        web3_service = Web3Service(config.RPC_URL, config.PRIVATE_KEY)
        logger.info("Connected to Ethereum node. Wallet: %s", config.WALLET_ADDRESS)

        # 2. Initialize DEX Handlers for Uniswap and Sushiswap
        dex_handlers: List[DEXHandler] = [
            DEXHandler(web3_service, config.UNISWAP_V2_ROUTER),
            DEXHandler(web3_service, config.SUSHISWAP_ROUTER)
        ]
        logger.info("DEX handlers initialized.")

        # 3. Initialize and run the trading strategy
        strategy = ArbitrageStrategy(dex_handlers)
        asyncio.run(strategy.run())

    except (ConfigurationError, DexError, StrategyError, ConnectionError) as e:
        logger.error("Initialization failed: %s", e)
    except KeyboardInterrupt:
        logger.info("\nBot shutting down gracefully.")
    except Exception as e:
        logger.exception("An unexpected critical error occurred: %s", e)


if __name__ == "__main__":
    main()
