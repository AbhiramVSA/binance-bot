"""
Binance Futures Trading Bot - Main Entry Point

A simplified trading bot for Binance Futures Testnet.
Supports MARKET, LIMIT, and advanced order types (STOP, TAKE_PROFIT).

Usage:
    python main.py              # Run interactive CLI
    python main.py --help       # Show help

Environment Variables:
    BINANCE_API_KEY     - Your Binance API key
    BINANCE_API_SECRET  - Your Binance API secret
    USE_TESTNET         - Use testnet (default: True)
"""
import argparse
import sys

from src.cli import TradingCLI, quick_order, run_cli
from src.config.config import settings
from src.utils.logger import logger


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Binance Futures Trading Bot (Testnet)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive mode
  python main.py --quick -s BTCUSDT -S BUY -t MARKET -q 0.001
  python main.py --quick -s ETHUSDT -S SELL -t LIMIT -q 0.01 -p 2000
  python main.py --quick -s BTCUSDT -S SELL -t STOP_MARKET -q 0.001 --stop-price 90000

Environment:
  Set BINANCE_API_KEY and BINANCE_API_SECRET in .env file or environment variables.
  Set USE_TESTNET=true to use testnet (default) or USE_TESTNET=false for mainnet.
        """
    )
    
    parser.add_argument(
        "--quick", "-Q",
        action="store_true",
        help="Quick order mode (non-interactive)"
    )
    
    parser.add_argument(
        "--symbol", "-s",
        type=str,
        help="Trading symbol (e.g., BTCUSDT)"
    )
    
    parser.add_argument(
        "--side", "-S",
        type=str,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side (BUY or SELL)"
    )
    
    parser.add_argument(
        "--type", "-t",
        type=str,
        dest="order_type",
        choices=["MARKET", "LIMIT", "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET",
                 "market", "limit", "stop", "stop_market", "take_profit", "take_profit_market"],
        help="Order type"
    )
    
    parser.add_argument(
        "--quantity", "-q",
        type=str,
        help="Order quantity"
    )
    
    parser.add_argument(
        "--price", "-p",
        type=str,
        help="Order price (for LIMIT orders)"
    )
    
    parser.add_argument(
        "--stop-price",
        type=str,
        help="Stop price (for STOP orders)"
    )
    
    parser.add_argument(
        "--api-key",
        type=str,
        help="Binance API key (overrides environment)"
    )
    
    parser.add_argument(
        "--api-secret",
        type=str,
        help="Binance API secret (overrides environment)"
    )
    
    parser.add_argument(
        "--mainnet",
        action="store_true",
        help="Use mainnet instead of testnet (CAUTION: Real money!)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the trading bot."""
    args = parse_arguments()
    
    # Configure logging level
    if args.verbose:
        import logging
        logger.setLevel(logging.DEBUG)
    
    # Determine environment
    use_testnet = not args.mainnet
    
    if not use_testnet:
        print("\n⚠️  WARNING: Running in MAINNET mode!")
        print("    This will use REAL money. Press Ctrl+C to cancel.")
        print("-" * 50)
    
    # Quick order mode
    if args.quick:
        # Validate required arguments
        if not all([args.symbol, args.side, args.order_type, args.quantity]):
            print("Error: Quick mode requires --symbol, --side, --type, and --quantity")
            print("Example: python main.py --quick -s BTCUSDT -S BUY -t MARKET -q 0.001")
            sys.exit(1)
        
        # Get API credentials
        api_key = args.api_key or settings.BINANCE_API_KEY
        api_secret = args.api_secret or settings.BINANCE_API_SECRET
        
        if not api_key or not api_secret:
            print("Error: API credentials not provided.")
            print("Set BINANCE_API_KEY and BINANCE_API_SECRET in .env or pass --api-key and --api-secret")
            sys.exit(1)
        
        # Place order
        result = quick_order(
            symbol=args.symbol.upper(),
            side=args.side.upper(),
            order_type=args.order_type.upper(),
            quantity=args.quantity,
            price=args.price,
            stop_price=args.stop_price,
            api_key=api_key,
            api_secret=api_secret,
            use_testnet=use_testnet
        )
        
        # Display result
        if result.success:
            print("\n✅ Order placed successfully!")
            print(f"   Order ID: {result.order_id}")
            print(f"   Symbol: {result.symbol}")
            print(f"   Status: {result.status}")
            print(f"   Side: {result.side}")
            print(f"   Type: {result.order_type}")
            print(f"   Quantity: {result.quantity}")
            if result.price and result.price != "0":
                print(f"   Price: {result.price}")
            if result.executed_qty and result.executed_qty != "0":
                print(f"   Executed: {result.executed_qty}")
        else:
            print(f"\n❌ Order failed: {result.message}")
            if result.error_code:
                print(f"   Error Code: {result.error_code}")
            sys.exit(1)
    else:
        # Interactive CLI mode
        run_cli()


if __name__ == "__main__":
    main()
