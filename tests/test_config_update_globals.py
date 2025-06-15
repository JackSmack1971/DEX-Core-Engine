from types import SimpleNamespace
import config


def make_cfg():
    trading = SimpleNamespace(max_position_size=1.0, risk_limit=0.1, max_daily_volume=10.0)
    risk = SimpleNamespace(max_drawdown_percent=1.0, stop_loss_percent=0.5, take_profit_percent=0.8)
    dex = SimpleNamespace(gas_limit=30000, tx_timeout=60)
    mev = SimpleNamespace(enabled=True, flashbots_url="http://x", fork_rpc_url="http://y", deviation_threshold=0.1)
    batch = SimpleNamespace(enabled=True, multicall_address="0x5")
    slippage = SimpleNamespace(dynamic_slippage_enabled=True, max_slippage_bps=50)
    portfolio = SimpleNamespace(rebalance_threshold=0.1, max_assets=5)
    database = SimpleNamespace(
        url="sqlite:///:memory:",
        pool_size=1,
        max_overflow=2,
        pool_timeout=5,
        pool_recycle=10,
        echo=False,
        require_ssl=True,
        encryption_key="a" * 44,
        audit_encryption_key="b" * 44,
        query_timeout=30,
    )
    return SimpleNamespace(
        rpc_url="rpc",
        encrypted_private_key="enc",
        wallet_address="0x1",
        token0_address="0x2",
        token1_address="0x3",
        uniswap_v2_router="0x4",
        sushiswap_router="0x5",
        uniswap_v3_quoter="0x6",
        uniswap_v3_router="0x7",
        curve_pool="0x8",
        balancer_vault="0x9",
        balancer_pool_id="pid",
        profit_threshold=1.0,
        poll_interval_seconds=1,
        slippage_tolerance_percent=0.5,
        trading=trading,
        risk=risk,
        dex=dex,
        mev=mev,
        batch=batch,
        slippage_protection=slippage,
        portfolio=portfolio,
        database=database,
    )


def test_update_globals_round_trip():
    original = config.cfg
    new_cfg = make_cfg()
    config._update_globals(new_cfg)
    assert config.RPC_URL == "rpc"
    assert config.MAX_POSITION_SIZE == 1.0
    assert config.DATABASE__POOL_SIZE == 1
    config._update_globals(original)

