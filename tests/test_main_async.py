import os
import asyncio
from unittest.mock import AsyncMock, MagicMock

import main


def test_main_runs(monkeypatch):
    os.environ.setdefault("RPC_URL", "http://localhost")
    os.environ.setdefault("PRIVATE_KEY", "key")
    os.environ.setdefault("WALLET_ADDRESS", "addr")

    monkeypatch.setattr(main, "Web3Service", MagicMock())
    monkeypatch.setattr(main, "DEXHandler", MagicMock())

    strategy = MagicMock()
    strategy.run = AsyncMock()
    monkeypatch.setattr(main, "ArbitrageStrategy", MagicMock(return_value=strategy))

    def fake_run(coro):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coro)

    monkeypatch.setattr(main, "asyncio", MagicMock(run=fake_run))

    main.main()
    strategy.run.assert_awaited_once()
