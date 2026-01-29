import sys
from pathlib import Path
from typing import Callable, Literal, Optional

from loguru import logger

LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


LOG_LEVELS = {
    "TRACE": 5,
    "DEBUG": 10,
    "INFO": 20,
    "SUCCESS": 25,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "SECTION": 35,
    "TITLE": 45,
}


def _create_custom_formatter() -> Callable:
    """Create a formatter with proper tag nesting for loguru colorization."""

    def formatter(record: dict) -> str:
        level_name = record["level"].name
        time_str = "<green>{time:HH:mm:ss}</green>"

        if level_name == "TITLE":
            return f"{time_str}\n<cyan><bold>=== {{message}} ===</bold></cyan>\n{{exception}}"

        if level_name == "SECTION":
            separator = "=" * 70
            return (
                f"<cyan>{separator}</cyan>\n"
                f"{time_str} | <cyan><bold>{{message}}</bold></cyan>\n"
                f"<cyan>{separator}</cyan>\n"
                "{exception}"
            )

        level_format = "<bold><level>{level: <8}</level></bold>"
        message_format = "<level>{message}</level>"

        return f"{time_str} | {level_format} | {message_format}\n{{exception}}"

    return formatter


def setup_logging(
    verbose: bool = True,
    level: LogLevel = "INFO",
    log_file: Optional[str | Path] = None,
) -> None:
    """
    Configure logging with professional formatting and enhanced INFO visibility.

    Args:
        verbose: Enable verbose console output with formatting
        level: Minimum log level to display on console
        log_file: Optional file path for logging all messages
    """
    logger.remove()

    # Register custom log levels
    for level_name, level_no in LOG_LEVELS.items():
        try:
            logger.level(level_name, no=level_no)
        except ValueError:
            pass

    # Console handler with formatting
    if verbose:
        logger.add(
            sys.stderr,
            format=_create_custom_formatter(),
            level=level,
            colorize=True,
            backtrace=True,
            diagnose=False,
        )
    else:
        logger.add(
            sys.stderr,
            format="{time:HH:mm:ss} | {level: <8} | {message}",
            level="WARNING",
            colorize=True,
        )

    # File handler for persistent logging
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.add(
            str(log_file),
            format=_create_custom_formatter(),
            level="DEBUG",
            rotation="10 MB",
        )
