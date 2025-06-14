from config import CONFIG_MANAGER


def test_database_settings_loaded():
    cfg = CONFIG_MANAGER.config.database
    assert cfg.url.startswith("sqlite")
    assert cfg.pool_size == 5
