# /usr/bin/env python3
# main.py
"""
Main entry point for the Ethereum Trading Bot.

This script initializes all necessary components and starts the
selected trading strategy.
"""

from typing import List

import config
from web3_service import Web3Service
from dex_handler import DEXHandler
from strategy import ArbitrageStrategy


def main() -> None:
    """
    Sets up and runs the trading bot.
    """
    print("Initializing Ethereum Trading Bot...")

    try:
        # 1. Initialize Web3 Service
        web3_service = Web3Service(config.RPC_URL, config.PRIVATE_KEY)
        print(f"Connected to Ethereum node. Wallet: {config.WALLET_ADDRESS}")

        # 2. Initialize DEX Handlers for Uniswap and Sushiswap
        dex_handlers: List[DEXHandler] = [
            DEXHandler(web3_service, config.UNISWAP_V2_ROUTER),
            DEXHandler(web3_service, config.SUSHISWAP_ROUTER)
        ]
        print("DEX handlers initialized.")

        # 3. Initialize and run the trading strategy
        strategy = ArbitrageStrategy(dex_handlers)
        strategy.run()

    except (ValueError, ConnectionError) as e:
        print(f"Initialization failed: {e}")
    except KeyboardInterrupt:
        print("\nBot shutting down gracefully.")
    except Exception as e:
        print(f"An unexpected critical error occurred: {e}")


if __name__ == "__main__":
    main()
