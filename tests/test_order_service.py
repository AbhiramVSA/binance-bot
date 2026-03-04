"""Tests for OrderService (mocked API client, no network calls)."""
from unittest.mock import MagicMock, patch

import pytest

from src.api.client import BinanceAPIError
from src.controllers.order_service import OrderService, OrderResult


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def service(mock_client):
    return OrderService(client=mock_client)


class TestPlaceOrder:
    def test_successful_market_order(self, service, mock_client):
        mock_client.place_order.return_value = {
            "orderId": 12345,
            "clientOrderId": "abc",
            "symbol": "BTCUSDT",
            "status": "FILLED",
            "side": "BUY",
            "type": "MARKET",
            "origQty": "0.001",
            "price": "0",
            "executedQty": "0.001",
            "avgPrice": "50000",
        }

        result = service.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
        )

        assert result.success is True
        assert result.order_id == 12345
        assert result.symbol == "BTCUSDT"

    def test_validation_error_returns_failed_result(self, service):
        result = service.place_order(
            symbol="X",  # too short
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
        )

        assert result.success is False
        assert "Validation error" in result.message

    def test_api_error_returns_failed_result(self, service, mock_client):
        mock_client.place_order.side_effect = BinanceAPIError(
            "Insufficient balance", code=-2019
        )

        result = service.place_order(
            symbol="BTCUSDT",
            side="BUY",
            order_type="MARKET",
            quantity="0.001",
        )

        assert result.success is False
        assert result.error_code == -2019


class TestCancelOrder:
    def test_successful_cancel(self, service, mock_client):
        mock_client.cancel_order.return_value = {
            "orderId": 99,
            "symbol": "BTCUSDT",
            "status": "CANCELED",
        }

        result = service.cancel_order("BTCUSDT", 99)

        assert result.success is True
        assert result.order_id == 99

    def test_cancel_api_error(self, service, mock_client):
        mock_client.cancel_order.side_effect = BinanceAPIError(
            "Order not found", code=-2011
        )

        result = service.cancel_order("BTCUSDT", 999)

        assert result.success is False
        assert result.error_code == -2011


class TestGetOpenOrders:
    def test_success(self, service, mock_client):
        mock_client.get_open_orders.return_value = [{"orderId": 1}]
        result = service.get_open_orders("BTCUSDT")
        assert result["success"] is True
        assert len(result["orders"]) == 1

    def test_api_error(self, service, mock_client):
        mock_client.get_open_orders.side_effect = BinanceAPIError("fail", code=-1)
        result = service.get_open_orders("BTCUSDT")
        assert result["success"] is False


class TestGetPositions:
    def test_success(self, service, mock_client):
        mock_client.get_positions.return_value = [{"symbol": "BTCUSDT"}]
        result = service.get_positions("BTCUSDT")
        assert result["success"] is True
        assert len(result["positions"]) == 1
