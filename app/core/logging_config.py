# app/core/logging_config.py

"""
Logging configuration for the application.
Provides structured logging with appropriate levels and formatting.
"""

import logging
import sys
from typing import Optional
from app.core.config import settings


# ==================== Logging Configuration ====================

def setup_logging(
    level: Optional[str] = None,
    log_format: Optional[str] = None
) -> None:
    """
    Configure application-wide logging.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
    """
    # Determine log level from settings or parameter
    log_level = level or getattr(settings, 'LOG_LEVEL', 'INFO')
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Default format
    if log_format is None:
        log_format = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(filename)s:%(lineno)d - %(message)s'
        )
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set third-party library log levels
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# ==================== Logger Instances ====================

# Service loggers
service_logger = get_logger('app.services')
user_service_logger = get_logger('app.services.user')
profile_service_logger = get_logger('app.services.profile')
matcher_logger = get_logger('app.services.matcher')
calculator_logger = get_logger('app.services.calculator')

# Repository loggers
repository_logger = get_logger('app.repositories')
user_repo_logger = get_logger('app.repositories.user')
profile_repo_logger = get_logger('app.repositories.profile')

# API loggers
api_logger = get_logger('app.api')
user_api_logger = get_logger('app.api.user')
profile_api_logger = get_logger('app.api.profile')

# Core loggers
core_logger = get_logger('app.core')
db_logger = get_logger('app.core.database')
auth_logger = get_logger('app.core.auth')
