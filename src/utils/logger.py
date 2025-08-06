import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import config


def setup_logger() -> None:
    """Configure loguru logger based on configuration."""
    # Remove default logger
    logger.remove()
    
    # Get logging configuration
    log_config = config.logging_config
    level = log_config.get("level", "INFO")
    format_type = log_config.get("format", "text")
    
    # Define formats
    if format_type == "json":
        log_format = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message} | {extra}"
        serialize = True
    else:
        log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        serialize = False
    
    # Console handler
    console_config = log_config.get("handlers", {}).get("console", {})
    if console_config.get("enabled", True):
        logger.add(
            sys.stderr,
            format=log_format,
            level=console_config.get("level", level),
            serialize=serialize
        )
    
    # File handler
    file_config = log_config.get("handlers", {}).get("file", {})
    if file_config.get("enabled", True):
        log_path = Path(file_config.get("path", "./logs/digimon_kg.log"))
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_path,
            format=log_format,
            level=file_config.get("level", level),
            rotation=log_config.get("file_rotation", "1 day"),
            retention=log_config.get("retention", "7 days"),
            serialize=serialize,
            compression="zip"
        )
    
    logger.info("Logger initialized")


def get_logger(name: Optional[str] = None) -> logger:
    """Get a logger instance with optional name binding."""
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logger on import
setup_logger()