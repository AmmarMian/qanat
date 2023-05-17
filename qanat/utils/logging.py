# ========================================
# FileName: logging.py
# Date: 20 avril 2023 - 17:32
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Logging tools.
# =========================================

import logging
from rich.logging import RichHandler
import sqlite3
import os
import yaml

DEFAULT_LOGGING_LEVEL = logging.DEBUG


def parse_logging_level(level):
    """Parse a logging level from a string.

    :param level: The logging level as a string.
    :type level: str

    :return: The logging level.
    :rtype: int
    """
    if level == 'DEBUG':
        return logging.DEBUG
    elif level == 'INFO':
        return logging.INFO
    elif level == 'WARNING':
        return logging.WARNING
    elif level == 'ERROR':
        return logging.ERROR
    elif level == 'CRITICAL':
        return logging.CRITICAL
    else:
        raise ValueError(f"Unknown logging level {level}.")


# TODO: Add tests for this function
def setup_logger(path='.qanat'):
    """Setup a logger for Qanat using rich console.

    :return: The logger.
    """

    try:
        with open(os.path.join(path, 'config.yaml'), 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
            LOGGING_LEVEL = parse_logging_level(config['logging'])
    except (FileNotFoundError, KeyError, ValueError):
        LOGGING_LEVEL = DEFAULT_LOGGING_LEVEL

    logging.basicConfig(
        level=LOGGING_LEVEL,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True,
                              tracebacks_suppress=[sqlite3])]
    )

    logger = logging.getLogger("rich")

    return logger
