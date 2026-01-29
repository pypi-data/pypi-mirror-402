import argparse
import logging as stdlogging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import NamedTuple
from colorama import init, Fore, Back, Style
try:
    from colorama import init

    init()  # Initialize colorama for Windows compatibility
except ImportError:
    pass

from cxppython.core.config import Config
from cxppython.utils.cxplogging.console import BittensorConsole
from .defines import (
    BITTENSOR_LOGGER_NAME,
    DATE_FORMAT,
    DEFAULT_LOG_BACKUP_COUNT,
    DEFAULT_LOG_FILE_NAME,
    DEFAULT_MAX_ROTATING_LOG_FILE_SIZE,
    TRACE_LOG_FORMAT,
)
from .format import BtFileFormatter, BtStreamFormatter

# Define custom log levels
TRACE_LEVEL = 5  # Below DEBUG (10)
SUCCESS_LEVEL = 25  # Between INFO (20) and WARNING (30)
stdlogging.addLevelName(TRACE_LEVEL, "TRACE")
stdlogging.addLevelName(SUCCESS_LEVEL, "SUCCESS")


# Add custom logging methods
def trace(self, message, *args, **kwargs):
    self.log(TRACE_LEVEL, message, *args, **kwargs)


def success(self, message, *args, **kwargs):
    self.log(SUCCESS_LEVEL, message, *args, **kwargs)


stdlogging.Logger.trace = trace
stdlogging.Logger.success = success

# Handle Python 3.11+ stacklevel for custom logging methods
CUSTOM_LOGGER_METHOD_STACK_LEVEL = 2 if sys.version_info >= (3, 11) else 1


def _concat_message(msg="", prefix="", suffix=""):
    """Concatenates a message with optional prefix and suffix."""
    message_parts = [
        str(component).strip()
        for component in [prefix, msg, suffix]
        if component is not None and str(component).strip()
    ]
    return " - ".join(message_parts)


class LoggingConfig(NamedTuple):
    """Named tuple to hold the logging configuration."""
    debug: bool
    trace: bool
    info: bool
    record_log: bool
    logging_dir: str


class CustomBtStreamFormatter(BtStreamFormatter):
    """Custom formatter to ensure TRACE and SUCCESS levels are displayed correctly with colors."""

    def format(self, record):
        # Set level name for custom levels
        if record.levelno == TRACE_LEVEL:
            record.levelname = "TRACE"
        elif record.levelno == SUCCESS_LEVEL:
            record.levelname = f"{record.levelname:^16}"
            record.levelname = f"{Fore.GREEN}{record.levelname}{Fore.GREEN}"  # Green level name
        # Ensure level name is padded to 16 characters
        record.levelname = f"{record.levelname:^16}"
        return super().format(record)


