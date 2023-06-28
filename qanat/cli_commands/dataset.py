# ========================================
# FileName: dataset.py
# Date: 03 mai 2023 - 11:13
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: CLI commands for datasets
# =========================================


import os
import rich
from rich import prompt
from ..utils.logging import setup_logger
from ..utils.parsing import parse_dataset_file
from ..core.database import (
    open_database, add_dataset, find_dataset_id,
    fetch_tags_of_dataset, delete_dataset,
    add_tag, find_tag_id, Dataset)
from ._constants import (
    DATASET_NAME, DATASET_DESCRIPTION, DATASET_PATH,
    DATASET_TAGS, DATASET_ID)
from rich.table import Table

logger = setup_logger()


# --------------------------------------------------------
# Command Add
# --------------------------------------------------------
def command_add_prompt():
    """Add dataset from prompt"""

    Prompt = prompt.Prompt

    logger.info("Dataset adding prompt")
    rich.print("Please enter the following information:")
    name = Prompt.ask(f"{DATASET_NAME} Name of the dataset")
    description = Prompt.ask(
            f"{DATASET_DESCRIPTION} Description of the dataset")
    path = Prompt.ask(f"{DATASET_PATH} Path to the dataset")

    while not os.path.exists(path):
        logger.error("Path does not exist")
        path = Prompt.ask(f"{DATASET_PATH} Path to the dataset")

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    if find_dataset_id(Session, name) != -1:
        logger.error("Dataset already exists")
        return

    tags = Prompt.ask(
            f"{DATASET_TAGS} Tags of the dataset separated by a comma",
            default="").strip().split(",")
    if tags == [""]:
        tags = []

    for tag in tags:
        if find_tag_id(Session, tag) == -1:
            logger.info(f"Tag {tag} does not exist")
            logger.info("Creating tag")
            tag_description = Prompt.ask(
                f'{DATASET_DESCRIPTION} Please add a description '
                f'for the tag [bold yellow]{tag}[/bold yellow]]',
                default="")
            add_tag(Session, tag, tag_description)

    rich.print("Please confirm the following information:")
    rich.print(f"[bold]Name[/bold]: {name}")
    rich.print(f"[bold]Description[/bold]: {description}")
    rich.print(f"[bold]Path[/bold]: {path}")
    rich.print(f"[bold]Tags[/bold]: {tags}")

    if prompt.Confirm.ask("Do you want to add this dataset?"):
        logger.info("Adding dataset to database")
        add_dataset(Session, path, name, description, tags)
        logger.info("Dataset added successfully")

    Session.close_all()


def command_add_from_file(dataset_file: str,
                     confirm: bool = True):
    """Add dataset from yaml file

    :param dataset_file: path to the yaml file
    :type dataset_file: str

    :param confirm: ask for confirmation before adding the dataset
    :type confirm: bool
    """

    if not os.path.exists(dataset_file):
        logger.error("File does not exist")
        return

    # Parse dataset file into a dict
    dataset = parse_dataset_file(dataset_file)

    # Check if dataset already exists
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    if find_dataset_id(Session, dataset["name"]) != -1:
        logger.error("Dataset already exists")
        return

    # Add dataset if confirm
    if confirm:
        rich.print("Please confirm the following information:")
        rich.print(f"[bold]{DATASET_NAME} Name[/bold]: {dataset['name']}")
        rich.print(f"[bold]{DATASET_DESCRIPTION} Description[/bold]: "
                   f"{dataset['description']}")
        rich.print(f"[bold]{DATASET_PATH} Path[/bold]: {dataset['path']}")
        rich.print(f"[bold]{DATASET_TAGS} Tags[/bold]: {dataset['tags']}")
        if not prompt.Confirm.ask("Do you want to add this dataset?"):
            return

    # Check if tags exist and add them if not
    for tag in dataset["tags"]:
        if find_tag_id(Session, tag) == -1:
            add_tag(Session, tag, "")

    # Add dataset to database
    add_dataset(Session, dataset['path'], dataset['name'],
                dataset['description'], dataset['tags'])
    logger.info("Dataset added successfully")
    Session.close_all()


