import pytest
from config import CONFIG_MANAGER
from exceptions import ConfigurationError


def test_database_settings_loaded():
    cfg = CONFIG_MANAGER.config.database
    assert str(cfg.url).startswith("postgresql")
    assert cfg.pool_size == 5
    assert cfg.require_ssl is True
    assert len(cfg.encryption_key) == 44
    assert len(cfg.audit_encryption_key) == 44
    assert cfg.query_timeout == 30


def test_invalid_encryption_key(monkeypatch):
    monkeypatch.setenv("DATABASE__ENCRYPTION_KEY", "x" * 44)
    with pytest.raises(ConfigurationError):
        CONFIG_MANAGER.reload()
