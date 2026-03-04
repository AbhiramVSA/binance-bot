"""Interactive CLI and quick-order interface for the trading bot."""

from src.api.client import BinanceFuturesClient, BinanceAPIError
from src.controllers.order_service import OrderService, OrderResult
from src.config.config import settings
from src.utils.logger import logger
from src.utils.validators import (
    VALID_SIDES,
    VALID_ORDER_TYPES,
    COMMON_SYMBOLS,
    ValidationError,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
)


class TradingCLI:
    """
    Command-line interface for the trading bot.
    Handles user interaction and displays results.
    """
    
    MENU_OPTIONS = {
        "1": "Place Order",
        "2": "View Open Orders",
        "3": "View Positions",
        "4": "Cancel Order",
        "5": "Check Server Connection",
        "6": "Get Current Price",
        "0": "Exit"
    }
    
    def __init__(self, order_service: OrderService | None = None):
        """
        Initialize CLI.
        
        Args:
            order_service: OrderService instance (creates new if not provided)
        """
        self.order_service = order_service
        self._initialized = False
    
    def _ensure_initialized(self) -> bool:
        """Ensure order service is initialized with valid credentials."""
        if self._initialized:
            return True
        
        if not settings.is_configured():
            print("\n" + "=" * 60)
            print("API credentials not found in environment.")
            print("Please enter your Binance API credentials:")
            print("=" * 60)
            
            api_key = self._prompt("API Key: ", required=True)
            api_secret = self._prompt("API Secret: ", required=True)
            use_testnet = self._prompt_yes_no("Use Testnet?", default=True)
            
            try:
                client = BinanceFuturesClient(
                    api_key=api_key,
                    api_secret=api_secret,
                    use_testnet=use_testnet
                )
                self.order_service = OrderService(client)
                self._initialized = True
            except Exception as e:
                print(f"\nError initializing client: {e}")
                return False
        else:
            if self.order_service is None:
                self.order_service = OrderService()
            self._initialized = True
        
        return True
    
    def run(self) -> None:
        """Run the CLI main loop."""
        self._print_header()

        if not self._ensure_initialized():
            print("Failed to initialize. Exiting.")
            return

        self._print_status()
        
        while True:
            try:
                choice = self._show_menu()
                
                if choice == "0":
                    print("\nGoodbye! Happy trading! 🚀")
                    break
                elif choice == "1":
                    self._handle_place_order()
                elif choice == "2":
                    self._handle_view_orders()
                elif choice == "3":
                    self._handle_view_positions()
                elif choice == "4":
                    self._handle_cancel_order()
                elif choice == "5":
                    self._handle_check_connection()
                elif choice == "6":
                    self._handle_get_price()
                else:
                    print("\nInvalid option. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nInterrupted. Goodbye!")
                break
            except (BinanceAPIError, ValueError, OSError) as e:
                logger.error(f"Error in CLI: {e}")
                print(f"\nError: {e}")
    
    def _print_header(self) -> None:
        """Print application header."""
        print("\n" + "=" * 60)
        print("  BINANCE FUTURES TRADING BOT")
        print("=" * 60)

    def _print_status(self) -> None:
        """Print connection status after initialization."""
        if self.order_service and self.order_service.client:
            client = self.order_service.client
            env = "TESTNET" if client.use_testnet else "MAINNET"
            print(f"  Environment: {env}")
            print(f"  API URL: {client.base_url}")
        else:
            env = "TESTNET" if settings.USE_TESTNET else "MAINNET"
            print(f"  Environment: {env}")
            print(f"  API URL: {settings.base_url}")
        print("=" * 60)
    
    def _show_menu(self) -> str:
        """Display menu and get user choice."""
        print("\n" + "-" * 40)
        print("MAIN MENU")
        print("-" * 40)
        for key, value in self.MENU_OPTIONS.items():
            print(f"  [{key}] {value}")
        print("-" * 40)
        return input("Select option: ").strip()
    
    def _prompt(self, message: str, required: bool = False, default: str | None = None) -> str:
        """
        Prompt user for input.
        
        Args:
            message: Prompt message
            required: Whether input is required
            default: Default value if not required
        
        Returns:
            User input or default
        """
        if default:
            message = f"{message} [{default}]: "
        
        while True:
            value = input(message).strip()
            
            if not value:
                if default:
                    return default
                if required:
                    print("This field is required.")
                    continue
                return ""
            
            return value
    
    def _prompt_yes_no(self, message: str, default: bool = True) -> bool:
        """Prompt for yes/no input."""
        default_str = "Y/n" if default else "y/N"
        response = input(f"{message} [{default_str}]: ").strip().lower()
        
        if not response:
            return default
        
        return response in ("y", "yes", "1", "true")
    
    def _prompt_choice(self, message: str, choices: list, show_choices: bool = True) -> str:
        """Prompt user to select from choices."""
        if show_choices:
            print(f"  Options: {', '.join(choices)}")
        
        while True:
            value = input(message).strip().upper()
            if value in choices:
                return value
            print(f"  Invalid choice. Options: {', '.join(choices)}")
    
    def _handle_place_order(self) -> None:
        """Handle order placement flow."""
        print("\n" + "=" * 40)
        print("PLACE NEW ORDER")
        print("=" * 40)
        
        # Select order type first
        print("\nOrder Types:")
        order_types = ["MARKET", "LIMIT", "STOP_MARKET", "STOP", "TAKE_PROFIT_MARKET", "TAKE_PROFIT"]
        for i, ot in enumerate(order_types, 1):
            print(f"  [{i}] {ot}")

        type_choice = self._prompt(f"Select order type (1-{len(order_types)}): ", required=True)
        try:
            order_type = order_types[int(type_choice) - 1]
        except (ValueError, IndexError):
            print("Invalid order type selection.")
            return
        
        # Common inputs
        print(f"\nCommon symbols: {', '.join(COMMON_SYMBOLS[:5])}...")
        symbol = self._prompt("Symbol (e.g., BTCUSDT): ", required=True).upper()
        
        side = self._prompt_choice("Side: ", VALID_SIDES)
        quantity = self._prompt("Quantity: ", required=True)
        
        # Type-specific inputs
        price = None
        stop_price = None
        
        if order_type == "LIMIT":
            price = self._prompt("Price: ", required=True)
        elif order_type == "STOP_MARKET":
            stop_price = self._prompt("Stop Price: ", required=True)
        elif order_type == "STOP":
            stop_price = self._prompt("Stop Price (trigger): ", required=True)
            price = self._prompt("Limit Price (execution): ", required=True)
        elif order_type == "TAKE_PROFIT_MARKET":
            stop_price = self._prompt("Take Profit Price: ", required=True)
        elif order_type == "TAKE_PROFIT":
            stop_price = self._prompt("Take Profit Price (trigger): ", required=True)
            price = self._prompt("Limit Price (execution): ", required=True)
        
        reduce_only = self._prompt_yes_no("Reduce Only?", default=False)
        
        # Confirm order
        print("\n" + "-" * 40)
        print("ORDER SUMMARY")
        print("-" * 40)
        print(f"  Symbol: {symbol}")
        print(f"  Type: {order_type}")
        print(f"  Side: {side}")
        print(f"  Quantity: {quantity}")
        if price:
            print(f"  Price: {price}")
        if stop_price:
            print(f"  Stop Price: {stop_price}")
        print(f"  Reduce Only: {reduce_only}")
        print("-" * 40)
        
        if not self._prompt_yes_no("Confirm order?", default=True):
            print("Order cancelled.")
            return
        
        # Place order
        print("\nPlacing order...")
        result = self.order_service.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            reduce_only=reduce_only
        )
        
        self._display_order_result(result)
    
    def _display_order_result(self, result: OrderResult) -> None:
        """Display order result."""
        print("\n" + "=" * 40)
        if result.success:
            print("✅ ORDER SUCCESSFUL")
        else:
            print("❌ ORDER FAILED")
        print("=" * 40)
        
        if result.success:
            print(f"  Order ID: {result.order_id}")
            print(f"  Symbol: {result.symbol}")
            print(f"  Status: {result.status}")
            print(f"  Side: {result.side}")
            print(f"  Type: {result.order_type}")
            print(f"  Quantity: {result.quantity}")
            if result.price and result.price != "0":
                print(f"  Price: {result.price}")
            if result.executed_qty and result.executed_qty != "0":
                print(f"  Executed: {result.executed_qty}")
            if result.avg_price and result.avg_price != "0":
                print(f"  Avg Price: {result.avg_price}")
        else:
            print(f"  Error: {result.message}")
            if result.error_code:
                print(f"  Error Code: {result.error_code}")
        
        print("=" * 40)
    
    def _handle_view_orders(self) -> None:
        """Handle viewing open orders."""
        print("\n" + "=" * 40)
        print("OPEN ORDERS")
        print("=" * 40)
        
        symbol = self._prompt("Symbol (leave empty for all): ")
        symbol = symbol.upper() if symbol else None
        
        result = self.order_service.get_open_orders(symbol)
        
        if not result["success"]:
            print(f"Error: {result.get('error')}")
            return
        
        orders = result.get("orders", [])
        
        if not orders:
            print("No open orders found.")
            return
        
        for order in orders:
            print(f"\n  Order ID: {order.get('orderId')}")
            print(f"  Symbol: {order.get('symbol')}")
            print(f"  Type: {order.get('type')}")
            print(f"  Side: {order.get('side')}")
            print(f"  Price: {order.get('price')}")
            print(f"  Quantity: {order.get('origQty')}")
            print(f"  Status: {order.get('status')}")
            print("-" * 40)
    
    def _handle_view_positions(self) -> None:
        """Handle viewing positions."""
        print("\n" + "=" * 40)
        print("POSITIONS")
        print("=" * 40)
        
        symbol = self._prompt("Symbol (leave empty for all): ")
        symbol = symbol.upper() if symbol else None
        
        result = self.order_service.get_positions(symbol)
        
        if not result["success"]:
            print(f"Error: {result.get('error')}")
            return
        
        positions = result.get("positions", [])
        
        # Filter to only show positions with non-zero amount
        active_positions = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
        
        if not active_positions:
            print("No active positions found.")
            return
        
        for pos in active_positions:
            print(f"\n  Symbol: {pos.get('symbol')}")
            print(f"  Position Amount: {pos.get('positionAmt')}")
            print(f"  Entry Price: {pos.get('entryPrice')}")
            print(f"  Mark Price: {pos.get('markPrice')}")
            print(f"  Unrealized PnL: {pos.get('unRealizedProfit')}")
            print(f"  Leverage: {pos.get('leverage')}")
            print("-" * 40)
    
    def _handle_cancel_order(self) -> None:
        """Handle order cancellation."""
        print("\n" + "=" * 40)
        print("CANCEL ORDER")
        print("=" * 40)
        
        symbol = self._prompt("Symbol: ", required=True).upper()
        order_id = self._prompt("Order ID: ", required=True)
        
        try:
            order_id = int(order_id)
        except ValueError:
            print("Invalid order ID.")
            return
        
        if not self._prompt_yes_no("Confirm cancellation?", default=False):
            print("Cancellation aborted.")
            return
        
        result = self.order_service.cancel_order(symbol, order_id)
        
        if result.success:
            print(f"\n✅ Order {order_id} cancelled successfully.")
        else:
            print(f"\n❌ Failed to cancel order: {result.message}")
    
    def _handle_check_connection(self) -> None:
        """Handle connection check."""
        print("\n" + "=" * 40)
        print("SERVER CONNECTION")
        print("=" * 40)
        
        try:
            server_time = self.order_service.client.get_server_time()
            print(f"✅ Connected to Binance")
            print(f"  Server Time: {server_time.get('serverTime')}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
    
    def _handle_get_price(self) -> None:
        """Handle getting current price."""
        print("\n" + "=" * 40)
        print("CURRENT PRICE")
        print("=" * 40)
        
        symbol = self._prompt("Symbol (e.g., BTCUSDT): ", required=True).upper()
        
        try:
            price_data = self.order_service.client.get_ticker_price(symbol)
            print(f"\n  Symbol: {price_data.get('symbol')}")
            print(f"  Price: {price_data.get('price')}")
        except Exception as e:
            print(f"Error: {e}")


def quick_order(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
    stop_price: str | None = None,
    api_key: str | None = None,
    api_secret: str | None = None,
    use_testnet: bool = True
) -> OrderResult:
    """
    Quick function to place an order without CLI interaction.
    
    Args:
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        order_type: Order type (MARKET/LIMIT/etc.)
        quantity: Order quantity
        price: Order price (for LIMIT orders)
        stop_price: Stop price (for stop orders)
        api_key: Binance API key
        api_secret: Binance API secret
        use_testnet: Whether to use testnet
    
    Returns:
        OrderResult with order details
    """
    client = BinanceFuturesClient(
        api_key=api_key,
        api_secret=api_secret,
        use_testnet=use_testnet
    )
    service = OrderService(client)
    
    return service.place_order(
        symbol=symbol,
        side=side,
        order_type=order_type,
        quantity=quantity,
        price=price,
        stop_price=stop_price
    )


def run_cli() -> None:
    """Entry point for running the CLI."""
    cli = TradingCLI()
    cli.run()


if __name__ == "__main__":
    run_cli()
