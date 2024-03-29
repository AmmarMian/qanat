# ========================================
# FileName: experiment.py
# Date: 27 avril 2023 - 11:36
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Experiment Command of the CLI
# =========================================

import os
import sys
import time
from datetime import datetime
import rich
from rich.table import Table
from rich import prompt
from rich.console import Console
from rich.live import Live
import rich_click as click
import sqlalchemy
import yaml
from typing import List
from ..utils.logging import setup_logger
from ..core.database import (
    open_database, add_experiment, find_experiment_id,
    find_dataset_id, count_number_runs_experiment,
    find_tag_id,
    fetch_tags_of_experiment, delete_experiment,
    fetch_datasets_of_experiment, fetch_runs_of_experiment,
    add_action, fetch_tags_of_run, add_tag,
    fetch_actions_of_experiment,
    update_experiment, delete_action, Experiment, Action,
    update_run_progress,
    RunOfAnExperiment)
from ._constants import (
    EXPERIMENT_NAME, EXPERIMENT_DESCRIPTION, EXPERIMENT_PATH,
    EXPERIMENT_EXECUTABLE, EXPERIMENT_EXECUTE_COMMAND, EXPERIMENT_TAGS,
    EXPERIMENT_DATASETS, EXPERIMENT_RUNS, EXPERIMENT_ID,
    EXPERIMENT_ACTION, get_run_status_emoji, EXIT, RUNNER,
    RUN_LAUNCH_DATE, RUN_DURATION, EXPERIMENT_LIVE_REFRESH, STATUS,
    PROGRESS)
from ..core.runs import (
    LocalMachineExecutionHandler,
    HTCondorExecutionHandler,
    SlurmExecutionHandler,
)
from ..core.actions import ActionExecutionHandler

logger = setup_logger()


# --------------------------------------------------------
# Command Action
# --------------------------------------------------------
def command_action(experiment_name: str, action_name: str,
                   run_id: int, ctx: click.Context = None,
                   group_no: int = None):
    """Execute action on a run of an experiment.

    :param experiment_name: Name of the experiment
    :param type: str

    :param action_name: Name of the action
    :param type: str

    :param run_id: ID of the run
    :param type: int

    :param ctx: Click context
    :param type: click.Context

    :param group_no: Group number
    :param type: int
    """

    engine, Base, session = open_database('.qanat/database.db')

    # Check if action_name is associated with the experiment
    Session = session()
    experiment_id = find_experiment_id(Session, experiment_name)
    if experiment_id == -1:
        logger.error("Experiment does not exist")
        return
    experiment_actions = fetch_actions_of_experiment(Session, experiment_name)
    action_names = [action.name for action in experiment_actions]
    if action_name not in action_names:
        logger.error(
                f"Action '{action_name}' is not associated with the experiment")
        return

    # Check if run_id is associated with the experiment
    run_ids = [run.id
               for run in
               fetch_runs_of_experiment(Session, experiment_name)]

    if run_id not in run_ids:
        logger.error("Run is not associated with the experiment: "
                     f"{experiment_name}")
        return

    # Execute action
    action_handler = ActionExecutionHandler(
        session, run_id, action_name, experiment_name,
        group_no)
    action_handler.execute_action(ctx)


