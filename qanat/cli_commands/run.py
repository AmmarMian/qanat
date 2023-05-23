# ========================================
# FileName: run.py
# Date: 09 mai 2023 - 14:38
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Managin run subcommand of
#        qanat experiment
# =========================================

import os
import time
import signal
import yaml
import rich_click as click
import rich
import git
from sqlalchemy import func
from functools import partial
from ._constants import (
        get_run_status_emoji,
        RUN_LAUNCH_DATE, PARAMETERS,
        ID, DESCRIPTION, PATH, TAGS,
        STATUS, RUNNER
)
from ..core.database import (
     open_database,
     add_run,
     RunOfAnExperiment,
     find_experiment_id,
     delete_run_from_id,
     fetch_tags_of_run,
     fetch_groupofparameters_of_run
    )
from ..core.runs import (
        parse_executionhandler, RunExecutionHandler,
        LocalMachineExecutionHandler, HTCondorExecutionHandler)
from ..utils.logging import setup_logger
from ..utils.parsing import (
    parse_args_cli
)

logger = setup_logger()


def explore_run(experiment_name: str, run_id: int):
    """Explore a run of an experiment.

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run_id: The id of the run to explore.
    :type run_id: int
    """
    # Opening database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Find the experiment id
    experiment_id = find_experiment_id(session, experiment_name)
    if experiment_id == -1:
        logger.error("Experiment does not exist")
        return

    # Check if run exists
    run = session.query(RunOfAnExperiment).filter_by(
        experiment_id=experiment_id, id=run_id).first()
    if run is None:
        logger.error(
                f"Run {run_id} of experiment {experiment_name} "
                "does not exist")
        return

    # Show run informations
    run = session.query(RunOfAnExperiment).filter_by(
        experiment_id=experiment_id, id=run_id).first()

    # Get Tags of the run
    tags = fetch_tags_of_run(session, run_id)

    # Get GroupOfParameters of the run
    groupofparameters = fetch_groupofparameters_of_run(session, run_id)

    rich.print(f"Run [bold red]{run_id}[/bold red] of experiment "
               f"[bold yellow]{experiment_name}[/bold yellow] informations:")
    rich.print(f"  - {ID} id: {run.id}")
    rich.print(f"  - {DESCRIPTION} description: {run.description}")
    rich.print(f"  - {TAGS} tags: {tags}")
    rich.print(f"  - {RUNNER} runner: {run.runner}")
    rich.print(f"  - {PATH} path: {run.storage_path}")
    rich.print(f"  - {STATUS} status: {get_run_status_emoji(run.status)}")
    rich.print(f"  - {RUN_LAUNCH_DATE} start time: {run.launched}")
    rich.print(f"  - {RUN_LAUNCH_DATE} end time: {run.finished}")

    # Show group of parameters
    grid = rich.table.Table.grid(padding=(0, 4))
    grid.add_column("Group", justify="center", style="cyan")
    grid.add_column("Parameters", justify="left", style="magenta")
    grid.add_column("Repertory", justify="left", style="green")
    grid.add_row("Group", "Parameters", 'Repertory')
    for i, group in enumerate(groupofparameters):
        string_parameters = ""
        if len(groupofparameters) == 1:
            repertory = run.storage_path
        else:
            repertory = os.path.join(run.storage_path, f"group_{i}")
        for key, value in group.values.items():
            string_parameters += f"{key} {value}"
        grid.add_row(f"{i}", string_parameters, repertory)
    rich.print(f"  - {PARAMETERS} Parameters:")
    rich.print(grid)