# --------------------------------------------------------
# Command Update
# --------------------------------------------------------
def command_update(dataset_name: str,
                   confirm: bool = True):
    """Update dataset information

    :param dataset_name: name of the dataset
    :type dataset_name: str

    :param confirm: ask for confirmation before updating the dataset
    :type confirm: bool
    """

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    # Check if dataset exists
    if find_dataset_id(Session, dataset_name) == -1:
        logger.error("Dataset does not exist")
        return

    # Fetch dataset
    dataset = Session.query(Dataset).filter_by(
            name=dataset_name).first()

    # Fetch tags
    tags = fetch_tags_of_dataset(Session, dataset.id)

    # Print dataset information
    rich.print(f"[bold]{DATASET_NAME} Name[/bold]: {dataset.name}")
    rich.print(f"[bold]{DATASET_DESCRIPTION} Description[/bold]: "
               f"{dataset.description}")
    rich.print(f"[bold]{DATASET_PATH} Path[/bold]: {dataset.path}")
    rich.print(f"[bold]{DATASET_TAGS} Tags[/bold]: {tags}")

    # Ask for which information to update
    choices = [
        "Name",
        "Description",
        "Path",
        "Exit"
    ]
    choices_no = [str(i) for i in range(1, len(choices) + 1)]
    rich.print("Which information do you want to update?")
    for i, choice in enumerate(choices):
        rich.print(f"[bold]{i + 1}[/bold]: {choice}")

    Prompt = prompt.Prompt
    choice = Prompt.ask("Please enter the number of your choice",
                        choices=choices_no)

    # TODO: Update tags
    while choice != choices_no[-1]:
        if choice == choices_no[0]:
            name = Prompt.ask(f"{DATASET_NAME} Name")
            dataset.name = name
        elif choice == choices_no[1]:
            description = Prompt.ask(f"{DATASET_DESCRIPTION} Description")
            dataset.description = description
        elif choice == choices_no[2]:
            path = Prompt.ask(f"{DATASET_PATH} Path")
            dataset.path = path
        else:
            logger.error("Invalid choice")

        choice = Prompt.ask("Please enter the number of your choice",
                            choices=choices_no)

    # Update dataset if changes were made
    if Session.dirty:
        if confirm:
            rich.print("Please confirm the following information:")
            rich.print(f"[bold]{DATASET_NAME} Name[/bold]: {dataset.name}")
            rich.print(f"[bold]{DATASET_DESCRIPTION} Description[/bold]: "
                       f"{dataset.description}")
            rich.print(f"[bold]{DATASET_PATH} Path[/bold]: {dataset.path}")
            rich.print(f"[bold]{DATASET_TAGS} Tags[/bold]: {tags}")
            if not prompt.Confirm.ask("Do you want to update this dataset?"):
                return

        Session.commit()
        logger.info("Dataset updated successfully")
    Session.close_all()


# --------------------------------------------------------
# Command Delete
# --------------------------------------------------------
def command_delete(dataset_name: str):
    """Delete dataset from database"""

    engine, Base, session = open_database('.qanat/database.db')
    Session = session()

    dataset_id = find_dataset_id(Session, dataset_name)
    if dataset_id == -1:
        logger.error("Dataset does not exist")
        Session.close_all()
        return

    # Fetch dataset info
    description, path = Session.query(
            Base.classes.datasets.description,
            Base.classes.datasets.path).filter_by(id=dataset_id).first()

    # Fetch experiments_id that use this dataset
    experiments_datasets = [element.experiment_id for element in
                            Session.query(
                                Base.classes.datasets_experiments).filter_by(
                                    dataset_id=dataset_id).all()]

    experiments = [experiment.name for experiment in
                   Session.query(Base.classes.experiments).filter(
                       Base.classes.experiments.id.in_(
                           experiments_datasets)).all()]

    rich.print("Please confirm the following information:")
    rich.print(f"[bold]{DATASET_NAME} Name[/bold]: {dataset_name}")
    rich.print(f"[bold]{DATASET_DESCRIPTION} Description[/bold]: "
               f"{description}")
    rich.print(f"[bold]{DATASET_PATH} Path[/bold]: {path}")

    if prompt.Confirm.ask("Do you want to delete this dataset?\n"
                          "The link between experiments "
                          f"[bold]{experiments}[/bold] and "
                          "this dataset will be deleted as well.\n"):
        logger.info("Deleting dataset from database")
        delete_dataset(Session, dataset_name)
        logger.info("Dataset deleted successfully")

    Session.close_all()


# --------------------------------------------------------
# Command List
# --------------------------------------------------------
def command_list():
    """List all datasets in the database"""
    engine, Base, session = open_database('.qanat/database.db')
    Session = session()
    datasets = Session.query(Base.classes.datasets).all()

    rich.print(f"Total number of datasets: [bold]{len(datasets)}[/bold]")
    grid = Table.grid(expand=False, padding=(0, 4))
    grid.add_column(justify="left", header="ID")
    grid.add_column(justify="left", header="Name")
    grid.add_column(justify="left", header="Description")
    grid.add_column(justify="left", header="Path")
    grid.add_column(justify="right", header="Tags", style="bold")
    grid.add_row("[bold]ID[/bold]", "[bold]Name[/bold]",
                 "[bold]Description[/bold]", "[bold]Path[/bold]",
                 "[bold]Tags[/bold]")
    for dataset in datasets:
        tags = fetch_tags_of_dataset(Session, dataset.name)
        if len(tags) >= 1:
            tags = f"{DATASET_TAGS} " +\
                   f", {DATASET_TAGS} ".join(tags)
        else:
            tags = ""

        grid.add_row(f"{DATASET_ID} {dataset.id}",
                     f"{DATASET_NAME} {dataset.name}",
                     f"{DATASET_DESCRIPTION} {dataset.description}",
                     f"{DATASET_PATH} {dataset.path}",
                     f"{tags}")
    rich.print(grid)