# --------------------------------------------------------
# Command Add
# --------------------------------------------------------
def command_new_experiment_from_yaml(yaml_file: str):
    """Add new experiment to the database
    from a yaml file.

    :param yaml_file: Path to the yaml file
    :param type: str
    """
    if not os.path.exists(yaml_file):
        logger.error("Yaml file does not exist")
        return

    with open(yaml_file, 'r') as f:
        experiment = yaml.safe_load(f)

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    # Check if experiment already exists
    if find_experiment_id(Session, experiment['name']) != -1:
        logger.error("Experiment already exists")
        return

    # Check if datasets exist
    if 'datasets' in experiment:
        for dataset in experiment['datasets']:
            if find_dataset_id(Session, dataset) == -1:
                logger.error(f"Dataset {dataset} does not exist")
                return
    else:
        experiment['datasets'] = []

    # Check if tags exist
    if 'tags' in experiment:
        for tag in experiment['tags']:
            if find_tag_id(Session, tag) == -1:
                logger.info(f'tag {tag} does not exist'
                            ' and will be added to the database')
                add_tag(Session, tag, "")
                Session.commit()
    else:
        experiment['tags'] = []

    # Add experiment
    add_experiment(Session, experiment['path'], experiment['name'],
                   experiment['description'], experiment['executable'],
                   experiment['executable_command'], experiment['tags'],
                   experiment['datasets'])
    Session.commit()

    logger.info("Experiment added successfully")

    # Add actions
    if 'actions' in experiment:
        experiment_id = find_experiment_id(Session, experiment['name'])
        for action in experiment['actions']:

            action_info = action.values()
            action_info = list(action_info)
            action_info = action_info[0]

            # Check if action already exists for the experiment
            if Session.query(Action).filter_by(
                    name=action_info['name'],
                    experiment_id=experiment_id).count() > 0:
                logger.error(
                        f"Action {action['name']} already "
                        "exists for the experiment")
                return

            # Add action
            add_action(Session, action_info['name'],
                       action_info['description'],
                       action_info['executable'],
                       action_info['executable_command'],
                       experiment['name'])
        Session.commit()

        logger.info("Actions added successfully")

    Session.commit()
    Session.close()


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

    # Check if tags exist
    for tag in tags:
        if find_experiment_id(Session, tag) == -1:
            logger.info(f"Tag {tag} does not exist")
            logger.info("Creating tag")
            tag_description = Prompt.ask(
                f'{EXPERIMENT_DESCRIPTION} Please add a description '
                f'for the tag [bold yellow]{tag}[/bold yellow]]',
                default="")
            add_tag(Session, tag, tag_description)

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
    else:
        logger.info("Experiment not added to database")
        session.close_all()
        return

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
# Command update
# --------------------------------------------------------
def action_update_prompt(Session: sqlalchemy.orm.session.Session,
                         experiment_name: str):
    """Update an action from prompt

    :param Session: SQLAlchemy session
    :type Session: sqlalchemy.orm.session.Session

    :param experiment_name: Name of the experiment
    :type experiment_name: str
    """

    Prompt = prompt.Prompt()
    continue_action_prompt = True
    list_actions_names = [action.name for action in
                          fetch_actions_of_experiment(
                              Session, experiment_name)]
    while continue_action_prompt:

        choice = Prompt.ask(
                f"{EXPERIMENT_ACTION} Do you want to add or "
                "remove an action? (add/remove/exit)",
                default='exit')

        while choice not in ['add', 'remove', 'exit']:
            logger.error("Invalid input")
            choice = Prompt.ask(
                    f"{EXPERIMENT_ACTION} Do you want to add or "
                    "remove an action? (add/remove/exit)",
                    default='exit')

        if choice == 'add':

            add_actions = True
            while add_actions:
                try:
                    logger.info(
                            'Action adding prompt. Press Ctrl+C to cancel.')
                    action_name = Prompt.ask(
                            f"{EXPERIMENT_NAME} Name of the action")
                    action_description = Prompt.ask(
                            f"{EXPERIMENT_DESCRIPTION} Description of the "
                            "action")

                    action_executable = Prompt.ask(
                            f"{EXPERIMENT_EXECUTABLE} Executable of the action"
                            "(path from project root)")

                    action_command = Prompt.ask(
                            f"{EXPERIMENT_EXECUTE_COMMAND} "
                            "Execute command of "
                            "the action",
                            default="/usr/bin/bash")

                    add_action(
                            Session, action_name,
                            action_description,
                            action_executable, action_command,
                            experiment_name)
                    logger.info(f"Action {action_name} added to database")
                    list_actions_names = [action.name for action in
                                          fetch_actions_of_experiment(
                                           Session, experiment_name)]

                except KeyboardInterrupt:
                    logger.info("Action adding canceled")

                add_actions = prompt.Confirm.ask(
                        "Would you like to add another action "
                        "to this experiment ?\n",
                        default=False)

        elif choice == 'remove':
            remove_actions = True
            while remove_actions:
                try:
                    logger.info(
                            'Action removing prompt. Press Ctrl+C to cancel.')
                    action_name = Prompt.ask(
                            f"{EXPERIMENT_NAME} Name of the action to "
                            "remove.\n"
                            f"List of actions in the database:\n"
                            f"[bold green]{list_actions_names}\n")
                    success = delete_action(Session, action_name,
                                            experiment_name)
                    if success:
                        logger.info(
                                f"Action {action_name} removed from database")

                except KeyboardInterrupt:
                    logger.info("Action removing canceled")

                remove_actions = prompt.Confirm.ask(
                        "Would you like to remove another action "
                        "from this experiment ?\n",
                        default=False)

        continue_action_prompt = \
            (choice == 'add' or choice == 'remove')


