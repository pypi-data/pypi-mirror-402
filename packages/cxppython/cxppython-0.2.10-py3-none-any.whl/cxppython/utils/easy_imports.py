from cxppython.utils.cxplogging import logging
from cxppython.bittensor.synapse import Synapse
synapse = Synapse
# Logging helpers.
def trace(on: bool = True):
    """
    Enables or disables trace logging.
    Args:
        on (bool): If True, enables trace logging. If False, disables trace logging.
    """
    logging.set_trace(on)


def debug(on: bool = True):
    """
    Enables or disables debug logging.
    Args:
        on (bool): If True, enables debug logging. If False, disables debug logging.
    """
    logging.set_debug(on)


def warning(on: bool = True):
    """
    Enables or disables warning logging.
    Args:
        on (bool): If True, enables warning logging. If False, disables warning logging and sets default (WARNING) level.
    """
    logging.set_warning(on)


def info(on: bool = True):
    """
    Enables or disables info logging.
    Args:
        on (bool): If True, enables info logging. If False, disables info logging and sets default (WARNING) level.
    """
    logging.set_info(on)
