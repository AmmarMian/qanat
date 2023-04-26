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
import argparse
import sqlite3

LOGGING_LEVEL = logging.DEBUG


# TODO: Add tests for this function
def setup_logger(name=""):
    """Setup a logger for Qanat using rich console.

    :param name: The name of the logger.
    :type name: str
    :return: The logger.
    """
    if name == "":
        custom_format = "%(message)s"
    else:
        custom_format = f"[{name}] %(message)s"
    logger = logging.getLogger(f"qanat-{name}")
    logger.setLevel(LOGGING_LEVEL)

    handler = RichHandler(rich_tracebacks=True,
                          tracebacks_suppress=[sqlite3, argparse])
    handler.setLevel(LOGGING_LEVEL)

    formatter = logging.Formatter(f"{custom_format} %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