def parse_update_choices(Session: sqlalchemy.orm.session.Session,
                         to_update: list,
                         dataset_names: list, datasets_in_db: list,
                         tags: list, experiment: Experiment) -> list:
    """Parse the update choices

    :param Session: SQLAlchemy session
    :type Session: sqlalchemy.orm.session.Session

    :param to_update: List of items to update
    :type to_update: list

    :param dataset_names: List of dataset names
    :type dataset_names: list

    :param datasets_in_db: List of datasets in database
    :type datasets_in_db: list

    :param tags: List of tags
    :type tags: list


    :param experiment: Experiment to update
    :type experiment: qanat.core.database.Experiment
    """

    new_experiment_name, new_experiment_description, \
        new_experiment_path, new_experiment_executable, \
        new_experiment_executable_command,\
        new_experiment_datasets, \
        new_experiment_tags = \
        None, None, None, None, None, None, None

    Prompt = prompt.Prompt()
    for item in to_update:
        if item == '1':
            new_experiment_name = Prompt.ask(
                    f"{EXPERIMENT_NAME} New experiment name",
                    default=experiment.name)

        elif item == '2':
            new_experiment_description = Prompt.ask(
                    f"{EXPERIMENT_DESCRIPTION} New experiment "
                    "description",
                    default=experiment.description)

        elif item == '3':
            new_experiment_path = Prompt.ask(
                    f"{EXPERIMENT_PATH} New experiment path",
                    default=experiment.path)

        elif item == '4':
            new_experiment_executable = Prompt.ask(
                    f"{EXPERIMENT_EXECUTABLE} New experiment "
                    "executable",
                    default=experiment.executable)

        elif item == '5':
            new_experiment_executable_command = Prompt.ask(
                    f"{EXPERIMENT_EXECUTE_COMMAND} New experiment "
                    "executable command",
                    default=experiment.executable_command)

        elif item == '6':
            new_experiment_datasets = Prompt.ask(
                    f"{EXPERIMENT_DATASETS} New experiment datasets"
                    f" (available datasets: [bold]{datasets_in_db}[/bold])\n"
                    f"Please enter the name of the datasets "
                    f"separated by a comma (e.g. dataset1,dataset2)",
                    default=",".join(dataset_names))
            new_experiment_datasets = \
                new_experiment_datasets.strip().split(',')
            while not all(item in datasets_in_db
                          for item in new_experiment_datasets):
                logger.error("Invalid input")
                new_experiment_datasets = Prompt.ask(
                        f"{EXPERIMENT_DATASETS} New experiment datasets ("
                        f"available datasets: [bold]{datasets_in_db}[/bold])\n"
                        f"Please enter the name of the datasets "
                        f"separated by a comma (e.g. dataset1,dataset2)",
                        default=dataset_names).strip().split(',')

        elif item == '7':
            new_experiment_tags = Prompt.ask(
                    f"{EXPERIMENT_TAGS} New experiment tags"
                    " (separated by a comma)",
                    default=",".join(tags))
            new_experiment_tags = new_experiment_tags.strip().split(',')
            if new_experiment_tags == ['']:
                new_experiment_tags = []
            for tag in new_experiment_tags:
                if find_tag_id(Session, tag) == -1:
                    logger.info(f"Tag {tag} does not exist")
                    logger.info("Creating tag")
                    tag_description = Prompt.ask(
                        f'{EXPERIMENT_DESCRIPTION} Please add a description '
                        f'for the tag [bold yellow]{tag}[/bold yellow]]',
                        default="")
                    add_tag(Session, tag, tag_description)

        elif item == '8':
            action_update_prompt(Session, experiment.name)

    return new_experiment_name, new_experiment_description, \
        new_experiment_path, new_experiment_executable, \
        new_experiment_executable_command, new_experiment_datasets, \
        new_experiment_tags


