from config import CONFIG_MANAGER


def test_database_settings_loaded():
    cfg = CONFIG_MANAGER.config.database
    assert str(cfg.url).startswith("postgresql")
    assert cfg.pool_size == 5
