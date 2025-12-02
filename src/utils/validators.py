"""
Input validation utilities for Binance Futures Trading Bot.
Validates user input before sending to the API.
"""
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


# Valid order sides
VALID_SIDES = ["BUY", "SELL"]

# Valid order types
VALID_ORDER_TYPES = ["MARKET", "LIMIT", "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]

# Common futures symbols (not exhaustive, API will validate)
COMMON_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT",
    "DOGEUSDT", "SOLUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT"
]


def validate_symbol(symbol: str) -> str:
    """
    Validate trading symbol.
    
    Args:
        symbol: Trading pair symbol (e.g., BTCUSDT)
    
    Returns:
        Validated symbol in uppercase
    
    Raises:
        ValidationError: If symbol is invalid
    """
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
    """
    Validate order side.
    
    Args:
        side: Order side (BUY or SELL)
    
    Returns:
        Validated side in uppercase
    
    Raises:
        ValidationError: If side is invalid
    """
    if not side or not isinstance(side, str):
        raise ValidationError("Side is required and must be a string")
    
    side = side.upper().strip()
    
    if side not in VALID_SIDES:
        raise ValidationError(
            f"Invalid side '{side}'. Must be one of: {', '.join(VALID_SIDES)}"
        )
    
    return side


def validate_order_type(order_type: str) -> str:
    """
    Validate order type.
    
    Args:
        order_type: Type of order (MARKET, LIMIT, etc.)
    
    Returns:
        Validated order type in uppercase
    
    Raises:
        ValidationError: If order type is invalid
    """
    if not order_type or not isinstance(order_type, str):
        raise ValidationError("Order type is required and must be a string")
    
    order_type = order_type.upper().strip()
    
    if order_type not in VALID_ORDER_TYPES:
        raise ValidationError(
            f"Invalid order type '{order_type}'. Must be one of: {', '.join(VALID_ORDER_TYPES)}"
        )
    
    return order_type


def validate_quantity(quantity: str) -> Decimal:
    """
    Validate order quantity.
    
    Args:
        quantity: Order quantity as string
    
    Returns:
        Validated quantity as Decimal
    
    Raises:
        ValidationError: If quantity is invalid
    """
    if not quantity:
        raise ValidationError("Quantity is required")
    
    try:
        qty = Decimal(str(quantity).strip())
    except (InvalidOperation, ValueError):
        raise ValidationError(f"Invalid quantity format: {quantity}")
    
    if qty <= 0:
        raise ValidationError("Quantity must be greater than 0")
    
    return qty


def validate_price(price: Optional[str], order_type: str) -> Optional[Decimal]:
    """
    Validate order price.
    
    Args:
        price: Order price as string (required for LIMIT orders)
        order_type: Order type to determine if price is required
    
    Returns:
        Validated price as Decimal or None for MARKET orders
    
    Raises:
        ValidationError: If price is invalid or missing when required
    """
    # Price is required for LIMIT and STOP orders
    requires_price = order_type in ["LIMIT", "STOP", "TAKE_PROFIT"]
    
    if requires_price:
        if not price:
            raise ValidationError(f"Price is required for {order_type} orders")
        
        try:
            p = Decimal(str(price).strip())
        except (InvalidOperation, ValueError):
            raise ValidationError(f"Invalid price format: {price}")
        
        if p <= 0:
            raise ValidationError("Price must be greater than 0")
        
        return p
    
    # For MARKET orders, price is optional but validate if provided
    if price:
        try:
            p = Decimal(str(price).strip())
            if p <= 0:
                raise ValidationError("Price must be greater than 0")
            return p
        except (InvalidOperation, ValueError):
            raise ValidationError(f"Invalid price format: {price}")
    
    return None


def validate_stop_price(stop_price: Optional[str], order_type: str) -> Optional[Decimal]:
    """
    Validate stop price for stop orders.
    
    Args:
        stop_price: Stop price as string
        order_type: Order type to determine if stop price is required
    
    Returns:
        Validated stop price as Decimal or None
    
    Raises:
        ValidationError: If stop price is invalid or missing when required
    """
    requires_stop_price = order_type in ["STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]
    
    if requires_stop_price:
        if not stop_price:
            raise ValidationError(f"Stop price is required for {order_type} orders")
        
        try:
            sp = Decimal(str(stop_price).strip())
        except (InvalidOperation, ValueError):
            raise ValidationError(f"Invalid stop price format: {stop_price}")
        
        if sp <= 0:
            raise ValidationError("Stop price must be greater than 0")
        
        return sp
    
    return None


def validate_order_input(
    symbol: str,
    side: str,
    order_type: str,
    quantity: str,
    price: Optional[str] = None,
    stop_price: Optional[str] = None
) -> Tuple[str, str, str, Decimal, Optional[Decimal], Optional[Decimal]]:
    """
    Validate all order input parameters.
    
    Args:
        symbol: Trading pair symbol
        side: Order side (BUY/SELL)
        order_type: Order type (MARKET/LIMIT/etc.)
        quantity: Order quantity
        price: Order price (for LIMIT orders)
        stop_price: Stop price (for stop orders)
    
    Returns:
        Tuple of validated (symbol, side, order_type, quantity, price, stop_price)
    
    Raises:
        ValidationError: If any input is invalid
    """
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
