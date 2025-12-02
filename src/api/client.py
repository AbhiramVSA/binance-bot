"""
Binance Futures API Client.
Handles authentication, request signing, and API communication.
"""
import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import requests

from src.config.config import settings
from src.utils.logger import logger, log_api_request, log_api_response, log_api_error


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors."""
    
    def __init__(self, message: str, code: Optional[int] = None, response: Optional[dict] = None):
        super().__init__(message)
        self.code = code
        self.response = response


class BinanceFuturesClient:
    """
    Client for Binance Futures API (USDT-M).
    Supports both testnet and mainnet.
    """
    
    # API Endpoints
    ENDPOINTS = {
        "order": "/fapi/v1/order",
        "open_orders": "/fapi/v1/openOrders",
        "all_orders": "/fapi/v1/allOrders",
        "account": "/fapi/v2/account",
        "position": "/fapi/v2/positionRisk",
        "exchange_info": "/fapi/v1/exchangeInfo",
        "ticker_price": "/fapi/v1/ticker/price",
        "server_time": "/fapi/v1/time",
    }
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        use_testnet: Optional[bool] = None
    ):
        """
        Initialize the Binance Futures client.
        
        Args:
            api_key: Binance API key (defaults to settings)
            api_secret: Binance API secret (defaults to settings)
            use_testnet: Whether to use testnet (defaults to settings)
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.use_testnet = use_testnet if use_testnet is not None else settings.USE_TESTNET
        
        self.base_url = (
            settings.TESTNET_BASE_URL if self.use_testnet else settings.MAINNET_BASE_URL
        )
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-MBX-APIKEY": self.api_key,
            "Content-Type": "application/x-www-form-urlencoded"
        })
        
        logger.info(
            f"Initialized Binance Futures Client | "
            f"Testnet: {self.use_testnet} | "
            f"Base URL: {self.base_url}"
        )
    
    def _get_timestamp(self) -> int:
        """Get current timestamp in milliseconds."""
        return int(time.time() * 1000)
    
    def _sign_request(self, params: Dict[str, Any]) -> str:
        """
        Create HMAC SHA256 signature for request.
        
        Args:
            params: Request parameters
        
        Returns:
            Signature string
        """
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        signed: bool = False
    ) -> Dict[str, Any]:
        """
        Make HTTP request to Binance API.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint
            params: Request parameters
            signed: Whether request needs signature
        
        Returns:
            API response as dictionary
        
        Raises:
            BinanceAPIError: If API returns an error
        """
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._sign_request(params)
        
        log_api_request(method, url, params)
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params)
            elif method == "POST":
                response = self.session.post(url, data=params)
            elif method == "DELETE":
                response = self.session.delete(url, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            data = response.json()
            log_api_response(response.status_code, data)
            
            if response.status_code != 200:
                error_msg = data.get("msg", "Unknown error")
                error_code = data.get("code", -1)
                raise BinanceAPIError(
                    f"API Error {error_code}: {error_msg}",
                    code=error_code,
                    response=data
                )
            
            return data
            
        except requests.exceptions.ConnectionError as e:
            log_api_error(e, "Connection error")
            raise BinanceAPIError(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            log_api_error(e, "Request timeout")
            raise BinanceAPIError(f"Request timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            log_api_error(e, "Request failed")
            raise BinanceAPIError(f"Request failed: {str(e)}")
    
    # Public Endpoints (no signature required)
    
    def get_server_time(self) -> Dict[str, Any]:
        """Get Binance server time."""
        return self._make_request("GET", self.ENDPOINTS["server_time"])
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        return self._make_request("GET", self.ENDPOINTS["exchange_info"])
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get latest price for a symbol or all symbols.
        
        Args:
            symbol: Trading pair symbol (optional)
        
        Returns:
            Price information
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", self.ENDPOINTS["ticker_price"], params)
    
    # Private Endpoints (signature required)
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get account information including balances and positions."""
        return self._make_request("GET", self.ENDPOINTS["account"], signed=True)
    
    def get_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get position information.
        
        Args:
            symbol: Trading pair symbol (optional)
        
        Returns:
            Position information
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", self.ENDPOINTS["position"], params, signed=True)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all open orders.
        
        Args:
            symbol: Trading pair symbol (optional)
        
        Returns:
            List of open orders
        """
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", self.ENDPOINTS["open_orders"], params, signed=True)
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_position: bool = False,
        position_side: str = "BOTH",
        working_type: str = "CONTRACT_PRICE"
    ) -> Dict[str, Any]:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair symbol (e.g., BTCUSDT)
            side: Order side (BUY or SELL)
            order_type: Order type (MARKET, LIMIT, STOP, STOP_MARKET, etc.)
            quantity: Order quantity
            price: Order price (required for LIMIT orders)
            stop_price: Stop price (required for STOP orders)
            time_in_force: Time in force (GTC, IOC, FOK)
            reduce_only: Reduce only flag
            close_position: Close position flag
            position_side: Position side (BOTH, LONG, SHORT)
            working_type: Working type (MARK_PRICE, CONTRACT_PRICE)
        
        Returns:
            Order response from Binance API
        
        Raises:
            BinanceAPIError: If order placement fails
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": str(quantity),
            "positionSide": position_side,
        }
        
        # Add price for LIMIT orders
        if order_type == "LIMIT":
            if price is None:
                raise BinanceAPIError("Price is required for LIMIT orders")
            params["price"] = str(price)
            params["timeInForce"] = time_in_force
        
        # Add stop price for stop orders
        if order_type in ["STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]:
            if stop_price is None:
                raise BinanceAPIError(f"Stop price is required for {order_type} orders")
            params["stopPrice"] = str(stop_price)
            params["workingType"] = working_type
            
            # For STOP and TAKE_PROFIT, also need price
            if order_type in ["STOP", "TAKE_PROFIT"]:
                if price is None:
                    raise BinanceAPIError(f"Price is required for {order_type} orders")
                params["price"] = str(price)
                params["timeInForce"] = time_in_force
        
        if reduce_only:
            params["reduceOnly"] = "true"
        
        if close_position:
            params["closePosition"] = "true"
            # Remove quantity if close_position is true
            del params["quantity"]
        
        return self._make_request("POST", self.ENDPOINTS["order"], params, signed=True)
    
    def cancel_order(self, symbol: str, order_id: Optional[int] = None, client_order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading pair symbol
            order_id: Order ID (either order_id or client_order_id required)
            client_order_id: Client order ID
        
        Returns:
            Cancelled order details
        
        Raises:
            BinanceAPIError: If cancellation fails
        """
        if not order_id and not client_order_id:
            raise BinanceAPIError("Either order_id or client_order_id is required")
        
        params = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        
        return self._make_request("DELETE", self.ENDPOINTS["order"], params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        Cancel all open orders for a symbol.
        
        Args:
            symbol: Trading pair symbol
        
        Returns:
            Cancellation result
        """
        params = {"symbol": symbol}
        return self._make_request("DELETE", self.ENDPOINTS["open_orders"], params, signed=True)
