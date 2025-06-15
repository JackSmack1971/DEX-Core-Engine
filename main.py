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
from logger import get_logger, set_correlation_id

logger = get_logger("main")


def setup_web3_service() -> Web3Service:
    """Initialize the Web3 service."""
    service = Web3Service(config.RPC_URL, config.ENCRYPTED_PRIVATE_KEY)
    logger.info("Connected to Ethereum node. Wallet: %s", config.WALLET_ADDRESS)
    return service


def setup_dex_handlers(web3_service: Web3Service) -> List[DEXHandler]:
    """Create DEX handlers for configured routers."""
    handlers = [
        DEXHandler(web3_service, config.UNISWAP_V2_ROUTER),
        DEXHandler(web3_service, config.SUSHISWAP_ROUTER),
    ]
    logger.info("DEX handlers initialized.")
    return handlers


async def launch_strategy(dex_handlers: List[DEXHandler]) -> None:
    """Run the arbitrage strategy."""
    strategy = ArbitrageStrategy(dex_handlers)
    await strategy.run()


def main() -> None:
    """
    Sets up and runs the trading bot.
    """
    set_correlation_id()
    logger.info("Initializing Ethereum Trading Bot...")

    try:
        web3_service = setup_web3_service()
        dex_handlers = setup_dex_handlers(web3_service)
        asyncio.run(launch_strategy(dex_handlers))

    except (ConfigurationError, DexError, StrategyError, ConnectionError) as e:
        logger.error("Initialization failed: %s", e)
    except KeyboardInterrupt:
        logger.info("\nBot shutting down gracefully.")
    except Exception as e:
        logger.exception("An unexpected critical error occurred: %s", e)


if __name__ == "__main__":
    main()
