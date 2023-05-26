# ========================================
# FileName: init.py
# Date: 26 avril 2023 - 08:57
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Init command of the CLI.
# =========================================

from ..core.repo import QanatRepertory, check_directory_is_qanat
from ..utils.logging import setup_logger


def init_qanat(path, yes=False):
    """Initialize the Qanat repertory.

    :param path: The path to the Qanat repertory.
    :type path: str

    :param yes: If True, the command will not ask for confirmation.
    :type yes: bool
    """
    logger = setup_logger()
    if check_directory_is_qanat(path):
        logger.info(f"Directory {path} is already a Qanat repertory.")
        return
    logger.info("Initializing Qanat repertory.")
    qanat_repo = QanatRepertory(path)
    qanat_repo.iniate_creation(yes=yes)
    logger.info("Qanat repertory initialized.")