def command_update(experiment_name: str):
    """Update an existing experiment.

    :param experiment_name: Name of the experiment
    :type experiment_name: str
    """

    # Check if experiment exists
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    if find_experiment_id(Session, experiment_name) == -1:
        logger.error("Experiment does not exist")
        Session.close_all()
        return

    Prompt = prompt.Prompt()

    datasets_in_db = [dataset.name for dataset in
                      Session.query(Base.classes.datasets).all()]
    if len(datasets_in_db) > 1:
        datasets_in_db = ', '.join(datasets_in_db)
    elif len(datasets_in_db) == 1:
        datasets_in_db = datasets_in_db[0]
    else:
        datasets_in_db = "No datasets is defined yet"

    experiment = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first()
    number_runs = count_number_runs_experiment(Session, experiment_name)
    datasets_names = [dataset.name for dataset in
                      fetch_datasets_of_experiment(Session, experiment_name)]
    tags = fetch_tags_of_experiment(Session, experiment_name)
    rich.print(f"[bold]{EXPERIMENT_NAME} Name[/bold]: {experiment.name}")
    rich.print(f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]: "
               f"{experiment.description}")
    rich.print(f"[bold]{EXPERIMENT_PATH} Path[/bold]: {experiment.path}")
    rich.print(f"[bold]{EXPERIMENT_DATASETS} Datasets[/bold]:"
               f"{datasets_names}")
    rich.print(f"[bold]{EXPERIMENT_EXECUTABLE} Executable[/bold]: "
               f"{experiment.executable}")
    rich.print(f"[bold]{EXPERIMENT_EXECUTE_COMMAND} Execute command[/bold]: "
               f"{experiment.executable_command}")
    rich.print(f"[bold]{EXPERIMENT_RUNS} Number of runs[/bold]: {number_runs}")
    rich.print(f"[bold]{EXPERIMENT_TAGS} Tags[/bold]: {tags}")

    # Get actions associated with the experiment
    actions = fetch_actions_of_experiment(Session, experiment_name)
    if len(actions) >= 1:
        rich.print(f"[bold]{EXPERIMENT_ACTION} Actions[/bold]:")
        for action in actions:
            rich.print(f"  - [bold]{action.name}[/bold]: {action.description}")

    if prompt.Confirm.ask("Do you want to update this experiment?",
                          default=False):

        continue_updating = True
        while continue_updating:
            choices = [f'1 - {EXPERIMENT_NAME} Name',
                       f'2 - {EXPERIMENT_DESCRIPTION} Description',
                       f'3 - {EXPERIMENT_PATH} Path',
                       f'4 - {EXPERIMENT_EXECUTABLE} Executable',
                       f'5 - {EXPERIMENT_EXECUTE_COMMAND} Execute command',
                       f'6 - {EXPERIMENT_DATASETS} Datasets',
                       f'7 - {EXPERIMENT_TAGS} Tags',
                       f'8 - {EXPERIMENT_ACTION} Actions',
                       f'9 - {EXIT} Exit']
            to_update = Prompt.ask("What do you want to update?\n" +
                                   "\n".join(choices) +
                                   "\nPlease enter the number of the "
                                   "corresponding actions separated by "
                                   "a comma (e.g. 1,3,4)",
                                   default='9')
            to_update = to_update.strip().split(',')

            while not all(item in ['1', '2', '3', '4', '5', '6', '7', '8', '9']
                          for item in to_update):
                logger.error("Invalid input")
                to_update = Prompt.ask("What to update?\n" +
                                       "\n".join(choices) +
                                       "Please enter the number of the "
                                       "corresponding actions separated by "
                                       "a comma (e.g. 1,3,4)",
                                       default='7')
                to_update = to_update.strip().split(',')

            if '9' in to_update:
                continue_updating = False
                continue

            new_experiment_name, new_experiment_description, \
                new_experiment_path, new_experiment_executable, \
                new_experiment_executable_command, new_experiment_datasets, \
                new_experiment_tags = parse_update_choices(
                        Session, to_update, datasets_names,
                        datasets_in_db, tags, experiment)

            update_experiment(Session, experiment_name, new_experiment_name,
                              new_experiment_description, new_experiment_path,
                              new_experiment_executable,
                              new_experiment_executable_command,
                              new_experiment_tags, new_experiment_datasets)
            logger.info("Experiment updated successfully.")

        Session.close_all()


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
        sys.exit(1)

    # Fetch experiment information
    experiment_id = find_experiment_id(Session, experiment_name)
    number_runs = count_number_runs_experiment(Session, experiment_id)
    tags = fetch_tags_of_experiment(Session, experiment_id)
    description = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first().description
    path = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first().path
    datasets_names = [dataset.name for dataset in
                      fetch_datasets_of_experiment(Session, experiment_name)]

    rich.print("Please confirm the following information:")
    rich.print(f"[bold]{EXPERIMENT_NAME} Name[/bold]: {experiment_name}")
    rich.print(f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]: "
               f"{description}")
    rich.print(f"[bold]{EXPERIMENT_PATH} Path[/bold]: {path}")
    rich.print(f"[bold]{EXPERIMENT_DATASETS} Datasets[/bold]:"
               f"{datasets_names}")
    rich.print(f"[bold]{EXPERIMENT_TAGS} Tags[/bold]: {tags}")
    rich.print(f"[bold]{EXPERIMENT_RUNS} Number of runs[/bold]: {number_runs}")

    # Get actions associated with the experiment
    actions = fetch_actions_of_experiment(Session, experiment_name)
    if len(actions) >= 1:
        rich.print(f"[bold]{EXPERIMENT_ACTION} Actions[/bold]:")
        for action in actions:
            rich.print(f"  - [bold]{action.name}[/bold]: {action.description}")

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
    grid = Table.grid(expand=False, padding=(1, 4))
    grid.add_column(justify="left", header="ID")
    grid.add_column(justify="left", header="Name")
    grid.add_column(justify="left", header="Description")
    grid.add_column(justify="left", header="Path")
    grid.add_column(justify="left", header="Number of runs")
    grid.add_column(justify="right", header="Tags", style="bold")
    grid.add_row(f"[bold]{EXPERIMENT_ID} ID[/bold]",
                 f"[bold]{EXPERIMENT_NAME} Name[/bold]",
                 f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]",
                 f"[bold]{EXPERIMENT_PATH} Path[/bold]",
                 f"[bold]{EXPERIMENT_RUNS} Number of runs[/bold]",
                 f"[bold]{EXPERIMENT_TAGS} Tags[/bold]")
    for experiment in experiments:
        runs_count = count_number_runs_experiment(Session, experiment.name)
        tags = fetch_tags_of_experiment(Session, experiment.name)
        if len(tags) >= 1:
            tags = ", ".join(fetch_tags_of_experiment(
                Session, experiment.name))
        else:
            tags = ""

        grid.add_row(f"{experiment.id}",
                     f"{experiment.name}",
                     f"{experiment.description}",
                     f"{experiment.path}",
                     f"{runs_count}",
                     f"{tags}")
    rich.print(grid)
    session.close_all()


