# config.py
# /usr/bin/env python3

"""
Configuration loader for the Ethereum Trading Bot.

Manages loading and validation of essential configuration parameters
from environment variables.
"""

import os
from typing import List, Final

from exceptions import ConfigurationError

from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()

# --- Security & Connection Configuration ---
# A secure RPC URL from a provider like Infura or Alchemy is required.
# Example: "https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID"
RPC_URL: Final[str] = os.getenv("RPC_URL", "")
if not RPC_URL:
    raise ConfigurationError("RPC_URL environment variable not set.")

# The private key of the trading wallet.
# WARNING: Keep this key secure and never expose it.
PRIVATE_KEY: Final[str] = os.getenv("PRIVATE_KEY", "")
if not PRIVATE_KEY:
    raise ConfigurationError("PRIVATE_KEY environment variable not set.")

# The public address of the trading wallet.
WALLET_ADDRESS: Final[str] = os.getenv("WALLET_ADDRESS", "")
if not WALLET_ADDRESS:
    raise ConfigurationError("WALLET_ADDRESS environment variable not set.")

# --- Trading Pair Configuration ---
# Addresses of the tokens to be traded.
# Values must be provided via environment variables.
def _load_address(var_name: str) -> str:
    address = os.getenv(var_name, "").strip()
    if not address:
        raise ConfigurationError(f"{var_name} environment variable not set.")
    if not (address.startswith("0x") and len(address) == 42):
        raise ConfigurationError(f"{var_name} is not a valid address.")
    return address

TOKEN0_ADDRESS: Final[str] = _load_address("TOKEN0_ADDRESS")
TOKEN1_ADDRESS: Final[str] = _load_address("TOKEN1_ADDRESS")

# --- DEX Configuration ---
# Contract addresses for Uniswap V2 and Sushiswap Routers.
UNISWAP_V2_ROUTER: Final[str] = _load_address("UNISWAP_V2_ROUTER")
SUSHISWAP_ROUTER: Final[str] = _load_address("SUSHISWAP_ROUTER")

DEX_ROUTERS: Final[List[str]] = [UNISWAP_V2_ROUTER, SUSHISWAP_ROUTER]

# --- Bot Operational Parameters ---
# The minimum profit threshold in TOKEN1 (e.g., DAI) to execute a trade.
PROFIT_THRESHOLD: Final[float] = 1.0  # e.g., 1 DAI

# Time in seconds to wait between polling for prices.
POLL_INTERVAL_SECONDS: Final[int] = 10

# Maximum acceptable slippage for trades, in percentage.
SLIPPAGE_TOLERANCE_PERCENT: Final[float] = 0.5
