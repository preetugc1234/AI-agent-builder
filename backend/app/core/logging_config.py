"""
Logging Configuration
Centralized logging setup with structured logging support
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict
from pathlib import Path


# Log Levels
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    Outputs logs in JSON format for better parsing and analysis
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""

        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add request context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        # Add file and line number for debugging
        if record.levelno >= logging.WARNING:
            log_data["file"] = record.pathname
            log_data["line"] = record.lineno
            log_data["function"] = record.funcName

        return json.dumps(log_data, default=str)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for better readability during development
    """

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",  # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")

        # Format message
        levelname = f"{color}{record.levelname:8}{reset}"
        message = f"{color}{record.getMessage()}{reset}"

        # Build log line
        log_line = f"{timestamp} | {levelname} | {record.name:30} | {message}"

        # Add exception info if present
        if record.exc_info:
            log_line += f"\n{self.formatException(record.exc_info)}"

        return log_line


def setup_logging(
    level: str = "INFO",
    log_file: str = None,
    json_logs: bool = False,
    colored_console: bool = True
) -> None:
    """
    Setup application-wide logging configuration

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (optional)
        json_logs: Use JSON structured logging
        colored_console: Use colored output for console (ignored if json_logs=True)
    """

    # Get log level
    log_level = LOG_LEVELS.get(level.upper(), logging.INFO)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)

    if json_logs:
        # Use JSON formatter for production
        console_formatter = StructuredFormatter()
    elif colored_console and sys.stdout.isatty():
        # Use colored formatter for development (only if terminal supports it)
        console_formatter = ColoredFormatter()
    else:
        # Use standard formatter
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(log_level)

        # Always use JSON formatter for file logs
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

    # Log startup message
    root_logger.info(
        f"Logging configured: level={level}, json_logs={json_logs}, log_file={log_file}"
    )


class Logger:
    """
    Enhanced logger with structured logging support
    Provides context-aware logging with automatic field injection
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}

    def bind(self, **kwargs) -> "Logger":
        """
        Bind context to logger for automatic field injection

        Usage:
            logger = Logger(__name__)
            request_logger = logger.bind(request_id="123", user_id="456")
            request_logger.info("User action")  # Includes request_id and user_id
        """
        new_logger = Logger(self.logger.name)
        new_logger.context = {**self.context, **kwargs}
        return new_logger

    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with context injection"""
        extra_data = {**self.context, **kwargs}

        # Create extra dict for logging
        extra = {}
        if extra_data:
            extra["extra_data"] = extra_data

        # Add context fields as record attributes
        for key, value in extra_data.items():
            extra[key] = value

        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={"extra_data": {**self.context, **kwargs}})


def get_logger(name: str) -> Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance with structured logging support
    """
    return Logger(name)
