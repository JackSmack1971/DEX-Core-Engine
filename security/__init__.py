"""Security utilities for the trading bot."""

from .key_manager import SecureKeyManager, locked_memory, secure_zero_memory
from .secure_memory import lock_memory, unlock_memory

__all__ = [
    "SecureKeyManager",
    "secure_zero_memory",
    "locked_memory",
    "lock_memory",
    "unlock_memory",
]
