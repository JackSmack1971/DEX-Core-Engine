import os
import sys
from pathlib import Path

# Ensure project root is on sys.path for test imports
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Set default environment variables to satisfy config loading
os.environ.setdefault("RPC_URL", "http://localhost")
os.environ.setdefault("ENCRYPTED_PRIVATE_KEY", "encrypted")
os.environ.setdefault("MASTER_PASSWORD", "password")
os.environ.setdefault("KEY_SALT", "testsalt")
os.environ.setdefault("JWT_SECRET_KEY", "testsecret")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,testserver")
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
os.environ.setdefault(
    "BATCH__MULTICALL_ADDRESS",
    "0x0000000000000000000000000000000000000009",
)
os.environ.setdefault("BATCH__ENABLED", "false")
os.environ.setdefault("MEV__ENABLED", "false")
os.environ.setdefault("TRADING__MAX_POSITION_SIZE", "1.0")
os.environ.setdefault("TRADING__RISK_LIMIT", "0.01")
os.environ.setdefault("TRADING__MAX_DAILY_VOLUME", "100.0")
os.environ.setdefault("RISK__MAX_DRAWDOWN_PERCENT", "20.0")
os.environ.setdefault("RISK__STOP_LOSS_PERCENT", "5.0")
os.environ.setdefault("RISK__TAKE_PROFIT_PERCENT", "10.0")
os.environ.setdefault("DEX__GAS_LIMIT", "250000")
os.environ.setdefault("DEX__TX_TIMEOUT", "120")
os.environ.setdefault("SLIPPAGE_PROTECTION__DYNAMIC_SLIPPAGE_ENABLED", "false")
os.environ.setdefault("SLIPPAGE_PROTECTION__MAX_SLIPPAGE_BPS", "50")
os.environ.setdefault("PORTFOLIO__REBALANCE_THRESHOLD", "0.05")
os.environ.setdefault("PORTFOLIO__MAX_ASSETS", "20")
os.environ.setdefault(
    "DATABASE__URL",
    "postgresql+asyncpg://user:pass@localhost/test",
)
os.environ.setdefault("DATABASE__POOL_SIZE", "5")
os.environ.setdefault("DATABASE__MAX_OVERFLOW", "10")
os.environ.setdefault("DATABASE__POOL_TIMEOUT", "30")
os.environ.setdefault("DATABASE__POOL_RECYCLE", "3600")
os.environ.setdefault("DATABASE__ECHO", "false")
os.environ.setdefault("DATABASE__REQUIRE_SSL", "true")
os.environ.setdefault(
    "DATABASE__ENCRYPTION_KEY",
    "8ZUJoRb_GXBDTPjL_Q0msBmE0vpo-hDabEIUkfGfs04=",
)
os.environ.setdefault(
    "DATABASE__AUDIT_ENCRYPTION_KEY",
    "oh-tvfXPINv_kIWFlUufdfrwqcoYlEtp6SuMziSRVLI=",
)
os.environ.setdefault("DATABASE__QUERY_TIMEOUT", "30")
