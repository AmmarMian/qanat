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
from ..core.database import (
    open_database, add_dataset, find_dataset_id,
    fetch_tags_of_dataset)
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

