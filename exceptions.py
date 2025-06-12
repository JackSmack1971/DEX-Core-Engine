class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

class DexError(Exception):
    """Raised for errors while interacting with a DEX."""

class StrategyError(Exception):
    """Raised for errors in strategy execution or setup."""

