"""
Structured logging configuration for FaultScope.

Provides consistent logging across the application with structured output
for easier parsing and analysis.
"""

import logging
import sys
from typing import Any, Dict
from app.core.config import get_settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured log messages.
    
    For production, this could be enhanced to output JSON format
    for integration with log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with structured fields"""
        
        # Base message
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        # Format as key=value pairs for readability
        parts = [f"{k}={v}" for k, v in log_data.items()]
        return " | ".join(parts)


def setup_logging() -> None:
    """
    Configure application-wide logging.
    
    Sets up console handler with structured formatting and appropriate log level.
    """
    settings = get_settings()
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Set formatter
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger.addHandler(console_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the specified module.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        logging.Logger: Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds extra contextual fields to log messages.
    
    Example:
        logger = LoggerAdapter(logging.getLogger(__name__), {"service_id": "xyz"})
        logger.info("Processing telemetry")  # Will include service_id in output
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra fields to log record"""
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        kwargs["extra"]["extra_fields"] = self.extra
        return msg, kwargs
