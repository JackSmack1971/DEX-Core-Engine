import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for test imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set default environment variables to satisfy config loading
os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("PRIVATE_KEY", "test")
os.environ.setdefault("WALLET_ADDRESS", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("TOKEN0_ADDRESS", "0x0000000000000000000000000000000000000001")
os.environ.setdefault("TOKEN1_ADDRESS", "0x0000000000000000000000000000000000000002")
os.environ.setdefault("UNISWAP_V2_ROUTER", "0x0000000000000000000000000000000000000003")
os.environ.setdefault("SUSHISWAP_ROUTER", "0x0000000000000000000000000000000000000004")
os.environ.setdefault("UNISWAP_V3_QUOTER", "0x0000000000000000000000000000000000000005")
os.environ.setdefault("UNISWAP_V3_ROUTER", "0x0000000000000000000000000000000000000006")
os.environ.setdefault("CURVE_POOL", "0x0000000000000000000000000000000000000007")
os.environ.setdefault("BALANCER_VAULT", "0x0000000000000000000000000000000000000008")
os.environ.setdefault("BALANCER_POOL_ID", "0xpool")
os.environ.setdefault("MULTICALL_ADDRESS", "0x0000000000000000000000000000000000000009")
os.environ.setdefault("BATCH_TRANSACTIONS_ENABLED", "false")
os.environ.setdefault("MEV_PROTECTION_ENABLED", "false")
os.environ.setdefault("MAX_POSITION_SIZE", "1.0")
os.environ.setdefault("RISK_LIMIT", "0.01")
os.environ.setdefault("MAX_DAILY_VOLUME", "100.0")
os.environ.setdefault("MAX_DRAWDOWN_PERCENT", "20.0")
os.environ.setdefault("STOP_LOSS_PERCENT", "5.0")
os.environ.setdefault("TAKE_PROFIT_PERCENT", "10.0")
os.environ.setdefault("GAS_LIMIT", "250000")
os.environ.setdefault("TX_TIMEOUT", "120")
os.environ.setdefault("DYNAMIC_SLIPPAGE_ENABLED", "false")
os.environ.setdefault("MAX_SLIPPAGE_BPS", "50")
