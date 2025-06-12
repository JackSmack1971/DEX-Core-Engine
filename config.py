# config.py
# /usr/bin/env python3

"""
Configuration loader for the Ethereum Trading Bot.

Manages loading and validation of essential configuration parameters
from environment variables.
"""

import os
from typing import Final, List

from web3 import Web3

from exceptions import ConfigurationError

from dotenv import load_dotenv

# --- Load environment variables from .env file ---
load_dotenv()


def _load_address(var_name: str) -> str:
    """Load and validate an Ethereum address from the environment."""
    address = os.getenv(var_name, "").strip()
    if not address:
        raise ConfigurationError(f"{var_name} environment variable not set.")
    if not Web3.isAddress(address):
        raise ConfigurationError(f"{var_name} is not a valid Ethereum address.")
    return Web3.toChecksumAddress(address)


def _load_float(var_name: str, default: float, *, minimum: float, maximum: float) -> float:
    """Load a float from the environment with range validation."""
    value_str = os.getenv(var_name, str(default))
    try:
        value = float(value_str)
    except ValueError as exc:
        raise ConfigurationError(f"{var_name} must be a number.") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(
            f"{var_name} must be between {minimum} and {maximum}."
        )
    return value


def _load_int(var_name: str, default: int, *, minimum: int, maximum: int) -> int:
    """Load an int from the environment with range validation."""
    value_str = os.getenv(var_name, str(default))
    try:
        value = int(value_str)
    except ValueError as exc:
        raise ConfigurationError(f"{var_name} must be an integer.") from exc
    if not minimum <= value <= maximum:
        raise ConfigurationError(
            f"{var_name} must be between {minimum} and {maximum}."
        )
    return value


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
WALLET_ADDRESS: Final[str] = _load_address("WALLET_ADDRESS")

# --- Trading Pair Configuration ---
# Addresses of the tokens to be traded.
# Values must be provided via environment variables.
TOKEN0_ADDRESS: Final[str] = _load_address("TOKEN0_ADDRESS")
TOKEN1_ADDRESS: Final[str] = _load_address("TOKEN1_ADDRESS")

# --- DEX Configuration ---
# Contract addresses for Uniswap V2 and Sushiswap Routers.
UNISWAP_V2_ROUTER: Final[str] = _load_address("UNISWAP_V2_ROUTER")
SUSHISWAP_ROUTER: Final[str] = _load_address("SUSHISWAP_ROUTER")

DEX_ROUTERS: Final[List[str]] = [UNISWAP_V2_ROUTER, SUSHISWAP_ROUTER]

# --- Bot Operational Parameters ---
# The minimum profit threshold in TOKEN1 (e.g., DAI) to execute a trade.
PROFIT_THRESHOLD: Final[float] = _load_float(
    "PROFIT_THRESHOLD", 1.0, minimum=0.0, maximum=1000.0
)

# Time in seconds to wait between polling for prices.
POLL_INTERVAL_SECONDS: Final[int] = _load_int(
    "POLL_INTERVAL_SECONDS", 10, minimum=1, maximum=3600
)

# Maximum acceptable slippage for trades, in percentage.
SLIPPAGE_TOLERANCE_PERCENT: Final[float] = _load_float(
    "SLIPPAGE_TOLERANCE_PERCENT", 0.5, minimum=0.0, maximum=100.0
)
