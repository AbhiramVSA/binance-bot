# Binance Futures Trading Bot

A simplified command-line trading bot for Binance USDT-M Futures, designed primarily for testnet usage. This bot provides a clean interface for placing market, limit, and advanced order types through both interactive and command-line modes.

## Features

- Support for Binance Futures Testnet and Mainnet
- Multiple order types: MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET
- Interactive CLI with menu-driven interface
- Quick command-line mode for scripting and automation
- Input validation with clear error messages
- Comprehensive logging of all API requests and responses
- Modular architecture for easy extension

## Requirements

- Python 3.10 or higher
- Binance Futures account (Testnet or Mainnet)
- API Key and Secret from Binance

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/binance-bot.git
cd binance-bot
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

Or install directly:

```bash
pip install pydantic pydantic-settings requests
```

4. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your Binance API credentials:

```
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
USE_TESTNET=true
```

## Getting Testnet API Keys

1. Visit [Binance Futures Testnet](https://testnet.binancefuture.com/)
2. Log in with your GitHub account
3. Navigate to API Management
4. Generate a new API key pair
5. Copy the API Key and Secret to your `.env` file

## Usage

### Interactive Mode

Run the bot without arguments to enter interactive mode:

```bash
python main.py
```

The interactive menu provides options to:
- Place orders (Market, Limit, Stop, Take Profit)
- View open orders
- View positions
- Cancel orders
- Check server connection
- Get current prices

### Command-Line Mode

For quick order placement or scripting, use the `--quick` flag:

```bash
# Place a market buy order
python main.py --quick -s BTCUSDT -S BUY -t MARKET -q 0.001

# Place a limit sell order
python main.py --quick -s ETHUSDT -S SELL -t LIMIT -q 0.01 -p 2500

# Place a stop-market order
python main.py --quick -s BTCUSDT -S SELL -t STOP_MARKET -q 0.001 --stop-price 90000
```

### Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--quick` | `-Q` | Enable quick order mode (non-interactive) |
| `--symbol` | `-s` | Trading symbol (e.g., BTCUSDT) |
| `--side` | `-S` | Order side: BUY or SELL |
| `--type` | `-t` | Order type: MARKET, LIMIT, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET |
| `--quantity` | `-q` | Order quantity |
| `--price` | `-p` | Limit price (required for LIMIT orders) |
| `--stop-price` | | Stop/trigger price (required for STOP orders) |
| `--api-key` | | Override API key from environment |
| `--api-secret` | | Override API secret from environment |
| `--mainnet` | | Use mainnet instead of testnet |
| `--verbose` | `-v` | Enable verbose logging |
| `--help` | `-h` | Show help message |

## Configuration

Configuration is managed through environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `BINANCE_API_KEY` | | Your Binance API key |
| `BINANCE_API_SECRET` | | Your Binance API secret |
| `USE_TESTNET` | `true` | Use testnet (`true`) or mainnet (`false`) |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `LOG_TO_FILE` | `false` | Enable file logging |
| `LOG_FILE_PATH` | `trading_bot.log` | Log file path |

## Project Structure

```
binance-bot/
├── main.py                 # Application entry point
├── pyproject.toml          # Project metadata and dependencies
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables template
├── README.md               # This file
└── src/
    ├── __init__.py
    ├── cli.py              # Command-line interface
    ├── api/
    │   ├── __init__.py
    │   └── client.py       # Binance API client
    ├── config/
    │   ├── __init__.py
    │   └── config.py       # Configuration management
    ├── controllers/
    │   ├── __init__.py
    │   └── order_service.py # Order management service
    └── utils/
        ├── __init__.py
        ├── logger.py       # Logging utilities
        └── validators.py   # Input validation
```

## API Reference

### BinanceFuturesClient

The main client for interacting with the Binance Futures API.

```python
from src.api.client import BinanceFuturesClient

client = BinanceFuturesClient(
    api_key="your_key",
    api_secret="your_secret",
    use_testnet=True
)

# Get current price
price = client.get_ticker_price("BTCUSDT")

# Place an order
response = client.place_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=Decimal("0.001")
)
```

### OrderService

High-level service for order management with validation.

```python
from src.controllers.order_service import OrderService

service = OrderService()

# Place a market order
result = service.place_market_order(
    symbol="BTCUSDT",
    side="BUY",
    quantity="0.001"
)

# Place a limit order
result = service.place_limit_order(
    symbol="ETHUSDT",
    side="SELL",
    quantity="0.01",
    price="2500"
)

if result.success:
    print(f"Order placed: {result.order_id}")
else:
    print(f"Error: {result.message}")
```

## Supported Order Types

| Order Type | Description | Required Parameters |
|------------|-------------|---------------------|
| MARKET | Execute immediately at market price | symbol, side, quantity |
| LIMIT | Execute at specified price or better | symbol, side, quantity, price |
| STOP | Stop-limit order triggered at stop price | symbol, side, quantity, price, stop_price |
| STOP_MARKET | Stop-market order triggered at stop price | symbol, side, quantity, stop_price |
| TAKE_PROFIT | Take-profit limit order | symbol, side, quantity, price, stop_price |
| TAKE_PROFIT_MARKET | Take-profit market order | symbol, side, quantity, stop_price |

## Error Handling

The bot handles various error conditions:

- **Validation Errors**: Invalid input parameters are caught before API calls
- **API Errors**: Binance API errors are captured with error codes and messages
- **Network Errors**: Connection issues and timeouts are handled gracefully
- **Authentication Errors**: Invalid API credentials are reported clearly

All errors are logged and displayed to the user with actionable information.

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. Format code with:

```bash
black src/
```

### Adding New Order Types

1. Add the order type to `VALID_ORDER_TYPES` in `src/utils/validators.py`
2. Update validation logic in `validate_price()` and `validate_stop_price()`
3. Add handling in `BinanceFuturesClient.place_order()`
4. Create a convenience method in `OrderService`
5. Update the CLI menu in `src/cli.py`

## Security Considerations

- Never commit your `.env` file or expose API credentials
- Use testnet for development and testing
- Enable IP restrictions on your API keys when possible
- The bot sanitizes sensitive data in logs
- Consider using read-only API keys when only viewing data

## Disclaimer

This software is provided for educational and informational purposes only. Trading cryptocurrencies involves substantial risk of loss. The authors are not responsible for any financial losses incurred through the use of this software.

- Always test thoroughly on testnet before using mainnet
- Never trade with funds you cannot afford to lose
- Past performance does not guarantee future results

## Contributing

Contributions are welcome. Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

Please ensure your code:
- Follows the existing code style
- Includes appropriate error handling
- Updates documentation as needed

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Binance API Documentation](https://binance-docs.github.io/apidocs/futures/en/)
- [python-binance](https://github.com/sammchardy/python-binance) for API reference
