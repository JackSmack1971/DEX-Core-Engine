"""Application configuration management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError, validator
from web3 import Web3

from exceptions import ConfigurationError


class TradingSettings(BaseModel):
    """Trading related parameters."""

    max_position_size: float = Field(..., gt=0)
    risk_limit: float = Field(..., ge=0, le=1)
    max_daily_volume: float = Field(100.0, gt=0)


class RiskSettings(BaseModel):
    """Risk management parameters."""

    max_drawdown_percent: float = Field(20.0, ge=0, le=100)
    stop_loss_percent: float = Field(5.0, ge=0, le=100)
    take_profit_percent: float = Field(10.0, ge=0, le=100)


class DexSettings(BaseModel):
    """DEX related parameters."""

    gas_limit: int = Field(..., gt=21_000)
    tx_timeout: int = Field(..., gt=0)


class MevProtectionSettings(BaseModel):
    """Configuration for MEV protection features."""

    enabled: bool = Field(False)
    flashbots_url: str | None = None
    fork_rpc_url: str | None = None
    deviation_threshold: float = Field(0.05, ge=0)


class BatchSettings(BaseModel):
    """Batch transaction configuration."""

    enabled: bool = Field(False)
    multicall_address: str | None = None

    @validator("multicall_address")
    def check_multicall(
        cls, value: str | None
    ) -> str | None:  # noqa: D417
        if value and not Web3.is_address(value):
            raise ValueError("invalid address")
        return Web3.to_checksum_address(value) if value else None


class SlippageProtectionSettings(BaseModel):
    """Dynamic slippage protection parameters."""

    dynamic_slippage_enabled: bool = Field(False)
    max_slippage_bps: int = Field(50, ge=0)


class AppConfig(BaseModel):
    """Validated application configuration."""

    rpc_url: str
    private_key: str
    wallet_address: str
    token0_address: str
    token1_address: str
    uniswap_v2_router: str
    sushiswap_router: str
    uniswap_v3_quoter: str
    uniswap_v3_router: str
    curve_pool: str
    balancer_vault: str
    balancer_pool_id: str
    profit_threshold: float = Field(1.0, ge=0)
    poll_interval_seconds: int = Field(10, gt=0)
    slippage_tolerance_percent: float = Field(0.5, ge=0, le=100)
    trading: TradingSettings
    risk: RiskSettings
    dex: DexSettings
    mev: MevProtectionSettings
    batch: BatchSettings
    slippage_protection: SlippageProtectionSettings

    @validator(
        "wallet_address",
        "token0_address",
        "token1_address",
        "uniswap_v2_router",
        "sushiswap_router",
        "uniswap_v3_quoter",
        "uniswap_v3_router",
        "curve_pool",
        "balancer_vault",
    )
    def check_address(cls, value: str) -> str:  # noqa: D417
        if not Web3.is_address(value):
            raise ValueError("invalid address")
        return Web3.to_checksum_address(value)


class ConfigManager:
    """Loads and validates configuration with reload capability."""

    def __init__(self, env: str | None = None) -> None:
        self.env = env or os.getenv("APP_ENV", "dev")
        self._config = self._build_config()
        _update_globals(self._config)

    def _load_env_file(self) -> None:
        for file in (f".env.{self.env}", ".env"):
            path = Path(file)
            if path.is_file():
                load_dotenv(path, override=False)

    def _env(self, key: str) -> str:
        value = os.getenv(key, "").strip()
        if not value:
            raise ConfigurationError(f"{key} environment variable not set")
        return value

    def _build_dict(self) -> Dict[str, Any]:
        self._load_env_file()
        return {
            "rpc_url": self._env("RPC_URL"),
            "private_key": self._env("PRIVATE_KEY"),
            "wallet_address": self._env("WALLET_ADDRESS"),
            "token0_address": self._env("TOKEN0_ADDRESS"),
            "token1_address": self._env("TOKEN1_ADDRESS"),
            "uniswap_v2_router": self._env("UNISWAP_V2_ROUTER"),
            "sushiswap_router": self._env("SUSHISWAP_ROUTER"),
            "uniswap_v3_quoter": self._env("UNISWAP_V3_QUOTER"),
            "uniswap_v3_router": self._env("UNISWAP_V3_ROUTER"),
            "curve_pool": self._env("CURVE_POOL"),
            "balancer_vault": self._env("BALANCER_VAULT"),
            "balancer_pool_id": self._env("BALANCER_POOL_ID"),
            "profit_threshold": float(os.getenv("PROFIT_THRESHOLD", 1.0)),
            "poll_interval_seconds": int(os.getenv("POLL_INTERVAL_SECONDS", 10)),
            "slippage_tolerance_percent": float(
                os.getenv("SLIPPAGE_TOLERANCE_PERCENT", 0.5)
            ),
            "trading": {
                "max_position_size": float(os.getenv("MAX_POSITION_SIZE", 1.0)),
                "risk_limit": float(os.getenv("RISK_LIMIT", 0.01)),
                "max_daily_volume": float(os.getenv("MAX_DAILY_VOLUME", 100.0)),
            },
            "risk": {
                "max_drawdown_percent": float(
                    os.getenv("MAX_DRAWDOWN_PERCENT", 20.0)
                ),
                "stop_loss_percent": float(os.getenv("STOP_LOSS_PERCENT", 5.0)),
                "take_profit_percent": float(os.getenv("TAKE_PROFIT_PERCENT", 10.0)),
            },
            "dex": {
                "gas_limit": int(os.getenv("GAS_LIMIT", 250_000)),
                "tx_timeout": int(os.getenv("TX_TIMEOUT", 120)),
            },
            "mev": {
                "enabled": os.getenv("MEV_PROTECTION_ENABLED", "false").lower()
                == "true",
                "flashbots_url": os.getenv("FLASHBOTS_URL"),
                "fork_rpc_url": os.getenv("FORK_RPC_URL"),
                "deviation_threshold": float(
                    os.getenv("DEVIATION_THRESHOLD", 0.05)
                ),
            },
            "batch": {
                "enabled": os.getenv("BATCH_TRANSACTIONS_ENABLED", "false").lower()
                == "true",
                "multicall_address": os.getenv("MULTICALL_ADDRESS"),
            },
            "slippage_protection": {
                "dynamic_slippage_enabled": os.getenv(
                    "DYNAMIC_SLIPPAGE_ENABLED", "false"
                ).lower()
                == "true",
                "max_slippage_bps": int(os.getenv("MAX_SLIPPAGE_BPS", 50)),
            },
        }

    def _build_config(self) -> AppConfig:
        try:
            return AppConfig(**self._build_dict())
        except ValidationError as exc:
            raise ConfigurationError(str(exc)) from exc

    @property
    def config(self) -> AppConfig:
        return self._config

    def reload(self) -> AppConfig:
        self._config = self._build_config()
        _update_globals(self._config)
        return self._config


def _update_globals(cfg: AppConfig) -> None:
    mapping = {
        "RPC_URL": cfg.rpc_url,
        "PRIVATE_KEY": cfg.private_key,
        "WALLET_ADDRESS": cfg.wallet_address,
        "TOKEN0_ADDRESS": cfg.token0_address,
        "TOKEN1_ADDRESS": cfg.token1_address,
        "UNISWAP_V2_ROUTER": cfg.uniswap_v2_router,
        "SUSHISWAP_ROUTER": cfg.sushiswap_router,
        "UNISWAP_V3_QUOTER": cfg.uniswap_v3_quoter,
        "UNISWAP_V3_ROUTER": cfg.uniswap_v3_router,
        "CURVE_POOL": cfg.curve_pool,
        "BALANCER_VAULT": cfg.balancer_vault,
        "BALANCER_POOL_ID": cfg.balancer_pool_id,
        "PROFIT_THRESHOLD": cfg.profit_threshold,
        "POLL_INTERVAL_SECONDS": cfg.poll_interval_seconds,
        "SLIPPAGE_TOLERANCE_PERCENT": cfg.slippage_tolerance_percent,
        "MAX_POSITION_SIZE": cfg.trading.max_position_size,
        "RISK_LIMIT": cfg.trading.risk_limit,
        "MAX_DAILY_VOLUME": cfg.trading.max_daily_volume,
        "MAX_DRAWDOWN_PERCENT": cfg.risk.max_drawdown_percent,
        "STOP_LOSS_PERCENT": cfg.risk.stop_loss_percent,
        "TAKE_PROFIT_PERCENT": cfg.risk.take_profit_percent,
        "GAS_LIMIT": cfg.dex.gas_limit,
        "TX_TIMEOUT": cfg.dex.tx_timeout,
        "MEV_PROTECTION_ENABLED": cfg.mev.enabled,
        "FLASHBOTS_URL": cfg.mev.flashbots_url,
        "FORK_RPC_URL": cfg.mev.fork_rpc_url,
        "DEVIATION_THRESHOLD": cfg.mev.deviation_threshold,
        "BATCH_TRANSACTIONS_ENABLED": cfg.batch.enabled,
        "MULTICALL_ADDRESS": cfg.batch.multicall_address,
        "DYNAMIC_SLIPPAGE_ENABLED": cfg.slippage_protection.dynamic_slippage_enabled,
        "MAX_SLIPPAGE_BPS": cfg.slippage_protection.max_slippage_bps,
    }
    globals().update(mapping)


CONFIG_MANAGER = ConfigManager()

cfg = CONFIG_MANAGER.config
RPC_URL = cfg.rpc_url
PRIVATE_KEY = cfg.private_key
WALLET_ADDRESS = cfg.wallet_address
TOKEN0_ADDRESS = cfg.token0_address
TOKEN1_ADDRESS = cfg.token1_address
UNISWAP_V2_ROUTER = cfg.uniswap_v2_router
SUSHISWAP_ROUTER = cfg.sushiswap_router
UNISWAP_V3_QUOTER = cfg.uniswap_v3_quoter
UNISWAP_V3_ROUTER = cfg.uniswap_v3_router
CURVE_POOL = cfg.curve_pool
BALANCER_VAULT = cfg.balancer_vault
BALANCER_POOL_ID = cfg.balancer_pool_id
PROFIT_THRESHOLD = cfg.profit_threshold
POLL_INTERVAL_SECONDS = cfg.poll_interval_seconds
SLIPPAGE_TOLERANCE_PERCENT = cfg.slippage_tolerance_percent
MAX_POSITION_SIZE = cfg.trading.max_position_size
RISK_LIMIT = cfg.trading.risk_limit
MAX_DAILY_VOLUME = cfg.trading.max_daily_volume
MAX_DRAWDOWN_PERCENT = cfg.risk.max_drawdown_percent
STOP_LOSS_PERCENT = cfg.risk.stop_loss_percent
TAKE_PROFIT_PERCENT = cfg.risk.take_profit_percent
GAS_LIMIT = cfg.dex.gas_limit
TX_TIMEOUT = cfg.dex.tx_timeout
MEV_PROTECTION_ENABLED = cfg.mev.enabled
FLASHBOTS_URL = cfg.mev.flashbots_url
FORK_RPC_URL = cfg.mev.fork_rpc_url
DEVIATION_THRESHOLD = cfg.mev.deviation_threshold
BATCH_TRANSACTIONS_ENABLED = cfg.batch.enabled
MULTICALL_ADDRESS = cfg.batch.multicall_address
DYNAMIC_SLIPPAGE_ENABLED = cfg.slippage_protection.dynamic_slippage_enabled
MAX_SLIPPAGE_BPS = cfg.slippage_protection.max_slippage_bps

__all__ = [
    "CONFIG_MANAGER",
    "RPC_URL",
    "PRIVATE_KEY",
    "WALLET_ADDRESS",
    "TOKEN0_ADDRESS",
    "TOKEN1_ADDRESS",
    "UNISWAP_V2_ROUTER",
    "SUSHISWAP_ROUTER",
    "UNISWAP_V3_QUOTER",
    "UNISWAP_V3_ROUTER",
    "CURVE_POOL",
    "BALANCER_VAULT",
    "BALANCER_POOL_ID",
    "PROFIT_THRESHOLD",
    "POLL_INTERVAL_SECONDS",
    "SLIPPAGE_TOLERANCE_PERCENT",
    "MAX_POSITION_SIZE",
    "RISK_LIMIT",
    "MAX_DAILY_VOLUME",
    "MAX_DRAWDOWN_PERCENT",
    "STOP_LOSS_PERCENT",
    "TAKE_PROFIT_PERCENT",
    "GAS_LIMIT",
    "TX_TIMEOUT",
    "MEV_PROTECTION_ENABLED",
    "FLASHBOTS_URL",
    "FORK_RPC_URL",
    "DEVIATION_THRESHOLD",
    "BATCH_TRANSACTIONS_ENABLED",
    "MULTICALL_ADDRESS",
    "DYNAMIC_SLIPPAGE_ENABLED",
    "MAX_SLIPPAGE_BPS",
]
