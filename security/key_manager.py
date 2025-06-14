from __future__ import annotations

"""Secure private key encryption and decryption utilities."""

import base64
import getpass
import os
import secrets
import ctypes
import sys

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id


def secure_zero_memory(data: bytearray) -> None:
    """Securely zero memory containing sensitive data."""
    addr = ctypes.addressof(ctypes.c_char.from_buffer(data))
    length = len(data)
    if sys.platform == "win32":
        ctypes.windll.kernel32.RtlSecureZeroMemory(addr, length)
    else:
        ctypes.memset(addr, 0, length)


class SecureKeyManager:
    """Manage encryption and decryption of private keys."""

    def __init__(self) -> None:
        password = os.getenv("MASTER_PASSWORD")
        if password is None:
            password = getpass.getpass("Enter master password: ")
        self.master_password = password
        salt_env = os.getenv("KEY_SALT")
        salt = salt_env.encode() if salt_env else secrets.token_bytes(16)
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=3,
            lanes=4,
            memory_cost=65536,
        )
        key = kdf.derive(password.encode())
        self._fernet = Fernet(base64.urlsafe_b64encode(key))
        secure_zero_memory(bytearray(key))

    def encrypt_private_key(self, private_key: str) -> str:
        """Encrypt ``private_key`` for storage."""
        return self._fernet.encrypt(private_key.encode()).decode()

    def decrypt_private_key(self, encrypted_key: str) -> str:
        """Decrypt an encrypted private key."""
        try:
            data = self._fernet.decrypt(encrypted_key.encode())
        except Exception as exc:  # noqa: BLE001
            raise ValueError("Invalid encryption key or corrupted data") from exc
        result = data.decode()
        secure_zero_memory(bytearray(data))
        return result

    def setup_encrypted_config(self) -> None:
        """Print helper instructions for encrypting existing configs."""
        plain = os.getenv("PRIVATE_KEY")
        if plain and not os.getenv("ENCRYPTED_PRIVATE_KEY"):
            encrypted = self.encrypt_private_key(plain)
            print("Add this to your .env file:")
            print(f"ENCRYPTED_PRIVATE_KEY={encrypted}")
            print("Remove PRIVATE_KEY from .env after adding ENCRYPTED_PRIVATE_KEY")

    def rotate_encrypted_key(self, new_private_key: str) -> str:
        """Encrypt ``new_private_key`` with the current password."""
        return self.encrypt_private_key(new_private_key)


__all__ = ["SecureKeyManager", "secure_zero_memory"]