def delete_run(experiment_name: str, run_id: int):
    """Delete a run from the database.

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run_id: The id of the run to delete.
    :type run_id: int
    """

    # Opening database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Find the experiment id
    experiment_id = find_experiment_id(session, experiment_name)
    if experiment_id == -1:
        logger.error("Experiment does not exist")
        return

    # Check if run exists
    run = session.query(RunOfAnExperiment).filter_by(
        experiment_id=experiment_id, id=run_id).first()
    if run is None:
        logger.error(
                f"Run {run_id} of experiment {experiment_name} "
                "does not exist")
        return

    # Delete the run
    logger.info(f"Deleting run {run_id} of experiment {experiment_name}")
    # Show run informations
    run = session.query(RunOfAnExperiment).filter_by(
        experiment_id=experiment_id, id=run_id).first()
    logger.info(f"Run {run_id} of experiment {experiment_name} informations:")
    logger.info(f"  - id: {run.id}")
    logger.info(f"  - status {run.status}")
    logger.info(f"  - runner: {run.runner}")
    logger.info(f"  - experiment_id: {run.experiment_id}")
    logger.info(f"  - description: {run.description}")
    logger.info(f"  - start_time: {run.launched}")
    logger.info(f"  - end_time: {run.finished}")
    logger.info(f"  - status: {run.status}")
    logger.info(f"  - storage_path {run.storage_path}")
    if rich.prompt.Confirm.ask("Are you sure?"):

        # Cancel the run if running
        if run.status == "running":
            wait_finish = False

            # Get the execution handler
            execution_handler = parse_executionhandler(
                run.runner)

            # Cancel the run
            if run.runner == "local":
                # Since the main process is somewhere else, we need to
                # do stuff here.
                # TODO: try to integrate in execution_handler
                info = execution_handler(Session, run.id).parse_yaml_file()

                # Kill main pid
                try:
                    if 'main_pid' in info:
                        os.kill(info['main_pid'], signal.SIGTERM)
                        wait_finish = True
                except ProcessLookupError:
                    logger.debug(f"Process {info['main_pid']} not found")

                # Wait for signal that run has been canceled
                if wait_finish:
                    session.close()
                    console = rich.console.Console()
                    with console.status(
                            "[bold green]Waiting for run to finish gracefully..."):
                        cancel_done = False
                        while not cancel_done:
                            session = Session()
                            run = session.query(RunOfAnExperiment).filter_by(
                                experiment_id=experiment_id, id=run_id).first()
                            time.sleep(0.5)
                            cancel_done = run.status == "cancelled"
                            session.close()
                    # Close the database if not closed
                    if session.is_active:
                        session.close()
                    session = Session()

            else:
                execution_handler(Session, run.id).cancel_experiment()
                logger.info(
                        f"Run {run_id} of experiment {experiment_name} canceled")

        delete_run_from_id(session, run_id)
        logger.info(f"Run {run_id} of experiment {experiment_name} deleted")
    else:
        logger.info(
                f"Run {run_id} of experiment {experiment_name} not deleted")
        return

    # Close the database
    session.close()


def signals_experiment_handler(executionhandler: RunExecutionHandler,
                               signum, frame):
    """Handler of signals to a run of the experiment.

    :param executionhandler: The execution handler of the experiment.
    :type executionhandler: RunExecutionHandler

    :param signum: The signal number.
    :type signum: int

    :param frame: The frame.
    :type frame: frame
    """

    if signum == signal.SIGTERM:
        executionhandler.cancel_experiment()
    else:
        raise ValueError(f"Signal {signum} not handled")


