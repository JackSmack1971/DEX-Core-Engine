import os
os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("ENCRYPTED_PRIVATE_KEY", "encrypted")
os.environ.setdefault("WALLET_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")

from unittest.mock import AsyncMock, MagicMock

import pytest

import main


def test_setup_web3_service(monkeypatch):
    svc = MagicMock()
    monkeypatch.setattr(main, "Web3Service", MagicMock(return_value=svc))
    result = main.setup_web3_service()
    assert result is svc


def test_setup_dex_handlers(monkeypatch):
    svc = MagicMock()
    handler = MagicMock()
    monkeypatch.setattr(main, "DEXHandler", MagicMock(return_value=handler))
    handlers = main.setup_dex_handlers(svc)
    assert handlers == [handler, handler]
    main.DEXHandler.assert_any_call(svc, main.config.UNISWAP_V2_ROUTER)
    main.DEXHandler.assert_any_call(svc, main.config.SUSHISWAP_ROUTER)


@pytest.mark.asyncio
async def test_launch_strategy(monkeypatch):
    strategy = MagicMock()
    strategy.run = AsyncMock()
    monkeypatch.setattr(main, "ArbitrageStrategy", MagicMock(return_value=strategy))
    await main.launch_strategy([MagicMock()])
    strategy.run.assert_awaited_once()


def test_main_runs(monkeypatch):
    svc = MagicMock()
    handlers = [MagicMock()]
    monkeypatch.setattr(main, "setup_web3_service", MagicMock(return_value=svc))
    monkeypatch.setattr(main, "setup_dex_handlers", MagicMock(return_value=handlers))
    launch = AsyncMock()
    monkeypatch.setattr(main, "launch_strategy", launch)

    main.main()

    main.setup_web3_service.assert_called_once()
    main.setup_dex_handlers.assert_called_once_with(svc)
    launch.assert_awaited_once_with(handlers)