# --------------------------------------------------------
# Command status
# -------------------------------------------------------
def generate_grid_runs(sessionmaker: sqlalchemy.orm.sessionmaker,
                       runs: List[RunOfAnExperiment]) -> Table:
    """Generate rich grid of runs to render in the console.

    :param sessionmaker: Sessionmaker of the database
    :type sessionmaker: sqlalchemy.orm.sessionmaker

    :param runs: List of runs
    :type runs: List[RunOfAnExperiment]

    :return: Table of runs
    :rtype: Table
    """
    grid = Table.grid(expand=False, padding=(0, 4))
    grid.add_column(justify="left", header="ID")
    grid.add_column(justify="left", header="Description")
    grid.add_column(justify="left", header="Path")
    grid.add_column(justify="center", header="Runner")
    grid.add_column(justify="left", header="Launch date")
    grid.add_column(justify="left", header="Duration")
    grid.add_column(justify="center", header="Status", no_wrap=True)
    grid.add_column(justify="left", header="Tags", style="bold")
    grid.add_column(justify="right", header="Progress")
    grid.add_row(f"[bold]{EXPERIMENT_ID} ID[/bold]",
                 f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]",
                 f"[bold]{EXPERIMENT_PATH} Path[/bold]",
                 f"[bold]{RUNNER} Runner[/bold]",
                 f"[bold]{RUN_LAUNCH_DATE} Launch date[/bold]",
                 f"[bold]{RUN_DURATION} Duration[/bold]",
                 f"[bold]{STATUS} Status[/bold]",
                 f"[bold]{EXPERIMENT_TAGS} Tags[/bold]",
                 f"[bold]{PROGRESS} Progress[/bold]")

    Session = sessionmaker()
    for i, run in enumerate(runs):

        tags = fetch_tags_of_run(Session, run.id)
        if len(tags) >= 1:
            tags = ", ".join(fetch_tags_of_run(Session, run.id))
        else:
            tags = ""

        if run.launched is not None:
            if run.status == "running":
                duration = datetime.now() - run.launched
            elif run.status == "finished" and run.finished is not None:
                duration = run.finished - run.launched
            else:
                duration = "N/A"
        else:
            duration = "N/A"

        RUN_STATUS = get_run_status_emoji(run.status)
        grid.add_row(f"{run.id}",
                     f"{run.description}",
                     f"{run.storage_path}",
                     f"{run.runner}",
                     f"{run.launched}",
                     f"{duration}",
                     f"{RUN_STATUS}",
                     f"{tags}",
                     f"{run.progress}")

    Session.close()
    return grid


