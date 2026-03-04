# Binance Futures Trading Bot

A command-line trading bot for Binance USDT-M Futures with support for market, limit, and conditional order types. Designed for testnet usage with optional mainnet support.

## Architecture

```
main.py                     CLI entry point (argparse)
  ├── Interactive mode      Menu-driven session via TradingCLI
  └── Quick mode            Single order from CLI flags
        │
src/cli.py                  User interaction layer
src/controllers/            Order validation + execution
src/api/client.py           Binance REST API client (HMAC-signed)
src/config/                 Settings from .env / environment
src/utils/                  Logging and input validation
```

**Data flow:** User input → `OrderService` (validates) → `BinanceFuturesClient` (signs & sends) → Binance API

## Setup

```bash
git clone https://github.com/yourusername/binance-bot.git
cd binance-bot
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env  # then edit with your API credentials
```

### Getting Testnet API Keys

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Log in with GitHub → API Management → Generate new key pair
3. Add credentials to `.env`

## Usage

### Interactive Mode

```bash
python main.py
```

Menu options: place orders, view positions/open orders, cancel orders, check prices.

### Quick Mode (Scripting)

```bash
# Market buy
python main.py --quick -s BTCUSDT -S BUY -t MARKET -q 0.001

# Limit sell
python main.py --quick -s ETHUSDT -S SELL -t LIMIT -q 0.01 -p 2500

# Stop-market
python main.py --quick -s BTCUSDT -S SELL -t STOP_MARKET -q 0.001 --stop-price 90000
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--quick` | `-Q` | Non-interactive quick order mode |
| `--symbol` | `-s` | Trading symbol (e.g., BTCUSDT) |
| `--side` | `-S` | BUY or SELL |
| `--type` | `-t` | MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET |
| `--quantity` | `-q` | Order quantity |
| `--price` | `-p` | Limit price |
| `--stop-price` | | Stop/trigger price |
| `--mainnet` | | Use mainnet (real money) |
| `--verbose` | `-v` | DEBUG-level logging |

## Configuration

Environment variables (or `.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `BINANCE_API_KEY` | | API key |
| `BINANCE_API_SECRET` | | API secret |
| `USE_TESTNET` | `true` | Use testnet vs mainnet |
| `LOG_LEVEL` | `INFO` | Logging level |
| `LOG_TO_FILE` | `false` | Write logs to file |
| `LOG_FILE_PATH` | `trading_bot.log` | Log file path |

## Order Types

| Type | Description | Required Fields |
|------|-------------|-----------------|
| MARKET | Immediate execution at market price | symbol, side, quantity |
| LIMIT | Execute at specified price or better | + price |
| STOP | Stop-limit triggered at stop price | + price, stop_price |
| STOP_MARKET | Stop-market triggered at stop price | + stop_price |
| TAKE_PROFIT | Take-profit limit | + price, stop_price |
| TAKE_PROFIT_MARKET | Take-profit market | + stop_price |

## Development

```bash
# Install dev dependencies
pip install pytest pytest-cov

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## Programmatic Usage

```python
from src.controllers.order_service import OrderService

service = OrderService()
result = service.place_market_order("BTCUSDT", "BUY", "0.001")

if result.success:
    print(f"Order {result.order_id}: {result.status}")
else:
    print(f"Error: {result.message}")
```

## Disclaimer

This software is for educational purposes only. Cryptocurrency trading involves substantial risk. Always test on testnet before using mainnet. Never trade with funds you cannot afford to lose.

## License

MIT — see [LICENSE](LICENSE) for details.
