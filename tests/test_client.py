"""Tests for BinanceFuturesClient (unit tests, no network calls)."""
import hashlib
import hmac
from decimal import Decimal
from unittest.mock import MagicMock, patch
from urllib.parse import urlencode

import pytest

from src.api.client import BinanceFuturesClient, BinanceAPIError


@pytest.fixture
def client():
    """Create a client with test credentials."""
    return BinanceFuturesClient(
        api_key="test_key",
        api_secret="test_secret",
        use_testnet=True
    )


class TestClientInit:
    def test_testnet_url(self, client):
        assert "testnet" in client.base_url

    def test_mainnet_url(self):
        c = BinanceFuturesClient(api_key="k", api_secret="s", use_testnet=False)
        assert "fapi.binance.com" in c.base_url

    def test_api_key_in_headers(self, client):
        assert client.session.headers["X-MBX-APIKEY"] == "test_key"


class TestSigning:
    def test_signature_is_valid_hmac(self, client):
        params = {"symbol": "BTCUSDT", "side": "BUY", "timestamp": 1234567890}
        sig = client._sign_request(params)

        expected = hmac.new(
            b"test_secret",
            urlencode(params).encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        assert sig == expected


class TestPlaceOrder:
    def test_limit_order_params(self, client):
        """Verify that place_order builds correct params for a LIMIT order."""
        with patch.object(client, "_make_request", return_value={"orderId": 1}) as mock:
            client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity=Decimal("0.001"),
                price=Decimal("50000"),
            )

            call_args = mock.call_args
            params = call_args[1].get("params") or call_args[0][2]
            assert params["symbol"] == "BTCUSDT"
            assert params["type"] == "LIMIT"
            assert params["price"] == "50000"
            assert params["timeInForce"] == "GTC"

    def test_market_order_no_price(self, client):
        """Market orders should not include price or timeInForce."""
        with patch.object(client, "_make_request", return_value={"orderId": 1}) as mock:
            client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="MARKET",
                quantity=Decimal("0.001"),
            )

            params = mock.call_args[0][2]
            assert "price" not in params
            assert "timeInForce" not in params

    def test_stop_market_requires_stop_price(self, client):
        with pytest.raises(BinanceAPIError, match="Stop price is required"):
            client.place_order(
                symbol="BTCUSDT",
                side="SELL",
                order_type="STOP_MARKET",
                quantity=Decimal("0.001"),
            )

    def test_limit_requires_price(self, client):
        with pytest.raises(BinanceAPIError, match="Price is required"):
            client.place_order(
                symbol="BTCUSDT",
                side="BUY",
                order_type="LIMIT",
                quantity=Decimal("0.001"),
            )

    def test_reduce_only(self, client):
        with patch.object(client, "_make_request", return_value={}) as mock:
            client.place_order(
                symbol="BTCUSDT",
                side="SELL",
                order_type="MARKET",
                quantity=Decimal("0.001"),
                reduce_only=True,
            )
            params = mock.call_args[0][2]
            assert params["reduceOnly"] == "true"

    def test_close_position_removes_quantity(self, client):
        with patch.object(client, "_make_request", return_value={}) as mock:
            client.place_order(
                symbol="BTCUSDT",
                side="SELL",
                order_type="MARKET",
                quantity=Decimal("0.001"),
                close_position=True,
            )
            params = mock.call_args[0][2]
            assert "quantity" not in params
            assert params["closePosition"] == "true"