def fetch_status_runs(sessionmaker: sqlalchemy.orm.sessionmaker,
                      experiment_name: str,
                      animation: bool = False) -> List[RunOfAnExperiment]:
    """Fetch the status of the runs of an experiment.

    :param sessionmaker: Sessionmaker of the database
    :type sessionmaker: sqlalchemy.orm.sessionmaker

    :param experiment_name: Name of the experiment
    :type experiment_name: str

    :param animation: If True, the command will be show a spinner
                      animation while fetching the status of the runs
    :type animation: bool

    :return: List of runs
    :rtype: List[RunOfAnExperiment]
    """

    def get_status():
        # Update status of all runs
        Session = sessionmaker()
        runs = fetch_runs_of_experiment(Session, experiment_name)
        Session.close()
        for run in runs:
            if run.runner == "local":
                execution_handler = LocalMachineExecutionHandler(
                        sessionmaker, run.id, only_check_status=True)
            elif run.runner == "htcondor":
                execution_handler = HTCondorExecutionHandler(
                        sessionmaker, run.id)
            elif run.runner == "slurm":
                execution_handler = SlurmExecutionHandler(
                        sessionmaker, run.id)
            try:
                run.status = execution_handler.check_status()
                if "100" not in run.progress.strip():
                    progress = execution_handler.check_progress()
                    if progress is not None:
                        logger.debug(f"Progress of run {run.id}: {progress}")
                        Session = sessionmaker()
                        update_run_progress(Session, run.id, progress)
                        Session.close()

            except Exception as e:
                logger.error(e)
                run.status = "unknown"

        # Fetch all runs again
        Session = sessionmaker()
        runs = fetch_runs_of_experiment(Session, experiment_name)
        Session.close()

        # Put running runs at the top
        runs = sorted(runs, key=lambda x: x.status == "running",
                      reverse=True)

        return runs

    if animation:
        console = Console()
        with console.status(
                "[bold green]Fetching runs...", spinner="dots"):
            runs = get_status()
    else:
        runs = get_status()

    return runs