def launch_run_experiment(experiment_name: str,
                          ctx: click.Context,
                          groups_of_parameters: list,
                          range_of_parameters: list,
                          runner: str,
                          storage_path: str,
                          description: str = "",
                          tags: list = [],
                          container_path: str = None) -> int:
    """Launch the run of the experiment with designated runner.


    :param experiment_name: The name of the experiment to run.
    :type experiment_name: str

    :param ctx: The context of the CLI.
    :type ctx: click.Context

    :param groups_of_parameters: The groups of parameters to parse.
    :type groups_of_parameters: list

    :param range_of_parameters: The range of parameters to parse.
    :type range_of_parameters: list

    :param runner: The runner to use for the run.
    :type runner: str

    :param storage_path: The path to the storage.
    :type storage_path: str

    :param description: The description of the run.
    :type description: str

    :param tags: The tags of the run.
    :type tags: list

    :param container_path: The path to the container.
    :type container_path: str

    :return: The id of the run.
    :rtype: int
    """

    if runner == 'htcondor':
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                import htcondor
            schedd = htcondor.Schedd()
            # check if the schedd is available
            schedd.xquery('true', [])

        except ImportError:
            logger.error(
                    "You need to install htcondor to use the htcondor runner.")
            return -1

        except htcondor.HTCondorLocateError:
            logger.error(
                    "The htcondor scheduler is not available. "
                    "Please check your configuration.")
            return -1

    if container_path is not None:
        if not os.path.exists(container_path):
            logger.error(f"Container {container_path} not found.")
            return -1

    # Opening database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Check if the experiment exists
    experiment_id = find_experiment_id(session, experiment_name)
    if experiment_id == -1:
        logger.error(f"Experiment {experiment_name} does not exist.")
        return -1

    # Check whether cwd is a git repository and committed
    repo = git.Repo('.')
    if repo.is_dirty() or len(repo.untracked_files) > 0:
        logger.error(
                "The repository is not clean. Please commit your changes.")
        # Show the changes in the repository
        logger.info("The following files have been modified:")
        for file in repo.git.diff(None, name_only=True).split("\n"):
            logger.info(file)

        # Show untracked files
        logger.info("The following files are untracked:")
        for file in repo.untracked_files:
            logger.info(file)

        if rich.prompt.Confirm.ask("Do you want me to commit the changes "
                                   "for you?",
                                   default=False):
            repo.git.add(".")
            commit_description = rich.prompt.Prompt.ask(
                    "Please enter a description for the commit")
            repo.git.commit("-m",
                            "Automatic commit before running experiment "
                            f"{experiment_name}: {commit_description}")
        else:
            return -1

    commit_sha = repo.head.object.hexsha

    # Get the parsed parameters
    parsed_parameters, runner_params = \
        parse_args_cli(ctx, groups_of_parameters,
                       range_of_parameters)

    # Check whether storage_path is not None
    if storage_path is None:
        # Get the storage path from the config.yaml
        with open(".qanat/config.yaml", "r") as f:
            config = yaml.safe_load(f)

        # Get las id of experiments in the database
        last_id = session.query(func.max(RunOfAnExperiment.id)).scalar()
        if last_id is None:
            last_id = 0
        storage_path = os.path.join(
                config["result_dir"],
                f"{experiment_name}/run_{last_id+1}"
        )

    # Create directories recursively if they do not exist
    if not os.path.exists(storage_path):
        os.makedirs(storage_path)
    else:
        logger.error("Something went wrong.")
        logger.error(f"Storage path {storage_path} already exists.")
        return -1

    # Create the run in the database
    if tags is None:
        tags = []
    run = add_run(
            session, experiment_name, storage_path,
            commit_sha, parsed_parameters, description,
            tags, runner, runner_params)
    run_id = run.id

    # Create the execution handler
    if runner == "local":
        if "--n_threads" not in runner_params:
            runner_params["--n_threads"] = 1
        execution_handler = LocalMachineExecutionHandler(
                database_sessionmaker=Session,
                run_id=run_id,
                n_threads=int(runner_params['--n_threads']),
                container_path=container_path
        )

    elif runner == "htcondor":
        # Check whether the submit_template is specified
        if "--submit_template" not in runner_params:
            # Take by default the submit_template in config.yaml
            with open(".qanat/config.yaml", "r") as f:
                config = yaml.safe_load(f)
            submit_info = config["htcondor"]["default"]

        else:
            # Check if submit_template is a file
            if os.path.isfile(runner_params["--submit_template"]):
                # load yaml
                with open(runner_params["--submit_template"], "r") as f:
                    submit_info = yaml.safe_load(f)
            else:
                # Read from config file
                with open(".qanat/config.yaml", "r") as f:
                    config = yaml.safe_load(f)
                if runner_params["--submit_template"] in \
                        config['htcondor']:
                    submit_info = config["htcondor"][
                        runner_params["--submit_template"]]
                else:
                    raise ValueError("Submit template "
                                     f"{runner_params['--submit_template']} "
                                     "not found in config.yaml nor is a file")

        execution_handler = HTCondorExecutionHandler(
                database_sessionmaker=Session,
                run_id=run_id,
                htcondor_submit_options=submit_info,
                container_path=container_path)

    else:
        raise NotImplementedError(f"Runner {runner} is not implemented yet.")

    # Setting up the run
    logger.info("Setting up the run...")
    execution_handler.setUp()

    # Setting signal handler for eventual cancel/halt/resume
    signal.signal(signal.SIGTERM,
                  handler=partial(
                      signals_experiment_handler, execution_handler))

    # Run the experiment
    logger.info("Running the experiment...")
    execution_handler.run_experiment()
