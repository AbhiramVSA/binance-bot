"""
Order Service for Binance Futures Trading Bot.
Handles order creation, validation, and execution.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from src.api.client import BinanceFuturesClient, BinanceAPIError
from src.utils.validators import validate_order_input, ValidationError
from src.utils.logger import logger, log_order_submitted, log_order_result


@dataclass
class OrderRequest:
    """Order request data class."""
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str = "GTC"
    reduce_only: bool = False


@dataclass
class OrderResult:
    """Order result data class."""
    success: bool
    order_id: int | None = None
    client_order_id: str | None = None
    symbol: str | None = None
    status: str | None = None
    side: str | None = None
    order_type: str | None = None
    quantity: str | None = None
    price: str | None = None
    executed_qty: str | None = None
    avg_price: str | None = None
    message: str | None = None
    raw_response: dict[str, Any] | None = None
    error_code: int | None = None


class OrderService:
    """High-level interface for order management with input validation."""

    def __init__(self, client: BinanceFuturesClient | None = None):
        self.client = client or BinanceFuturesClient()
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: str,
        price: str | None = None,
        stop_price: str | None = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> OrderResult:
        """Validate inputs and place an order. Returns OrderResult (never raises)."""
        try:
            # Validate input
            (
                validated_symbol,
                validated_side,
                validated_type,
                validated_qty,
                validated_price,
                validated_stop_price
            ) = validate_order_input(symbol, side, order_type, quantity, price, stop_price)
            
            # Create order request
            order_request = OrderRequest(
                symbol=validated_symbol,
                side=validated_side,
                order_type=validated_type,
                quantity=validated_qty,
                price=validated_price,
                stop_price=validated_stop_price,
                time_in_force=time_in_force,
                reduce_only=reduce_only
            )
            
            log_order_submitted({
                "symbol": order_request.symbol,
                "side": order_request.side,
                "type": order_request.order_type,
                "quantity": str(order_request.quantity),
                "price": str(order_request.price) if order_request.price else None,
                "stop_price": str(order_request.stop_price) if order_request.stop_price else None,
            })
            
            # Execute order
            response = self.client.place_order(
                symbol=order_request.symbol,
                side=order_request.side,
                order_type=order_request.order_type,
                quantity=order_request.quantity,
                price=order_request.price,
                stop_price=order_request.stop_price,
                time_in_force=order_request.time_in_force,
                reduce_only=order_request.reduce_only
            )
            
            result = OrderResult(
                success=True,
                order_id=response.get("orderId"),
                client_order_id=response.get("clientOrderId"),
                symbol=response.get("symbol"),
                status=response.get("status"),
                side=response.get("side"),
                order_type=response.get("type"),
                quantity=response.get("origQty"),
                price=response.get("price"),
                executed_qty=response.get("executedQty"),
                avg_price=response.get("avgPrice"),
                message="Order placed successfully",
                raw_response=response
            )
            
            log_order_result(True, response)
            return result
            
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            result = OrderResult(
                success=False,
                message=f"Validation error: {str(e)}"
            )
            log_order_result(False, {"error": str(e)})
            return result
            
        except BinanceAPIError as e:
            logger.error(f"API error: {str(e)}")
            result = OrderResult(
                success=False,
                message=str(e),
                error_code=e.code,
                raw_response=e.response
            )
            log_order_result(False, {"error": str(e), "code": e.code})
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            result = OrderResult(
                success=False,
                message=f"Unexpected error: {str(e)}"
            )
            log_order_result(False, {"error": str(e)})
            return result
    
    def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        reduce_only: bool = False
    ) -> OrderResult:
        """Place a market order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="MARKET",
            quantity=quantity,
            reduce_only=reduce_only
        )
    
    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> OrderResult:
        """Place a limit order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="LIMIT",
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            reduce_only=reduce_only
        )
    
    def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        stop_price: str,
        reduce_only: bool = False
    ) -> OrderResult:
        """Place a stop-market order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="STOP_MARKET",
            quantity=quantity,
            stop_price=stop_price,
            reduce_only=reduce_only
        )
    
    def place_stop_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        price: str,
        stop_price: str,
        time_in_force: str = "GTC",
        reduce_only: bool = False
    ) -> OrderResult:
        """Place a stop-limit order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="STOP",
            quantity=quantity,
            price=price,
            stop_price=stop_price,
            time_in_force=time_in_force,
            reduce_only=reduce_only
        )
    
    def place_take_profit_market_order(
        self,
        symbol: str,
        side: str,
        quantity: str,
        stop_price: str,
        reduce_only: bool = False
    ) -> OrderResult:
        """Place a take-profit market order."""
        return self.place_order(
            symbol=symbol,
            side=side,
            order_type="TAKE_PROFIT_MARKET",
            quantity=quantity,
            stop_price=stop_price,
            reduce_only=reduce_only
        )
    
    def cancel_order(self, symbol: str, order_id: int) -> OrderResult:
        """Cancel an existing order by ID."""
        try:
            response = self.client.cancel_order(symbol=symbol, order_id=order_id)
            
            return OrderResult(
                success=True,
                order_id=response.get("orderId"),
                symbol=response.get("symbol"),
                status=response.get("status"),
                message="Order cancelled successfully",
                raw_response=response
            )
            
        except BinanceAPIError as e:
            logger.error(f"Cancel order error: {str(e)}")
            return OrderResult(
                success=False,
                message=str(e),
                error_code=e.code,
                raw_response=e.response
            )
    
    def get_open_orders(self, symbol: str | None = None) -> dict[str, Any]:
        """Get open orders, optionally filtered by symbol."""
        try:
            orders = self.client.get_open_orders(symbol)
            return {"success": True, "orders": orders}
        except BinanceAPIError as e:
            logger.error(f"Get open orders error: {str(e)}")
            return {"success": False, "error": str(e), "code": e.code}
    
    def get_positions(self, symbol: str | None = None) -> dict[str, Any]:
        """Get position information, optionally filtered by symbol."""
        try:
            positions = self.client.get_positions(symbol)
            return {"success": True, "positions": positions}
        except BinanceAPIError as e:
            logger.error(f"Get positions error: {str(e)}")
            return {"success": False, "error": str(e), "code": e.code}
