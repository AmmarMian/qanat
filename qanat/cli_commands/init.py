# ========================================
# FileName: init.py
# Date: 26 avril 2023 - 08:57
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Init command of the CLI.
# =========================================

from ..core.repo import QanatRepertory
from ..utils.logging import setup_logger


def init_qanat(path):
    """Initialize the Qanat repertory.

    :param path: The path to the Qanat repertory.
    :type path: str
    """
    logger = setup_logger()
    logger.info("Initializing Qanat repertory.")
    qanat_repo = QanatRepertory(path)
    qanat_repo.iniate_creation()
    logger.info("Qanat repertory initialized.")
