# ========================================
# FileName: experiment.py
# Date: 27 avril 2023 - 11:36
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Experiment Command of the CLI
# =========================================

import os
import rich
from rich import prompt
from ..utils.logging import setup_logger
from ..core.database import (
    open_database, add_experiment, find_experiment_id)

logger = setup_logger()


# --------------------------------------------------------
# Command Add
# --------------------------------------------------------
def command_add_prompt():
    """Add experiment from prompt"""

    Prompt = prompt.Prompt

    logger.info("Experiment adding prompt")
    rich.print("Please enter the following information:")
    name = Prompt.ask(":bookmark: Name of the experiment")
    description = Prompt.ask(
            ":speech_balloon: Description of the experiment")
    path = Prompt.ask(":file_folder: Path to the experiment")

    while not os.path.exists(path):
        logger.error("Path does not exist")
        path = Prompt.ask(":file_folder: Path to the experiment")

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    if find_experiment_id(Session, path) != -1:
        logger.error("Experiment already exists")
        return

    executable = Prompt.ask(":gear: Executable of the experiment",
                            default=f"{path}/execute.sh")
    execute_command = Prompt.ask(
            ":gear: Execute command of the experiment",
            default=f"/usr/bin/bash")
    tags = Prompt.ask(
            ":label:  Tags of the experiment separated by a comma",
            default="").strip().split(",")
    if tags == [""]:
        tags = []
    datasets = Prompt.ask(
            ":floppy_disk: Datasets (path) of the experiment",
            default="").strip().split(",")
    if datasets == [""]:
        datasets = []

    rich.print("Please confirm the following information:")
    rich.print(f"Name: {name}")
    rich.print(f"Description: {description}")
    rich.print(f"Path: {path}")
    rich.print(f"Executable: {executable}")
    rich.print(f"Tags: {tags}")
    rich.print(f"Datasets: {datasets}")

    if prompt.Confirm.ask("Do you want to add this experiment?"):
        logger.info("Adding experiment to database")
        add_experiment(Session, path, name, description, executable,
                       execute_command, tags, datasets)
        logger.info("Experiment added to database")

    session.close_all()


def command_add_yaml():
    """Add experiment from yaml"""
    pass


# --------------------------------------------------------
# Command List
# --------------------------------------------------------
def command_list():
    """Show a list of all the experiments available"""
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    experiments = Session.query(Base.classes.experiments).all()

    rich.print(f"Total number of experiments: {len(experiments)}")
    for experiment in experiments:
        to_print = f":bookmark: [bold]{experiment.name}[/bold] - " +\
                   f":speech_balloon: {experiment.description} - " +\
                   f":file_folder: {experiment.path}"
        rich.print(to_print)
    session.close_all()
