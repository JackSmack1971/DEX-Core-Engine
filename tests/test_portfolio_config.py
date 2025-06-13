import config


def test_portfolio_config_reload(monkeypatch):
    monkeypatch.setenv("REBALANCE_THRESHOLD", "0.1")
    monkeypatch.setenv("MAX_PORTFOLIO_ASSETS", "30")
    config.CONFIG_MANAGER.reload()
    assert config.REBALANCE_THRESHOLD == 0.1
    assert config.MAX_PORTFOLIO_ASSETS == 30
