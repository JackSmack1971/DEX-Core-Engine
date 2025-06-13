import os

import config


def test_config_manager_loads_defaults():
    cfg = config.CONFIG_MANAGER.config
    assert cfg.rpc_url == os.environ["RPC_URL"]
    assert cfg.trading.max_position_size == float(os.environ["MAX_POSITION_SIZE"])
    assert (
        cfg.slippage_protection.max_slippage_bps
        == int(os.environ["MAX_SLIPPAGE_BPS"])
    )


def test_config_reload(monkeypatch):
    monkeypatch.setenv("PROFIT_THRESHOLD", "2.5")
    monkeypatch.setenv("MAX_SLIPPAGE_BPS", "75")
    config.CONFIG_MANAGER.reload()
    assert config.PROFIT_THRESHOLD == 2.5
    assert config.MAX_SLIPPAGE_BPS == 75
