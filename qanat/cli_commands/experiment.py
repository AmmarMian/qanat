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
    open_database, add_experiment, find_experiment_id,
    find_dataset_id, count_number_runs_experiment,
    fetch_tags_of_experiment, delete_experiment,
    add_action)
from ._constants import (
    EXPERIMENT_NAME, EXPERIMENT_DESCRIPTION, EXPERIMENT_PATH,
    EXPERIMENT_EXECUTABLE, EXPERIMENT_EXECUTE_COMMAND, EXPERIMENT_TAGS,
    EXPERIMENT_DATASETS, EXPERIMENT_RUNS, EXPERIMENT_ID)
from rich.table import Table

logger = setup_logger()


# --------------------------------------------------------
# Command Add
# --------------------------------------------------------
def command_add_prompt():
    """Add experiment from prompt"""

    Prompt = prompt.Prompt

    logger.info("Experiment adding prompt")
    rich.print("Please enter the following information:")
    name = Prompt.ask(f"{EXPERIMENT_NAME} Name of the experiment")
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    if find_experiment_id(Session, name) != -1:
        logger.error("Experiment already exists")
        return

    description = Prompt.ask(
            f"{EXPERIMENT_DESCRIPTION} Description of the experiment")

    path = Prompt.ask(f"{EXPERIMENT_PATH} Path to the experiment")

    while not os.path.exists(path):
        logger.error("Path does not exist")
        path = Prompt.ask(f"{EXPERIMENT_PATH} Path to the experiment")

    executable = Prompt.ask(
            f"{EXPERIMENT_EXECUTABLE} Executable of the experiment "
            "(path from project root)",
            default=f"{path}/execute.sh")
    execute_command = Prompt.ask(
            f"{EXPERIMENT_EXECUTE_COMMAND} Execute command of the experiment",
            default="/usr/bin/bash")
    tags = Prompt.ask(
            f"{EXPERIMENT_TAGS} Tags of the experiment separated by a comma",
            default="").strip().split(",")
    if tags == [""]:
        tags = []

    datasets_in_db = [dataset.name for dataset in
                      Session.query(Base.classes.datasets).all()]
    if len(datasets_in_db) > 1:
        datasets_in_db = ', '.join(datasets_in_db)
    elif len(datasets_in_db) == 1:
        datasets_in_db = datasets_in_db[0]
    else:
        datasets_in_db = "No datasets is defined yet"

    datasets = Prompt.ask(
            f"{EXPERIMENT_DATASETS} Datasets (name) of the experiment\n "
            "List of datasets in the database:\n "
            f"[bold green]{datasets_in_db}[/bold green]\n"
            "Enter the names separated by a comma: ",
            default="").strip().split(",")

    if datasets == [""]:
        datasets = []

    # Check if datasets exist
    for dataset in datasets:
        if find_dataset_id(Session, dataset) == -1:
            logger.error(f"Dataset {dataset} does not exist")
            logger.error("Please add the dataset first by using the command: "
                         "'qanat dataset new'")
            session.close_all()
            return

    rich.print("Please confirm the following information:")
    rich.print(f"[bold]Name[/bold]: {name}")
    rich.print(f"[bold]Description[/bold]: {description}")
    rich.print(f"[bold]Path[/bold]: {path}")
    rich.print(f"[bold]Executable[/bold]: {executable}")
    rich.print(f"[bold]Tags[/bold]: {tags}")
    rich.print(f"[bold]Datasets[/bold]: {datasets}")

    if prompt.Confirm.ask("Do you want to add this experiment?"):
        logger.info("Adding experiment to database")
        add_experiment(Session, path, name, description, executable,
                       execute_command, tags, datasets)
        logger.info("Experiment added to database")

    # Add actions
    add_actions = prompt.Confirm.ask(
            "Would you like to add an action to this experiment ?\n"
            "It is possible to add actions later with the command "
            "'qanat experiment update'.\n")

    while add_actions:
        try:
            logger.info('Action adding prompt. Press Ctrl+C to cancel.')
            action_name = Prompt.ask(f"{EXPERIMENT_NAME} Name of the action")
            action_description = Prompt.ask(
                    f"{EXPERIMENT_DESCRIPTION} Description of the action")

            action_executable = Prompt.ask(
                    f"{EXPERIMENT_EXECUTABLE} Executable of the action"
                    "(path from project root)")

            action_command = Prompt.ask(
                    f"{EXPERIMENT_EXECUTE_COMMAND} Execute command of "
                    "the action",
                    default="/usr/bin/bash")

            add_action(Session, action_name, action_description,
                       action_executable, action_command, name)

        except KeyboardInterrupt:
            logger.info("Action adding canceled")

        add_actions = prompt.Confirm.ask(
                "Would you like to add another action to this experiment ?\n",
                default=False)

    session.close_all()


