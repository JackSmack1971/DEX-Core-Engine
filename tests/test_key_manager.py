import os
import pytest

from security import SecureKeyManager


@pytest.fixture
def key_manager(monkeypatch) -> SecureKeyManager:
    monkeypatch.setenv("MASTER_PASSWORD", "pass")
    monkeypatch.setenv("KEY_SALT", "testsalt")
    return SecureKeyManager()


def test_encrypt_decrypt_round_trip(key_manager: SecureKeyManager):
    encrypted = key_manager.encrypt_private_key("secret")
    decrypted = key_manager.decrypt_private_key(encrypted)
    assert decrypted == "secret"


def test_decrypt_invalid_raises(key_manager: SecureKeyManager):
    with pytest.raises(ValueError):
        key_manager.decrypt_private_key("invalid")

