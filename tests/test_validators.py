"""Tests for input validation functions."""
from decimal import Decimal

import pytest

from src.utils.validators import (
    ValidationError,
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    validate_stop_price,
    validate_order_input,
)


class TestValidateSymbol:
    def test_valid_symbol(self):
        assert validate_symbol("BTCUSDT") == "BTCUSDT"

    def test_lowercase_normalized(self):
        assert validate_symbol("ethusdt") == "ETHUSDT"

    def test_strips_whitespace(self):
        assert validate_symbol("  BTCUSDT  ") == "BTCUSDT"

    def test_busd_suffix(self):
        assert validate_symbol("BTCBUSD") == "BTCBUSD"

    def test_usd_suffix(self):
        assert validate_symbol("BTCUSD") == "BTCUSD"

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="required"):
            validate_symbol("")

    def test_too_short_raises(self):
        with pytest.raises(ValidationError, match="Invalid symbol"):
            validate_symbol("BTC")

    def test_wrong_suffix_raises(self):
        with pytest.raises(ValidationError, match="should end with"):
            validate_symbol("BTCETH")


class TestValidateSide:
    def test_buy(self):
        assert validate_side("BUY") == "BUY"

    def test_sell_lowercase(self):
        assert validate_side("sell") == "SELL"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="Invalid side"):
            validate_side("HOLD")

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="required"):
            validate_side("")


class TestValidateOrderType:
    def test_market(self):
        assert validate_order_type("MARKET") == "MARKET"

    def test_all_types(self):
        for ot in ["MARKET", "LIMIT", "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"]:
            assert validate_order_type(ot) == ot

    def test_lowercase(self):
        assert validate_order_type("limit") == "LIMIT"

    def test_invalid_raises(self):
        with pytest.raises(ValidationError, match="Invalid order type"):
            validate_order_type("FOK")


class TestValidateQuantity:
    def test_valid(self):
        assert validate_quantity("0.001") == Decimal("0.001")

    def test_integer_string(self):
        assert validate_quantity("5") == Decimal("5")

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_quantity("0")

    def test_negative_raises(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_quantity("-1")

    def test_empty_raises(self):
        with pytest.raises(ValidationError, match="required"):
            validate_quantity("")

    def test_non_numeric_raises(self):
        with pytest.raises(ValidationError, match="Invalid quantity"):
            validate_quantity("abc")


class TestValidatePrice:
    def test_required_for_limit(self):
        assert validate_price("100.5", "LIMIT") == Decimal("100.5")

    def test_missing_for_limit_raises(self):
        with pytest.raises(ValidationError, match="required for LIMIT"):
            validate_price(None, "LIMIT")

    def test_required_for_stop(self):
        assert validate_price("200", "STOP") == Decimal("200")

    def test_required_for_take_profit(self):
        assert validate_price("300", "TAKE_PROFIT") == Decimal("300")

    def test_optional_for_market(self):
        assert validate_price(None, "MARKET") is None

    def test_provided_for_market_validated(self):
        assert validate_price("100", "MARKET") == Decimal("100")

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="Invalid price"):
            validate_price("abc", "LIMIT")

    def test_zero_raises(self):
        with pytest.raises(ValidationError, match="greater than 0"):
            validate_price("0", "LIMIT")


class TestValidateStopPrice:
    def test_required_for_stop(self):
        assert validate_stop_price("90000", "STOP") == Decimal("90000")

    def test_required_for_stop_market(self):
        assert validate_stop_price("90000", "STOP_MARKET") == Decimal("90000")

    def test_required_for_take_profit(self):
        assert validate_stop_price("100000", "TAKE_PROFIT") == Decimal("100000")

    def test_required_for_take_profit_market(self):
        assert validate_stop_price("100000", "TAKE_PROFIT_MARKET") == Decimal("100000")

    def test_missing_for_stop_raises(self):
        with pytest.raises(ValidationError, match="required for STOP"):
            validate_stop_price(None, "STOP")

    def test_not_required_for_market(self):
        assert validate_stop_price(None, "MARKET") is None

    def test_not_required_for_limit(self):
        assert validate_stop_price(None, "LIMIT") is None


class TestValidateOrderInput:
    def test_market_order(self):
        result = validate_order_input("BTCUSDT", "BUY", "MARKET", "0.001")
        symbol, side, otype, qty, price, stop_price = result
        assert symbol == "BTCUSDT"
        assert side == "BUY"
        assert otype == "MARKET"
        assert qty == Decimal("0.001")
        assert price is None
        assert stop_price is None

    def test_limit_order(self):
        result = validate_order_input("ETHUSDT", "SELL", "LIMIT", "0.5", price="2000")
        _, _, _, _, price, _ = result
        assert price == Decimal("2000")

    def test_stop_order(self):
        result = validate_order_input(
            "BTCUSDT", "SELL", "STOP", "0.001",
            price="89000", stop_price="90000"
        )
        _, _, _, _, price, stop_price = result
        assert price == Decimal("89000")
        assert stop_price == Decimal("90000")

    def test_invalid_symbol_raises(self):
        with pytest.raises(ValidationError):
            validate_order_input("X", "BUY", "MARKET", "1")

    def test_missing_stop_price_raises(self):
        with pytest.raises(ValidationError, match="Stop price is required"):
            validate_order_input("BTCUSDT", "BUY", "STOP_MARKET", "0.001")
