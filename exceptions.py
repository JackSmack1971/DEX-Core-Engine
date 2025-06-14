"""Application specific exceptions with error codes."""

from dataclasses import dataclass


@dataclass
class BaseAppError(Exception):
    """Base class for application errors."""

    code: str
    message: str

    def __str__(self) -> str:  # noqa: D401 - simple str
        return f"[{self.code}] {self.message}"


class ConfigurationError(BaseAppError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__("config_error", message)


class DexError(BaseAppError):
    """Raised for errors while interacting with a DEX."""

    def __init__(self, message: str) -> None:
        super().__init__("dex_error", message)


class BatcherError(BaseAppError):
    """Raised for errors during batched transactions."""

    def __init__(self, message: str) -> None:
        super().__init__("batcher_error", message)


class StrategyError(BaseAppError):
    """Raised for errors in strategy execution or setup."""

    def __init__(self, message: str) -> None:
        super().__init__("strategy_error", message)


class InventoryError(BaseAppError):
    """Raised for inventory management issues."""

    def __init__(self, message: str) -> None:
        super().__init__("inventory_error", message)


class RateLimitError(BaseAppError):
    """Raised when a client exceeds allowed request rate."""

    def __init__(self, message: str) -> None:
        super().__init__("rate_limit", message)


class ServiceUnavailableError(BaseAppError):
    """Raised when a service dependency is unavailable."""

    def __init__(self, message: str) -> None:
        super().__init__("service_unavailable", message)


class DatabaseError(BaseAppError):
    """Raised for database related failures."""

    def __init__(self, message: str) -> None:
        super().__init__("database_error", message)




class PriceManipulationError(BaseAppError):
    """Raised when transaction simulation detects price manipulation."""

    def __init__(self, message: str) -> None:
        super().__init__("price_manipulation", message)


class AnalyticsAPIError(BaseAppError):
    """Raised when analytics API requests fail."""

    def __init__(self, message: str) -> None:
        super().__init__("analytics_error", message)
