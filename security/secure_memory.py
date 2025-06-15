from __future__ import annotations

"""Memory locking and zeroing utilities."""

import ctypes
import sys
from contextlib import contextmanager
from typing import Iterator


def secure_zero_memory(data: bytearray) -> None:
    """Overwrite ``data`` with zeros."""
    addr = ctypes.addressof(ctypes.c_char.from_buffer(data))
    length = len(data)
    if sys.platform == "win32":
        ctypes.windll.kernel32.RtlSecureZeroMemory(addr, length)
    else:
        ctypes.memset(addr, 0, length)


def lock_memory(data: bytearray) -> None:
    """Prevent ``data`` from being swapped to disk."""
    addr = ctypes.addressof(ctypes.c_char.from_buffer(data))
    length = len(data)
    if sys.platform == "win32":
        ctypes.windll.kernel32.VirtualLock(addr, length)
    else:
        libc = ctypes.CDLL(None)
        libc.mlock(addr, length)


def unlock_memory(data: bytearray) -> None:
    """Release memory lock on ``data``."""
    addr = ctypes.addressof(ctypes.c_char.from_buffer(data))
    length = len(data)
    if sys.platform == "win32":
        ctypes.windll.kernel32.VirtualUnlock(addr, length)
    else:
        libc = ctypes.CDLL(None)
        libc.munlock(addr, length)


@contextmanager
def locked_memory(data: bytes) -> Iterator[memoryview]:
    """Yield a locked memoryview of ``data`` and securely zero on exit."""
    buf = bytearray(data)
    lock_memory(buf)
    try:
        yield memoryview(buf)
    finally:
        secure_zero_memory(buf)
        unlock_memory(buf)
