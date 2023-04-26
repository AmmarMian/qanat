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

LOGGING_LEVEL = logging.DEBUG

logging.basicConfig(
    level=LOGGING_LEVEL,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True,
                          tracebacks_suppress=[sqlite3])]
)


# TODO: Add tests for this function
def setup_logger():
    """Setup a logger for Qanat using rich console.

    :return: The logger.
    """
    logger = logging.getLogger("rich")

    return logger
