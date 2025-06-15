"""Application configuration management."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from cryptography.fernet import Fernet
from pydantic import (
    BaseModel,
    Field,
    PostgresDsn,
    ValidationError,
    validator,
    field_validator,
)
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)
from web3 import Web3
from security import SecureKeyManager

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


class PortfolioSettings(BaseModel):
    """Portfolio management parameters."""

    rebalance_threshold: float = Field(0.05, ge=0, le=1)
    max_assets: int = Field(20, ge=1)


class DatabaseSettings(BaseSettings):
    """Database connection parameters."""

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_nested_delimiter="__",
    )

    url: PostgresDsn = Field(..., description="PostgreSQL connection URL")
    pool_size: int = Field(5, ge=1, le=20)
    max_overflow: int = Field(10, ge=0, le=50)
    pool_timeout: int = Field(30, ge=5, le=120)
    pool_recycle: int = Field(3600, ge=300)
    echo: bool = Field(False, description="Enable SQL query logging")
    require_ssl: bool = Field(True, description="Require SSL connections")
    encryption_key: str
    audit_encryption_key: str
    query_timeout: int

    @field_validator("encryption_key", "audit_encryption_key")
    @classmethod
    def _check_fernet_key(cls, value: str) -> str:
        if len(value) != 44:
            raise ValueError("Fernet key must be 44 characters")
        Fernet(value)
        return value


class AppConfig(BaseSettings):
    """Validated application configuration."""

    model_config = SettingsConfigDict(env_nested_delimiter="__")

    rpc_url: str
    encrypted_private_key: str
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
    portfolio: PortfolioSettings
    database: DatabaseSettings

    @property
    def private_key(self) -> str:
        """Decrypt the stored encrypted private key."""
        key_manager = SecureKeyManager()
        return key_manager.decrypt_private_key(self.encrypted_private_key)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Load .env files before reading environment variables."""

        def load_env() -> dict[str, Any]:
            env = os.getenv("APP_ENV", "dev")
            for file in (f".env.{env}", ".env"):
                path = Path(file)
                if path.is_file():
                    load_dotenv(path, override=False)
            return env_settings()

        return init_settings, load_env, dotenv_settings, file_secret_settings

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



    def _build_config(self) -> AppConfig:
        self._load_env_file()
        try:
            return AppConfig()
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
        "ENCRYPTED_PRIVATE_KEY": cfg.encrypted_private_key,
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
        "REBALANCE_THRESHOLD": cfg.portfolio.rebalance_threshold,
        "MAX_PORTFOLIO_ASSETS": cfg.portfolio.max_assets,
        "DATABASE__URL": cfg.database.url,
        "DATABASE__POOL_SIZE": cfg.database.pool_size,
        "DATABASE__MAX_OVERFLOW": cfg.database.max_overflow,
        "DATABASE__POOL_TIMEOUT": cfg.database.pool_timeout,
        "DATABASE__POOL_RECYCLE": cfg.database.pool_recycle,
        "DATABASE__ECHO": cfg.database.echo,
        "DATABASE__REQUIRE_SSL": cfg.database.require_ssl,
        "DATABASE__ENCRYPTION_KEY": cfg.database.encryption_key,
        "DATABASE__AUDIT_ENCRYPTION_KEY": cfg.database.audit_encryption_key,
        "DATABASE__QUERY_TIMEOUT": cfg.database.query_timeout,
    }
    globals().update(mapping)


CONFIG_MANAGER = ConfigManager()

cfg = CONFIG_MANAGER.config
RPC_URL = cfg.rpc_url
ENCRYPTED_PRIVATE_KEY = cfg.encrypted_private_key
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
REBALANCE_THRESHOLD = cfg.portfolio.rebalance_threshold
MAX_PORTFOLIO_ASSETS = cfg.portfolio.max_assets
DATABASE__URL = cfg.database.url
DATABASE__POOL_SIZE = cfg.database.pool_size
DATABASE__MAX_OVERFLOW = cfg.database.max_overflow
DATABASE__POOL_TIMEOUT = cfg.database.pool_timeout
DATABASE__POOL_RECYCLE = cfg.database.pool_recycle
DATABASE__ECHO = cfg.database.echo
DATABASE__REQUIRE_SSL = cfg.database.require_ssl
DATABASE__ENCRYPTION_KEY = cfg.database.encryption_key
DATABASE__AUDIT_ENCRYPTION_KEY = cfg.database.audit_encryption_key
DATABASE__QUERY_TIMEOUT = cfg.database.query_timeout

__all__ = [
    "CONFIG_MANAGER",
    "RPC_URL",
    "ENCRYPTED_PRIVATE_KEY",
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
    "REBALANCE_THRESHOLD",
    "MAX_PORTFOLIO_ASSETS",
    "DATABASE__URL",
    "DATABASE__POOL_SIZE",
    "DATABASE__MAX_OVERFLOW",
    "DATABASE__POOL_TIMEOUT",
    "DATABASE__POOL_RECYCLE",
    "DATABASE__ECHO",
    "DATABASE__REQUIRE_SSL",
    "DATABASE__ENCRYPTION_KEY",
    "DATABASE__AUDIT_ENCRYPTION_KEY",
    "DATABASE__QUERY_TIMEOUT",
]
