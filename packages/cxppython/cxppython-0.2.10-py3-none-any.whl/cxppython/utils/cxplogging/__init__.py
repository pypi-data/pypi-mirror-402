"""
cxplogging sub-package standardized logging for Bittensor.

This module provides logging functionality for the Bittensor package. It includes custom loggers, handlers, and
formatters to ensure consistent logging throughout the project.
"""

from .loggingmachine import LoggingMachine
# from .logginsimple import LoggingSimple

logging = LoggingMachine(LoggingMachine.config())
# logging = LoggingSimple(LoggingMachine.config())

