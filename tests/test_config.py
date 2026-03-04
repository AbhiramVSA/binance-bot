"""Tests for configuration module."""
from src.config.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings(BINANCE_API_KEY="", BINANCE_API_SECRET="")
        assert s.USE_TESTNET is True
        assert s.LOG_LEVEL == "INFO"
        assert s.LOG_TO_FILE is False

    def test_is_configured_false_when_empty(self):
        s = Settings(BINANCE_API_KEY="", BINANCE_API_SECRET="")
        assert s.is_configured() is False

    def test_is_configured_true(self):
        s = Settings(BINANCE_API_KEY="key", BINANCE_API_SECRET="secret")
        assert s.is_configured() is True

    def test_base_url_testnet(self):
        s = Settings(BINANCE_API_KEY="", BINANCE_API_SECRET="", USE_TESTNET=True)
        assert "testnet" in s.base_url

    def test_base_url_mainnet(self):
        s = Settings(BINANCE_API_KEY="", BINANCE_API_SECRET="", USE_TESTNET=False)
        assert "fapi.binance.com" in s.base_url
