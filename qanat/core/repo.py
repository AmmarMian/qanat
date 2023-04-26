# ========================================
# FileName: repo.py
# Date: 26 avril 2023 - 08:58
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Qanat repertory management.
# =========================================

import os
import git
from rich.prompt import Confirm
from pathlib import Path

from ..utils.logging import setup_logger
from ..core.database import init_database


class QanatRepertory:
    """Class for managing the Qanat repertory."""

    def __init__(self, path):
        """Initialize the Qanat repertory.

        :param path: The path to the Qanat repertory.
        :type path: str
        """

        # Check if path exists
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist.")

        # Check if path does not finish with .qanat
        if os.path.basename(os.path.normpath(path)) != ".qanat":
            self.path = path
            self.qanat_dir_path = os.path.join(path, ".qanat")
        else:
            self.path = os.path.dirname(os.path.normpath(path))
            self.qanat_dir_path = path

        self.path = path
        self.logger = setup_logger()

    def check_exists_qanat(self):
        """Check if the Qanat repertory exists.

        :return: True if the Qanat repertory exists, False otherwise.
        :rtype: bool
        """
        self.logger.info(
                f"Checking if .qanat repertory exists in {self.path}.")
        return os.path.exists(self.qanat_dir_path)

    def create_qanat(self):
        """Create the Qanat repertory."""
        if not self.check_exists_qanat():
            self.logger.info("Creating Qanat repertory.")
            os.mkdir(self.qanat_dir_path)
            return False
        else:
            self.logger.info("Qanat repertory already exists.")
            return True

    def check_git(self):
        """Check if the repertory is a git repository.

        :return: True if the Qanat repertory is a git repository,
                 False otherwise.
        :rtype: bool
        """
        self.logger.info("Checking if repertory is a git repository.")
        return os.path.exists(os.path.join(self.path, ".git"))

    def iniate_creation(self):
        """Initiate the creation of the Qanat repertory."""

        should_commit = False

        # .qanat repertory
        self.create_qanat()

        # Creating database if not exists
        if not os.path.exists(
                os.path.join(self.qanat_dir_path, "database.db")):
            self.logger.info("Creating database.")
            init_database(os.path.join(self.qanat_dir_path, "database.db"))
        else:
            self.logger.info("Database already exists.")

        # .git repertory
        if not self.check_git():
            self.logger.warning("Repertory is not a git repository.")
            if Confirm.ask("Do you want to create a git repository?"):
                self.logger.info("Creating git repository.")
                git.Repo.init(self.path)
                sould_gitignore = True
            else:
                sould_gitignore = False
        else:
            self.logger.info("Repertory is a git repository.")
            sould_gitignore = True

        # Add .qanat/ to .gitignore except .qanat/config.yaml
        if sould_gitignore:
            self.logger.info("Adding .qanat/ to .gitignore.")
            if not os.path.exists(os.path.join(self.path, ".gitignore")):
                # create empty file
                Path(os.path.join(self.path, ".gitignore")).touch()

            with open(os.path.join(self.path, ".gitignore"), "r+") as f:
                # check if not already in gitignore
                for line in f:
                    if '.qanat/' in line:
                        self.logger.info(
                                "Qanat repertory already in .gitignore.")
                        break
                else:
                    should_commit = True
                    f.seek(0, os.SEEK_END)
                    f.write(".qanat/*\n")
                    f.write("!.qanat/config.yaml")

        # Commit the changes if user want to
        if should_commit:
            if Confirm.ask("Do you want to commit the changes?"):
                self.logger.info("Commiting the creation of qanat.")
                repo = git.Repo(self.path)
                repo.index.add([".gitignore", ".qanat"])
                repo.index.commit("Create qanat repertory.")
