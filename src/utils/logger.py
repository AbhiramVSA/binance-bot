"""Centralized logging configuration and API log helpers."""
import logging
import sys

from src.config.config import settings

_SENSITIVE_KEYS = frozenset(["signature", "api_key", "apiKey", "secret"])


def setup_logger(
    name: str = "binance_bot",
    level: str | None = None,
    log_to_file: bool | None = None,
    log_file_path: str | None = None
) -> logging.Logger:
    """Create and configure a logger with console and optional file output."""
    level = level or settings.LOG_LEVEL
    log_to_file = log_to_file if log_to_file is not None else settings.LOG_TO_FILE
    log_file_path = log_file_path or settings.LOG_FILE_PATH

    _logger = logging.getLogger(name)
    _logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    _logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)

    if log_to_file:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)

    return _logger


logger = setup_logger()


def _sanitize_params(params: dict | None) -> dict:
    """Return a copy of params with sensitive values masked."""
    if not params:
        return {}

    sanitized = params.copy()
    for key in _SENSITIVE_KEYS:
        if key in sanitized:
            sanitized[key] = "***HIDDEN***"
    return sanitized


def log_api_request(method: str, url: str, params: dict | None = None) -> None:
    """Log an outgoing API request (params are sanitized)."""
    params_str = f" | Params: {_sanitize_params(params)}" if params else ""
    logger.info(f"API Request: {method} {url}{params_str}")


def log_api_response(status_code: int, response_data: dict) -> None:
    """Log API response status at INFO, full body at DEBUG."""
    logger.info(f"API Response: Status {status_code}")
    logger.debug(f"API Response Body: {response_data}")


def log_api_error(error: Exception, context: str | None = None) -> None:
    """Log an API error with optional context."""
    context_str = f" | {context}" if context else ""
    logger.error(f"API Error: {type(error).__name__}: {error}{context_str}")


def log_order_submitted(order_details: dict) -> None:
    """Log order submission."""
    logger.info(f"Order Submitted: {order_details}")


def log_order_result(success: bool, result: dict) -> None:
    """Log order result (info on success, error on failure)."""
    if success:
        logger.info(f"Order Success: {result}")
    else:
        logger.error(f"Order Failed: {result}")