def command_status(experiment_name: str,
                   live: bool = False):
    """Show information about an experiment.

    :param experiment_name: Name of the experiment
    :type experiment_name: str

    :param live: If True, the command will be executed in live mode
    :type live: bool
    """
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    experiment_id = find_experiment_id(Session, experiment_name)
    if experiment_id == -1:
        logger.error("Experiment does not exist")
        Session.close_all()
        return

    experiment = Session.query(Base.classes.experiments).filter_by(
            name=experiment_name).first()
    number_runs = count_number_runs_experiment(Session, experiment_name)
    datasets_names = [dataset.name for dataset in
                      fetch_datasets_of_experiment(Session, experiment_name)]
    tags = fetch_tags_of_experiment(Session, experiment_name)
    rich.print(f"[bold]{EXPERIMENT_NAME} Name[/bold]: {experiment.name}")
    rich.print(f"[bold]{EXPERIMENT_DESCRIPTION} Description[/bold]: "
               f"{experiment.description}")
    rich.print(f"[bold]{EXPERIMENT_PATH} Path[/bold]: {experiment.path}")
    rich.print(f"[bold]{EXPERIMENT_DATASETS} Datasets[/bold]:"
               f"{datasets_names}")
    rich.print(f"[bold]{EXPERIMENT_EXECUTABLE} Executable[/bold]: "
               f"{experiment.executable}")
    rich.print(f"[bold]{EXPERIMENT_EXECUTE_COMMAND} Execute command[/bold]: "
               f"{experiment.executable_command}")
    rich.print(f"[bold]{EXPERIMENT_RUNS} Number of runs[/bold]: {number_runs}")
    rich.print(f"[bold]{EXPERIMENT_TAGS} Tags[/bold]: {tags}")

    # Get actions associated with the experiment
    actions = fetch_actions_of_experiment(Session, experiment_name)
    if len(actions) >= 1:
        rich.print(f"[bold]{EXPERIMENT_ACTION} Actions[/bold]:")
        for action in actions:
            rich.print(f"  - [bold]{action.name}[/bold]: {action.description}")

    # Show runs associated with the experiment as a list
    rich.print(f"\n[bold]{EXPERIMENT_RUNS} Runs[/bold]:")

    if not live:
        runs = fetch_status_runs(session, experiment_name)
        grid = generate_grid_runs(session, runs)
        rich.print(grid)

    else:

        runs = fetch_status_runs(session, experiment_name)
        with Live(generate_grid_runs(session, runs),
                  refresh_per_second=EXPERIMENT_LIVE_REFRESH,
                  screen=True) as live:

            try:
                while True:
                    time.sleep(EXPERIMENT_LIVE_REFRESH)
                    runs = fetch_status_runs(session, experiment_name)
                    live.update(generate_grid_runs(session, runs))
            except KeyboardInterrupt:
                return
