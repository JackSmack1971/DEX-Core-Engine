# DEX-Core-Engine

## Overview

DEX-Core-Engine is a modular Ethereum trading bot focused on decentralized exchanges (DEXs). It provides a flexible framework with security, observability, and risk management features so new strategies can be implemented quickly.

### Feature Highlights
- **Multi-DEX Arbitrage** – Uniswap V2/V3, Curve, and Balancer adapters with multi-hop routing
- **Flash Loan & Cross-Chain Support** – Optional flash-loan based arbitrage and bridge price providers
- **Dynamic Slippage & MEV Protection** – Automated slippage checks and optional Flashbots submission
- **Batch Transactions** – Multicall batching to reduce gas usage
- **Portfolio & Risk Management** – Position sizing, drawdown limits, portfolio rebalancing
- **Analytics & Reporting** – Prometheus metrics, P&L reporting and export utilities
- **Resilience Utilities** – Circuit breaker, retry logic and Redis caching
- **REST API** – FastAPI application exposing health, metrics and analytics endpoints

## Project Layout
```
├── main.py                 # Command line entry point
├── config.py               # Pydantic-based configuration loader
├── dex_handler.py          # Uniswap‑style DEX interaction
├── routing/                # Multi-hop routing engine
├── strategies/             # Strategy framework and implementations
├── portfolio/              # Portfolio tracking and rebalancing
├── database/               # Async ORM models and repositories
├── analytics/              # Reporting and visualization tools
├── security/               # Key encryption and MEV protection
├── api/                    # FastAPI server with JWT auth
└── tests/                  # Pytest suite
```

## Installation
1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd DEX-Core-Engine
   ```
2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Python 3.9 or newer is required.

## Environment Configuration
All configuration is provided through environment variables. Copy `.env.example` and adjust values, then set additional variables as needed:

```
RPC_URL="..."                     # Ethereum node URL
ENCRYPTED_PRIVATE_KEY="..."       # Output of SecureKeyManager
MASTER_PASSWORD="..."             # Password used for decryption
WALLET_ADDRESS="..."              # Your wallet address
TOKEN0_ADDRESS="..."              # Token in
TOKEN1_ADDRESS="..."              # Token out
UNISWAP_V2_ROUTER="..."
SUSHISWAP_ROUTER="..."
UNISWAP_V3_QUOTER="..."
UNISWAP_V3_ROUTER="..."
CURVE_POOL="..."
BALANCER_VAULT="..."
BALANCER_POOL_ID="..."
MULTICALL_ADDRESS="..."           # Required when batching
MEV_PROTECTION_ENABLED=false
BATCH_TRANSACTIONS_ENABLED=false
PROFIT_THRESHOLD=1.0
POLL_INTERVAL_SECONDS=10
SLIPPAGE_TOLERANCE_PERCENT=0.5
TRADING__MAX_POSITION_SIZE=1.0
TRADING__RISK_LIMIT=0.02
TRADING__MAX_DAILY_VOLUME=100
RISK__MAX_DRAWDOWN_PERCENT=20
RISK__STOP_LOSS_PERCENT=5
RISK__TAKE_PROFIT_PERCENT=10
DEX__GAS_LIMIT=250000
DEX__TX_TIMEOUT=120
MEV__FLASHBOTS_URL="..."
MEV__FORK_RPC_URL="..."
MEV__DEVIATION_THRESHOLD=0.05
DYNAMIC_SLIPPAGE_ENABLED=false
MAX_SLIPPAGE_BPS=50
BATCH__MULTICALL_ADDRESS="..."
REBALANCE_THRESHOLD=0.05
MAX_PORTFOLIO_ASSETS=20
DATABASE__URL="postgresql+asyncpg://user:pass@localhost/db"
DATABASE__POOL_SIZE=5
DATABASE__MAX_OVERFLOW=10
DATABASE__POOL_TIMEOUT=30
DATABASE__POOL_RECYCLE=3600
DATABASE__ECHO=false
MARKET_DATA_URL="https://api.example.com/slippage"
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=""
REDIS_TIMEOUT=5
FX_API_URL="https://fx.example.com"
FX_API_KEY=""
EXPORT_DIR=exports
LOG_FILE=logs/dex_bot.log
LOG_LEVEL=INFO
JWT_SECRET_KEY="your-secret"
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=15
ALLOWED_HOSTS=localhost
CORS_ORIGINS=http://localhost
API_RATE_LIMIT=100
KEY_SALT="optional-salt"
APP_ENV=dev
```

### SecureKeyManager
Run `SecureKeyManager.setup_encrypted_config()` in a Python shell with your plain private key in the `PRIVATE_KEY` environment variable to generate `ENCRYPTED_PRIVATE_KEY`.

## Usage
### Run the trading bot
```bash
python main.py
```
The bot initializes the Web3 connection, loads DEX handlers and starts the default `ArbitrageStrategy` loop.

### Run the API server
```bash
uvicorn api:app --reload
```
Endpoints:
- `GET /health` – liveness probe
- `GET /ready` – readiness probe
- `GET /metrics` – Prometheus metrics (requires `analytics:read` permission)
- `GET /analytics/report?period=<daily|weekly|monthly>`
- `GET /analytics/performance?confidence=0.95`
- `POST /admin/shutdown` – trigger emergency shutdown

All protected routes use JWT authentication. Set `JWT_SECRET_KEY` and related variables before starting.

### Batch Transactions
When `BATCH_TRANSACTIONS_ENABLED` and `MULTICALL_ADDRESS` are configured:
```python
from batcher import Batcher
batcher = Batcher(web3_service, MULTICALL_ADDRESS)
tx_hash = await batcher.execute([call1, call2], reorder=True)
print(tx_hash)
```

### Database Migrations
Ensure `DATABASE__URL` is set.
```bash
alembic revision --autogenerate -m "Message"
alembic upgrade head
# rollback:
alembic downgrade -1
```

## Testing
The repository includes extensive Pytest suites. To run all tests with coverage:
```bash
pytest --cov=.
```

## Build & Deployment
No npm/yarn scripts are provided. Deployment typically involves:
1. Installing dependencies via `pip install -r requirements.txt` on the target server.
2. Running database migrations.
3. Starting the bot (`python main.py`) and/or the API server (`uvicorn api:app`).
Configure environment variables according to the target environment (`APP_ENV`).

## Contributing
Pull requests are welcome! Please follow these guidelines:
1. Ensure code is formatted with `black` and includes type hints.
2. Add unit tests for new functionality (aim for 80% coverage).
3. Do not commit secrets—always use environment variables for credentials.
4. Run `pytest` before submitting your PR.
5. Describe any API changes clearly in the PR message.

## License
MIT
