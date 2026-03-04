"""Input validation for order parameters."""
from decimal import Decimal, InvalidOperation


class ValidationError(Exception):
    """Raised when order input validation fails."""
    pass


VALID_SIDES = ["BUY", "SELL"]

VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]

COMMON_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "SOLUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
]


def validate_symbol(symbol: str) -> str:
    """Validate and normalize a trading pair symbol (e.g. BTCUSDT)."""
    if not symbol or not isinstance(symbol, str):
        raise ValidationError("Symbol is required and must be a string")

    symbol = symbol.upper().strip()

    if len(symbol) < 5:
        raise ValidationError(f"Invalid symbol format: {symbol}")

    if not symbol.endswith(("USDT", "BUSD", "USD")):
        raise ValidationError(
            f"Symbol '{symbol}' should end with USDT, BUSD, or USD for futures trading"
        )

    return symbol


def validate_side(side: str) -> str:
    """Validate order side (BUY or SELL)."""
    if not side or not isinstance(side, str):
        raise ValidationError("Side is required and must be a string")

    side = side.upper().strip()

    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )

    return side


def validate_order_type(order_type: str) -> str:
    """Validate order type against supported types."""
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type is required and must be a string")

    order_type = order_type.upper().strip()

    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )

    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """Validate that quantity is a positive number."""
    if not quantity:
        raise ValidationError("Quantity is required")

    try:
        qty = Decimal(str(quantity).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid quantity format: {quantity}")

    if qty <= 0:
        raise ValidationError("Quantity must be greater than 0")

    return qty


def _parse_positive_decimal(value: str, label: str) -> Decimal:
    """Parse a string into a positive Decimal, raising ValidationError on failure."""
    try:
        d = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid {label} format: {value}")

    if d <= 0:
        raise ValidationError(f"{label.capitalize()} must be greater than 0")

    return d


def validate_price(price: str | None, order_type: str) -> Decimal | None:
    """Validate order price. Required for LIMIT, STOP, and TAKE_PROFIT orders."""
    requires_price = order_type in ["LIMIT", "STOP", "TAKE_PROFIT"]

    if requires_price:
        if not price:
            raise ValidationError(f"Price is required for {order_type} orders")
        return _parse_positive_decimal(price, "price")

    if price:
        return _parse_positive_decimal(price, "price")

    return None


def validate_stop_price(stop_price: str | None, order_type: str) -> Decimal | None:
    """Validate stop price. Required for STOP, STOP_MARKET, TAKE_PROFIT, and TAKE_PROFIT_MARKET."""
    requires_stop_price = order_type in ["STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]

    if requires_stop_price:
        if not stop_price:
            raise ValidationError(f"Stop price is required for {order_type} orders")
        return _parse_positive_decimal(stop_price, "stop price")

    return None


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: str | None = None,
    stop_price: str | None = None
) -> tuple[str, str, str, Decimal, Decimal | None, Decimal | None]:
    """Validate all order parameters. Returns a tuple of validated values."""
    validated_symbol = validate_symbol(symbol)
    validated_side = validate_side(side)
    validated_type = validate_order_type(order_type)
    validated_qty = validate_quantity(quantity)
    validated_price = validate_price(price, validated_type)
    validated_stop_price = validate_stop_price(stop_price, validated_type)

    return (
        validated_symbol,
        validated_side,
        validated_type,
        validated_qty,
        validated_price,
        validated_stop_price
    )
