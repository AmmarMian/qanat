# ========================================
# FileName: status.py
# Date: 03 mai 2023 - 14:40
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Status cli command
# =========================================


from rich.console import Console
from ..utils.logging import setup_logger
from ..utils.misc import get_size
from ..core.database import open_database
from ._constants import (
        STATUS_DATASET, STATUS_EXPERIMENT, STATUS_RUN,
        STATUS_DISKSIZE, STATUS_RUNNING)
import yaml
logger = setup_logger()


def command_status():
    """Status command"""

    console = Console()
    with console.status(
            "[bold green]Computing status...", spinner="dots"):
        # Compute number of experiments
        engine, Base, session = open_database('.qanat/database.db')
        Session = session()
        number_experiments = Session.query(Base.classes.experiments).count()

        # Compute number of datasets
        number_datasets = Session.query(Base.classes.datasets).count()

        # Compute number of total runs
        number_runs = Session.query(Base.classes.runs_of_experiments).count()
        number_run_running = Session.query(
                Base.classes.runs_of_experiments).filter_by(
            status="running").count()

        # Measure disk size of results directory
        with open('.qanat/config.yaml') as file:
            config = yaml.load(file, Loader=yaml.FullLoader)
        results_path = config['result_dir']
        results_size = get_size(results_path)/1000000

        # Print status
        # TODO: Rich layout for status
        console.print(
                f"{STATUS_EXPERIMENT} [bold]Number of experiments[/bold]: "
                f"{number_experiments}")
        console.print(
                f"{STATUS_DATASET} [bold]Number of datasets[/bold]: "
                f"{number_datasets}")
        console.print(
                f"{STATUS_RUN} [bold]Number of runs[/bold]: {number_runs}")
        console.print(
                f"{STATUS_RUNNING} [bold]Number of running runs[/bold]: "
                f"{number_run_running}")
        console.print(
                f"{STATUS_DISKSIZE} [bold]Size of results directory[/bold]: "
                f"{results_size} MB")
