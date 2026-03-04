"""Binance Futures API client with HMAC authentication and request signing."""
import hashlib
import hmac
import time
from decimal import Decimal
from typing import Any
from urllib.parse import urlencode

import requests

from src.config.config import settings
from src.utils.logger import logger, log_api_request, log_api_response, log_api_error


class BinanceAPIError(Exception):
    """Custom exception for Binance API errors."""
    
    def __init__(self, message: str, code: int | None = None, response: dict | None = None):
        super().__init__(message)
        self.code = code
        self.response = response


class BinanceFuturesClient:
    """
    Client for Binance Futures API (USDT-M).
    Supports both testnet and mainnet.
    """

    REQUEST_TIMEOUT = 10  # seconds

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
        api_key: str | None = None,
        api_secret: str | None = None,
        use_testnet: bool | None = None
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
    
    def _sign_request(self, params: dict[str, Any]) -> str:
        """Create HMAC SHA256 signature for the given request parameters."""
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
        params: dict[str, Any] | None = None,
        signed: bool = False
    ) -> dict[str, Any]:
        """Send a signed or unsigned request to the Binance API."""
        url = f"{self.base_url}{endpoint}"
        params = params or {}
        
        if signed:
            params["timestamp"] = self._get_timestamp()
            params["signature"] = self._sign_request(params)
        
        log_api_request(method, url, params)
        
        try:
            if method == "GET":
                response = self.session.get(url, params=params, timeout=self.REQUEST_TIMEOUT)
            elif method == "POST":
                response = self.session.post(url, data=params, timeout=self.REQUEST_TIMEOUT)
            elif method == "DELETE":
                response = self.session.delete(url, params=params, timeout=self.REQUEST_TIMEOUT)
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
    
    def get_server_time(self) -> dict[str, Any]:
        """Get Binance server time."""
        return self._make_request("GET", self.ENDPOINTS["server_time"])
    
    def get_exchange_info(self) -> dict[str, Any]:
        """Get exchange trading rules and symbol information."""
        return self._make_request("GET", self.ENDPOINTS["exchange_info"])
    
    def get_ticker_price(self, symbol: str | None = None) -> dict[str, Any]:
        """Get latest price for a symbol or all symbols."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", self.ENDPOINTS["ticker_price"], params)
    
    # Private Endpoints (signature required)
    
    def get_account_info(self) -> dict[str, Any]:
        """Get account information including balances and positions."""
        return self._make_request("GET", self.ENDPOINTS["account"], signed=True)
    
    def get_positions(self, symbol: str | None = None) -> dict[str, Any]:
        """Get position information, optionally filtered by symbol."""
        params = {}
        if symbol:
            params["symbol"] = symbol
        return self._make_request("GET", self.ENDPOINTS["position"], params, signed=True)
    
    def get_open_orders(self, symbol: str | None = None) -> dict[str, Any]:
        """Get all open orders, optionally filtered by symbol."""
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
        price: Decimal | None = None,
        stop_price: Decimal | None = None,
        time_in_force: str = "GTC",
        reduce_only: bool = False,
        close_position: bool = False,
        position_side: str = "BOTH",
        working_type: str = "CONTRACT_PRICE"
    ) -> dict[str, Any]:
        """Place a new futures order. Raises BinanceAPIError on failure."""
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
    
    def cancel_order(self, symbol: str, order_id: int | None = None, client_order_id: str | None = None) -> dict[str, Any]:
        """Cancel an order by order_id or client_order_id."""
        if not order_id and not client_order_id:
            raise BinanceAPIError("Either order_id or client_order_id is required")
        
        params = {"symbol": symbol}
        if order_id:
            params["orderId"] = order_id
        if client_order_id:
            params["origClientOrderId"] = client_order_id
        
        return self._make_request("DELETE", self.ENDPOINTS["order"], params, signed=True)
    
    def cancel_all_orders(self, symbol: str) -> dict[str, Any]:
        """Cancel all open orders for a symbol."""
        params = {"symbol": symbol}
        return self._make_request("DELETE", self.ENDPOINTS["open_orders"], params, signed=True)
