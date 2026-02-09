"""
Centralized logging configuration for Thrryv
Provides structured logging with different levels and handlers
"""
import logging
import sys
from datetime import datetime
from pathlib import Path
import json


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for better parsing and analysis"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id
        if hasattr(record, 'claim_id'):
            log_data["claim_id"] = record.claim_id
        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Add colors to console logs for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging(log_dir: Path = None, log_level: str = "INFO"):
    """
    Setup logging configuration
    
    Args:
        log_dir: Directory to store log files (optional)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with JSON format (if log_dir provided)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Application log
        app_log_file = log_dir / f"thrryv_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(app_log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        json_formatter = JSONFormatter()
        file_handler.setFormatter(json_formatter)
        root_logger.addHandler(file_handler)
        
        # Error log (separate file for errors only)
        error_log_file = log_dir / f"thrryv_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(json_formatter)
        root_logger.addHandler(error_handler)
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('motor').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(name)


# Context manager for request logging
class RequestLogger:
    """Add request context to logs"""
    
    def __init__(self, logger: logging.Logger, request_id: str, user_id: str = None):
        self.logger = logger
        self.request_id = request_id
        self.user_id = user_id
    
    def debug(self, message: str, **kwargs):
        extra = {'request_id': self.request_id}
        if self.user_id:
            extra['user_id'] = self.user_id
        extra.update(kwargs)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        extra = {'request_id': self.request_id}
        if self.user_id:
            extra['user_id'] = self.user_id
        extra.update(kwargs)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, **kwargs):
        extra = {'request_id': self.request_id}
        if self.user_id:
            extra['user_id'] = self.user_id
        extra.update(kwargs)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, **kwargs):
        extra = {'request_id': self.request_id}
        if self.user_id:
            extra['user_id'] = self.user_id
        extra.update(kwargs)
        self.logger.error(message, extra=extra)
