import config


def test_portfolio_config_reload(monkeypatch):
    monkeypatch.setenv("PORTFOLIO__REBALANCE_THRESHOLD", "0.1")
    monkeypatch.setenv("PORTFOLIO__MAX_ASSETS", "30")
    config.CONFIG_MANAGER.reload()
    assert config.REBALANCE_THRESHOLD == 0.1
    assert config.MAX_PORTFOLIO_ASSETS == 30
