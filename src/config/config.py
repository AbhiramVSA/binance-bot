"""
Configuration module for Binance Futures Trading Bot.
Handles API credentials and environment settings.
"""
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    # Binance API credentials
    BINANCE_API_KEY: str = Field(default="", description="Binance API Key")
    BINANCE_API_SECRET: str = Field(default="", description="Binance API Secret")
    
    # Environment settings
    USE_TESTNET: bool = Field(default=True, description="Use Binance Testnet")
    
    # API URLs
    TESTNET_BASE_URL: str = Field(
        default="https://testnet.binancefuture.com",
        description="Binance Futures Testnet API URL"
    )
    MAINNET_BASE_URL: str = Field(
        default="https://fapi.binance.com",
        description="Binance Futures Mainnet API URL"
    )
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_TO_FILE: bool = Field(default=False, description="Log to file")
    LOG_FILE_PATH: str = Field(default="trading_bot.log", description="Log file path")
    
    @property
    def base_url(self) -> str:
        """Get the appropriate base URL based on testnet flag."""
        return self.TESTNET_BASE_URL if self.USE_TESTNET else self.MAINNET_BASE_URL
    
    def is_configured(self) -> bool:
        """Check if API credentials are configured."""
        return bool(self.BINANCE_API_KEY and self.BINANCE_API_SECRET)


settings = Settings()