def command_add_yaml():
    """Add experiment from yaml"""
    # TODO: Implement this
    pass


# --------------------------------------------------------
# Command delete
# --------------------------------------------------------
def command_delete(experiment_name: str):
    """Remove experiment.

    :param experiment_name: Name of the experiment
    :type experiment_name: str
    """

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    if find_experiment_id(Session, experiment_name) == -1:
        logger.error("Experiment does not exist")
        Session.close_all()
        return

    # Fetch experiment information
    experiment_id = find_experiment_id(Session, experiment_name)
    number_runs = count_number_runs_experiment(Session, experiment_id)
    tags = fetch_tags_of_experiment(Session, experiment_id)
    description = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first().description
    path = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first().path

    rich.print("Please confirm the following information:")
    rich.print(f"[bold]{EXPERIMENT_NAME} Name[/bold]: {experiment_name}")
    rich.print(f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]: {description}")
    rich.print(f"[bold]{EXPERIMENT_PATH} Path[/bold]: {path}")
    rich.print(f"[bold]{EXPERIMENT_TAGS} Tags[/bold]: {tags}")
    rich.print(f"[bold]{EXPERIMENT_RUNS} Number of runs[/bold]: {number_runs}")

    if prompt.Confirm.ask("Do you want to remove this experiment?\n"
                          "This will remove all the runs associated with it "
                          "as well as results and logs.\n"
                          "[bold red]This action cannot be undone!\n"):
        logger.info("Removing experiment from database")
        delete_experiment(Session, experiment_name)
        logger.info("Experiment removed from database")

    session.close_all()


# --------------------------------------------------------
# Command List
# --------------------------------------------------------
def command_list():
    """Show a list of all the experiments available"""
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    experiments = Session.query(Base.classes.experiments).all()

    rich.print(f"Total number of experiments: [bold]{len(experiments)}[/bold]")
    grid = Table.grid(expand=False, padding=(0, 4))
    grid.add_column(justify="left", header="ID")
    grid.add_column(justify="left", header="Name")
    grid.add_column(justify="left", header="Description")
    grid.add_column(justify="left", header="Path")
    grid.add_column(justify="left", header="Number of runs")
    grid.add_column(justify="right", header="Tags", style="bold")
    grid.add_row("[bold]ID[/bold]",
                 "[bold]Name[/bold]", "[bold]Description[/bold]",
                 "[bold]Path[/bold]", "[bold]Number of runs[/bold]",
                 "[bold]Tags[/bold]")
    for experiment in experiments:
        runs_count = count_number_runs_experiment(Session, experiment.name)
        tags = fetch_tags_of_experiment(Session, experiment.name)
        if len(tags) >= 1:
            tags = f"{EXPERIMENT_TAGS} " +\
                   f", {EXPERIMENT_TAGS} ".join(fetch_tags_of_experiment(
                                                Session, experiment.name))
        else:
            tags = ""

        grid.add_row(f"{EXPERIMENT_ID} {experiment.id}",
                     f"{EXPERIMENT_NAME} {experiment.name}",
                     f"{EXPERIMENT_DESCRIPTION} {experiment.description}",
                     f"{EXPERIMENT_PATH} {experiment.path}",
                     f"{EXPERIMENT_RUNS} {runs_count}",
                     f"{tags}")
    rich.print(grid)
    session.close_all()
