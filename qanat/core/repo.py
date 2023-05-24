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
from rich import prompt
from pathlib import Path
import yaml

from ..utils.logging import setup_logger
from ..core.database import init_database


def check_directory_is_qanat(path='./'):
    """Check if directory is a Qanat repertory.

    :param path: The path to the directory to check.
    :type path: str

    :return: True if the directory is a Qanat repertory, False otherwise.
    :rtype: bool
    """
    is_qanat = os.path.exists(os.path.join(path, ".qanat"))
    is_qanat = is_qanat and os.path.exists(
            os.path.join(path, ".qanat/database.db"))
    is_qanat = is_qanat and os.path.exists(
            os.path.join(path, ".qanat/config.yaml"))
    return is_qanat


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

        # Asking about result directory
        Prompt = prompt.Prompt()
        self.result_dir_path = Prompt.ask(
                "Where do you want to store the results?",
                default=os.path.join(self.path, "results"))

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
        else:
            self.logger.info("Qanat repertory already exists.")

        if not os.path.path.exists(
                os.path.join(self.qanat_dir_path, "cache")):
            self.logger.info("Creating cache directory.")
            os.mkdir(os.path.join(self.qanat_dir_path, "cache"))

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
                should_gitignore = True
            else:
                should_gitignore = False
        else:
            self.logger.info("Repertory is a git repository.")
            should_gitignore = True

        # Create results directory if needed
        if not os.path.exists(self.result_dir_path):
            self.logger.info("Creating results directory.")
            os.mkdir(self.result_dir_path)

        # Creating .qanat/config.yaml
        # Check whether resutls directory is inside path
        # TODO: Make it more robust to really check the
        #       contents of current directory recursively
        if self.result_dir_path.startswith(self.path):
            result_path = os.path.relpath(self.result_dir_path, self.path)
            should_add_results = True
        else:
            result_path = self.result_dir_path
        if not os.path.exists(
                os.path.join(self.qanat_dir_path, "config.yaml")):
            self.logger.info("Creating .qanat/config.yaml.")
            with open(
                    os.path.join(self.qanat_dir_path, "config.yaml"),
                    "w") as f:
                default_htcondor_options = {
                    'request_cpus': 1,
                    'request_memory': '1GB',
                    'request_disk': '1GB',
                    'request_gpus': 0,
                    'universe': 'vanilla',
                    '+WishedAcctGroup': 'group_usmb.listic',
                    'getenv': 'true',
                }
                yaml.dump(
                        {"result_dir": result_path,
                         "logging": "INFO",
                         "htcondor": {"default": default_htcondor_options}},
                        f,
                        default_flow_style=False)
        else:
            # Add result_dir to .qanat/config.yaml if not already there
            with open(
                    os.path.join(self.qanat_dir_path, "config.yaml"),
                    "r") as f:
                config = yaml.safe_load(f)
                if config["result_dir"] != result_path:
                    self.logger.info(
                            "Adding result_dir to .qanat/config.yaml.")
                    config["result_dir"] = result_path
                    should_commit = True

                    with open(os.path.join(self.qanat_dir_path, "config.yaml"),
                              "w") as f:
                        yaml.dump(config, f, default_flow_style=False)

        if self.result_dir_path.startswith(self.path):
            should_add_results = True

        # Add .qanat/ to .gitignore except .qanat/config.yaml
        if should_gitignore:
            self.logger.info("Adding .qanat to .gitignore.")
            if not os.path.exists(os.path.join(self.path, ".gitignore")):
                # create empty file
                Path(os.path.join(self.path, ".gitignore")).touch()

            with open(os.path.join(self.path, ".gitignore"), "r+") as f:
                # check if not already in gitignore
                for line in f:
                    if '.qanat' in line:
                        self.logger.info(
                                "Qanat repertory already in .gitignore.")
                        break
                else:
                    should_commit = True
                    f.seek(0, os.SEEK_END)
                    f.write(".qanat\n")

            if should_add_results:
                self.logger.info(f"Adding {result_path} to .gitignore.")
                with open(os.path.join(self.path, ".gitignore"), "r+") as f:
                    # check if not already in gitignore
                    for line in f:
                        if result_path in line:
                            self.logger.info(
                                    "Results repertory already in .gitignore.")
                            break
                    else:
                        should_commit = True
                        f.seek(0, os.SEEK_END)
                        f.write(f"{result_path}\n")

        # Commit the changes if user want to
        if should_commit:
            if Confirm.ask("Do you want to commit the changes?"):
                self.logger.info("Commiting the creation of qanat.")
                repo = git.Repo(self.path)
                repo.index.add([".gitignore"])
                repo.index.commit("Create qanat repertory.")
