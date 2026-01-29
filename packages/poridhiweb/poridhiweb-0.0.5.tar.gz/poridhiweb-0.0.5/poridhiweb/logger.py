import logging
import sys
from pathlib import Path
from typing import Optional


class Logger:
    """
    Logger class with standard formatting for the web framework
    """

    # Color codes for terminal output
    COLORS = {
        'DEBUG': '\033[36m',  # Cyan
        'INFO': '\033[32m',  # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',  # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m',  # Reset
    }

    def __init__(
        self,
        name: str = 'PoridhiFrame',
        level: int = logging.INFO,
        log_file: Optional[str] = None,
        use_colors: bool = True,
        format_string: str = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    ):
        """
        Initialize logger with standard configuration

        Args:
            name: Logger name
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path to write logs
            use_colors: Enable colored output for console
            format_string: Custom format string (uses default if None)
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.use_colors = use_colors

        # Prevent duplicate handlers
        if self.logger.handlers:
            self.logger.handlers.clear()

        self.format_string = format_string
        self.date_format = '%Y-%m-%d %H:%M:%S'

        # Add console handler
        self._add_console_handler()

        # Add file handler if specified
        if log_file:
            self._add_file_handler(log_file)

    def _add_console_handler(self):
        """Add console handler with optional colors"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.logger.level)

        if self.use_colors:
            formatter = self.ColoredFormatter(
                self.format_string,
                datefmt=self.date_format
            )
        else:
            formatter = logging.Formatter(
                self.format_string,
                datefmt=self.date_format
            )

        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

    def _add_file_handler(self, log_file: str):
        """Add file handler for persistent logging"""
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(self.logger.level)

        # File logs don't use colors
        formatter = logging.Formatter(
            self.format_string,
            datefmt=self.date_format
        )

        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    class ColoredFormatter(logging.Formatter):
        """Custom formatter that adds colors to log levels"""

        def format(self, record):
            levelname = record.levelname
            if levelname in Logger.COLORS:
                record.levelname = (
                    f"{Logger.COLORS[levelname]}{levelname}"
                    f"{Logger.COLORS['RESET']}"
                )
            return super().format(record)

    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)

    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)

    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)

    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)

    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)

    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)

    def set_level(self, level: int):
        """Change logging level dynamically"""
        self.logger.setLevel(level)
        for handler in self.logger.handlers:
            handler.setLevel(level)


# Convenience function to create a logger
def create_logger(
    name: str = 'PoridhiFrame',
    level: str = 'INFO',
    log_file: Optional[str] = None,
    use_colors: bool = True
) -> Logger:
    """
    Create a logger instance with string level names

    Args:
        name: Logger name
        level: Log level as string ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_file: Optional file path for logging
        use_colors: Enable colored console output

    Returns:
        Logger instance
    """
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL,
    }

    log_level = level_map.get(level.upper(), logging.INFO)

    return Logger(
        name=name,
        level=log_level,
        log_file=log_file,
        use_colors=use_colors
    )
