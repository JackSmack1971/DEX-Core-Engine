# config.py
# /usr/bin/env python3

"""
Configuration loader for the Ethereum Trading Bot.

Manages loading and validation of essential configuration parameters
from environment variables.
"""

import os
from typing import List, Final

from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

# --- Security & Connection Configuration ---
# A secure RPC URL from a provider like Infura or Alchemy is required.
# Example: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
RPC_URL: Final[str] = os.getenv("RPC_URL", "")
if not RPC_URL:
    raise ValueError("RPC_URL environment variable not set.")

# The private key of the trading wallet.
# WARNING: Keep this key secure and never expose it.
PRIVATE_KEY: Final[str] = os.getenv("PRIVATE_KEY", "")
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY environment variable not set.")

# The public address of the trading wallet.
WALLET_ADDRESS: Final[str] = os.getenv("WALLET_ADDRESS", "")
if not WALLET_ADDRESS:
    raise ValueError("WALLET_ADDRESS environment variable not set.")

# --- Trading Pair Configuration ---
# Addresses of the tokens to be traded.
# Example uses WETH and DAI.
TOKEN0_ADDRESS: Final[str] = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" # WETH
TOKEN1_ADDRESS: Final[str] = "0x6B175474E89094C44Da98b954EedeAC495271d0F" # DAI

# --- DEX Configuration ---
# Contract addresses for Uniswap V2 and Sushiswap Routers.
UNISWAP_V2_ROUTER: Final[str] = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
SUSHISWAP_ROUTER: Final[str] = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"

DEX_ROUTERS: Final[List[str]] = [UNISWAP_V2_ROUTER, SUSHISWAP_ROUTER]

# --- Bot Operational Parameters ---
# The minimum profit threshold in TOKEN1 (e.g., DAI) to execute a trade.
PROFIT_THRESHOLD: Final[float] = 1.0  # e.g., 1 DAI

# Time in seconds to wait between polling for prices.
POLL_INTERVAL_SECONDS: Final[int] = 10

# Maximum acceptable slippage for trades, in percentage.
SLIPPAGE_TOLERANCE_PERCENT: Final[float] = 0.5