class LoggingSimple:
    """Simplified logging framework for Bittensor, without state machine or queue."""

    def __init__(self, config: "Config", name: str = None):
        # Use unique logger name with last two digits of id
        self._id_suffix = str(id(self))[-2:]
        self._name = name or f"{BITTENSOR_LOGGER_NAME}_{self._id_suffix}"
        self._config = self._extract_logging_config(config)
        self._logger = stdlogging.getLogger(self._name)

        # Initialize formatters
        self._stream_formatter = CustomBtStreamFormatter()
        self._file_formatter = BtFileFormatter(TRACE_LOG_FORMAT, DATE_FORMAT)

        # Configure handlers
        self._handlers = self._configure_handlers(self._config)
        for handler in self._handlers:
            self._logger.addHandler(handler)

        # Set initial log level
        self._set_initial_level(self._config)

        # Initialize console
        self.console = BittensorConsole(self)

    def _extract_logging_config(self, config: "Config") -> LoggingConfig:
        """Extract logging configuration from Bittensor config."""
        if getattr(config, "logging", None):
            cfg = config.logging
        else:
            cfg = config
        return LoggingConfig(
            debug=cfg.debug if hasattr(cfg, 'debug') else False,
            trace=cfg.trace if hasattr(cfg, 'trace') else False,
            info=cfg.info if hasattr(cfg, 'info') else False,
            record_log=cfg.record_log if hasattr(cfg, 'record_log') else False,
            logging_dir=cfg.logging_dir if hasattr(cfg, 'logging_dir') else os.path.join("~", ".bittensor", "miners")
        )

    def _configure_handlers(self, config: LoggingConfig) -> list[stdlogging.Handler]:
        """Configure logging handlers (StreamHandler and optional RotatingFileHandler)."""
        handlers = []
        # StreamHandler for console output
        stream_handler = stdlogging.StreamHandler(sys.stdout)
        self._stream_formatter = CustomBtStreamFormatter()
        stream_handler.setFormatter(self._stream_formatter)
        handlers.append(stream_handler)

        # FileHandler for file logging, if enabled
        if config.record_log and config.logging_dir:
            logfile = os.path.abspath(
                os.path.join(config.logging_dir, f"{DEFAULT_LOG_FILE_NAME}_{self._id_suffix}.log")
            )
            file_handler = RotatingFileHandler(
                logfile,
                maxBytes=DEFAULT_MAX_ROTATING_LOG_FILE_SIZE,
                backupCount=DEFAULT_LOG_BACKUP_COUNT,
            )
            file_handler.setFormatter(self._file_formatter)
            file_handler.setLevel(TRACE_LEVEL)
            handlers.append(file_handler)

        return handlers

    def _set_initial_level(self, config: LoggingConfig):
        """Set initial logging level based on config."""
        if config.trace:
            self._logger.setLevel(TRACE_LEVEL)
            self._stream_formatter.set_trace(True)
        elif config.debug:
            self._logger.setLevel(stdlogging.DEBUG)
            self._stream_formatter.set_trace(True)
        elif config.info:
            self._logger.setLevel(stdlogging.INFO)
            self._stream_formatter.set_trace(False)
        else:
            self._logger.setLevel(stdlogging.WARNING)
            self._stream_formatter.set_trace(False)

    def set_config(self, config: "Config"):
        """Update logging configuration."""
        self._config = self._extract_logging_config(config)

        # Update handlers
        for handler in self._logger.handlers[:]:
            self._logger.removeHandler(handler)
        self._handlers = self._configure_handlers(self._config)
        for handler in self._handlers:
            self._logger.addHandler(handler)

        # Update log level
        self._set_initial_level(self._config)

    def trace(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a trace message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.log(
            TRACE_LEVEL,
            msg,
            *args,
            **kwargs,
            stacklevel=stacklevel + CUSTOM_LOGGER_METHOD_STACK_LEVEL,
        )

    def debug(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a debug message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.debug(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def info(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log an info message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.info(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def success(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a success message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.log(
            SUCCESS_LEVEL,
            msg,
            *args,
            **kwargs,
            stacklevel=stacklevel + CUSTOM_LOGGER_METHOD_STACK_LEVEL,
        )

    def warning(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a warning message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.warning(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def error(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log an error message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.error(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def critical(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a critical message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.critical(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def fatal(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log a fatal message (mapped to CRITICAL level)."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.fatal(
            msg,
            *args,
            **kwargs,
            stacklevel=stacklevel + CUSTOM_LOGGER_METHOD_STACK_LEVEL,
        )

    def exception(self, msg="", prefix="", suffix="", *args, stacklevel=1, **kwargs):
        """Log an exception message."""
        msg = _concat_message(msg, prefix, suffix)
        if not msg:
            return
        self._logger.exception(msg, *args, **kwargs, stacklevel=stacklevel + 1)

    def set_debug(self, on: bool = True):
        """Enable or disable debug logging."""
        if on:
            self._logger.setLevel(stdlogging.DEBUG)
            self._stream_formatter.set_trace(True)
        else:
            self._logger.setLevel(stdlogging.WARNING)
            self._stream_formatter.set_trace(False)

    def set_trace(self, on: bool = True):
        """Enable or disable trace logging."""
        if on:
            self._logger.setLevel(TRACE_LEVEL)
            self._stream_formatter.set_trace(True)
        else:
            self._logger.setLevel(stdlogging.WARNING)
            self._stream_formatter.set_trace(False)

    def set_info(self, on: bool = True):
        """Enable or disable info logging."""
        if on:
            self._logger.setLevel(stdlogging.INFO)
            self._stream_formatter.set_trace(False)
        else:
            self._logger.setLevel(stdlogging.WARNING)

    def set_warning(self, on: bool = True):
        """Enable or disable warning logging."""
        if on:
            self._logger.setLevel(stdlogging.WARNING)
            self._stream_formatter.set_trace(False)
        else:
            self._logger.setLevel(stdlogging.CRITICAL)

    def set_default(self):
        """Set default logging level (WARNING)."""
        self._logger.setLevel(stdlogging.WARNING)
        self._stream_formatter.set_trace(False)

    def get_level(self) -> int:
        """Return current logging level."""
        return self._logger.level

    def setLevel(self, level):
        """Set the specified logging level."""
        self._logger.setLevel(level)

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser, prefix: str = None):
        """Add logging-specific arguments to parser."""
        prefix_str = "" if prefix is None else prefix + "."
        try:
            default_logging_debug = os.getenv("BT_LOGGING_DEBUG", False)
            default_logging_info = os.getenv("BT_LOGGING_INFO", False)
            default_logging_trace = os.getenv("BT_LOGGING_TRACE", False)
            default_logging_record_log = os.getenv("BT_LOGGING_RECORD_LOG", False)
            default_logging_logging_dir = os.getenv(
                "BT_LOGGING_LOGGING_DIR", os.path.join("~", ".bittensor", "miners")
            )
            parser.add_argument(
                "--" + prefix_str + "logging.debug",
                action="store_true",
                help="Turn on Bittensor debugging information",
                default=default_logging_debug,
            )
            parser.add_argument(
                "--" + prefix_str + "logging.trace",
                action="store_true",
                help="Turn on Bittensor trace level information",
                default=default_logging_trace,
            )
            parser.add_argument(
                "--" + prefix_str + "logging.info",
                action="store_true",
                help="Turn on Bittensor info level information",
                default=default_logging_info,
            )
            parser.add_argument(
                "--" + prefix_str + "logging.record_log",
                action="store_true",
                help="Turns on logging to file.",
                default=default_logging_record_log,
            )
            parser.add_argument(
                "--" + prefix_str + "logging.logging_dir",
                type=str,
                help="Logging default root directory.",
                default=default_logging_logging_dir,
            )
        except argparse.ArgumentError:
            pass

    @classmethod
    def config(cls) -> "Config":
        """Get config from the argument parser."""
        parser = argparse.ArgumentParser()
        cls.add_args(parser)
        return Config(parser)

    def __call__(
            self,
            config: "Config" = None,
            debug: bool = None,
            trace: bool = None,
            info: bool = None,
            record_log: bool = None,
            logging_dir: str = None,
    ):
        """Update configuration and logging settings."""
        if config is not None:
            cfg = self._extract_logging_config(config)
            if info is not None:
                cfg = LoggingConfig(cfg.debug, cfg.trace, info, cfg.record_log, cfg.logging_dir)
            elif debug is not None:
                cfg = LoggingConfig(debug, cfg.trace, cfg.info, cfg.record_log, cfg.logging_dir)
            elif trace is not None:
                cfg = LoggingConfig(cfg.debug, trace, cfg.info, cfg.record_log, cfg.logging_dir)
            if record_log is not None:
                cfg = LoggingConfig(cfg.debug, cfg.trace, cfg.info, record_log, cfg.logging_dir)
            if logging_dir is not None:
                cfg = LoggingConfig(cfg.debug, cfg.trace, cfg.info, cfg.record_log, logging_dir)
        else:
            cfg = LoggingConfig(
                debug=debug or False,
                trace=trace or False,
                info=info or False,
                record_log=record_log or False,
                logging_dir=logging_dir or os.path.join("~", ".bittensor", "miners"),
            )
        self.set_config(cfg)