"""
Logging system for the engine.
"""
import sys
from typing import Optional
from enum import Enum
from datetime import datetime


class LogLevel(Enum):
    """Log levels."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class Logger:
    """Logger for engine messages."""
    
    def __init__(self, name: str = "Core", level: LogLevel = LogLevel.INFO):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            level: Minimum log level
        """
        self.name = name
        self.level = level
        self._handlers = []
        self._enable_colors = sys.stdout.isatty()
    
    def set_level(self, level: LogLevel):
        """Set minimum log level."""
        self.level = level
    
    def _should_log(self, level: LogLevel) -> bool:
        """Check if message should be logged."""
        return level.value >= self.level.value
    
    def _format_message(self, level: LogLevel, message: str) -> str:
        """Format log message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_name = level.name
        return f"[{timestamp}] [{level_name}] [{self.name}] {message}"
    
    def _log(self, level: LogLevel, message: str, *args, **kwargs):
        """Internal log method."""
        if not self._should_log(level):
            return
        
        formatted = self._format_message(level, message)
        if args or kwargs:
            formatted = formatted.format(*args, **kwargs)
        
        # Print to console
        output = sys.stdout if level.value < LogLevel.ERROR else sys.stderr
        
        if self._enable_colors:
            colors = {
                LogLevel.DEBUG: '\033[36m',    # Cyan
                LogLevel.INFO: '\033[32m',     # Green
                LogLevel.WARNING: '\033[33m',  # Yellow
                LogLevel.ERROR: '\033[31m',    # Red
                LogLevel.CRITICAL: '\033[35m', # Magenta
            }
            reset = '\033[0m'
            formatted = f"{colors.get(level, '')}{formatted}{reset}"
        
        print(formatted, file=output)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message."""
        self._log(LogLevel.DEBUG, message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message."""
        self._log(LogLevel.INFO, message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message."""
        self._log(LogLevel.WARNING, message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message."""
        self._log(LogLevel.ERROR, message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message."""
        self._log(LogLevel.CRITICAL, message, *args, **kwargs)


# Global logger instance
_logger_instance: Optional[Logger] = None


def get_logger() -> Logger:
    """Get global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = Logger()
    return _logger_instance


# Convenience functions
def debug(message: str, *args, **kwargs):
    """Log debug message."""
    get_logger().debug(message, *args, **kwargs)


def info(message: str, *args, **kwargs):
    """Log info message."""
    get_logger().info(message, *args, **kwargs)


def warning(message: str, *args, **kwargs):
    """Log warning message."""
    get_logger().warning(message, *args, **kwargs)


def error(message: str, *args, **kwargs):
    """Log error message."""
    get_logger().error(message, *args, **kwargs)


def critical(message: str, *args, **kwargs):
    """Log critical message."""
    get_logger().critical(message, *args, **kwargs)

