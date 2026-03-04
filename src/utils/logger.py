"""
Logging utility for Binance Futures Trading Bot.
Provides centralized logging configuration and functions.
"""
import logging
import sys

from src.config.config import settings


def setup_logger(
    name: str = "binance_bot",
    level: str | None = None,
    log_to_file: bool | None = None,
    log_file_path: str | None = None
) -> logging.Logger:
    """
    Set up and configure a logger instance.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_file_path: Path to log file
    
    Returns:
        Configured logger instance
    """
    level = level or settings.LOG_LEVEL
    log_to_file = log_to_file if log_to_file is not None else settings.LOG_TO_FILE
    log_file_path = log_file_path or settings.LOG_FILE_PATH
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_to_file:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logger()


def log_api_request(method: str, url: str, params: dict | None = None) -> None:
    """Log an API request."""
    params_str = f" | Params: {_sanitize_params(params)}" if params else ""
    logger.info(f"API Request: {method} {url}{params_str}")


def log_api_response(status_code: int, response_data: dict) -> None:
    """Log an API response."""
    logger.info(f"API Response: Status {status_code} | Data: {response_data}")


def log_api_error(error: Exception, context: str | None = None) -> None:
    """Log an API error."""
    context_str = f" | Context: {context}" if context else ""
    logger.error(f"API Error: {type(error).__name__}: {str(error)}{context_str}")


def log_order_submitted(order_details: dict) -> None:
    """Log order submission details."""
    logger.info(f"Order Submitted: {order_details}")


def log_order_result(success: bool, result: dict) -> None:
    """Log order execution result."""
    if success:
        logger.info(f"Order Success: {result}")
    else:
        logger.error(f"Order Failed: {result}")


def _sanitize_params(params: dict | None) -> dict:
    """Sanitize parameters by hiding sensitive data."""
    if not params:
        return {}
    
    sanitized = params.copy()
    sensitive_keys = ["signature", "api_key", "apiKey", "secret"]
    
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "***HIDDEN***"
    
    return sanitized
