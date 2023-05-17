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
from ..core.database import (
     open_database,
     add_run,
     RunOfAnExperiment,
     find_experiment_id,
     delete_run_from_id
    )
from ..core.runs import (
        parse_executionhandler, RunExecutionHandler,
        LocalMachineExecutionHandler)
from ..utils.logging import setup_logger

logger = setup_logger()


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
            info = execution_handler(Session, run.id).parse_yaml_file()

            # Kill main pid
            try:
                os.kill(info['main_pid'], signal.SIGTERM)
                wait_finish = True
            except ProcessLookupError:
                logger.debug(f"Process {info['main_pid']} not found")

            logger.info(
                    f"Run {run_id} of experiment {experiment_name} canceled")

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
        delete_run_from_id(session, run_id)
        logger.info(f"Run {run_id} of experiment {experiment_name} deleted")
    else:
        logger.info(
                f"Run {run_id} of experiment {experiment_name} not deleted")
        return

    # Close the database
    session.close()


def parse_positional_optional_arguments(
        parameters: list, pos_shift: int = 0) -> dict:
    """Parse the positional and optional arguments depending on
    if there is -- or not in the string of the parameters.

    :param parameters: The parameters to parse.
    :type parameters: list

    :param pos_shift: The shift of the positional arguments.
    :type pos_shift: int

    :return: A dictionary of the parsed parameters.
    :rtype: dict
    """

    # Parse the string of the group by splitting
    # it with the space character
    i = 0
    pos_number = pos_shift
    result = {}
    while i < len(parameters):
        if parameters[i].startswith("--"):
            result[parameters[i]] = parameters[i+1]
            i += 2
        else:
            result[f"pos_{pos_number}"] = parameters[i]
            pos_number += 1
            i += 1

    return result


def parse_args_cli(ctx: click.Context, groups_of_parameters: list,
                   runner_params_to_get: list =
                   ["--n_threads", "--submit_template"]) -> tuple:
    """Parse the arguments of the CLI and return a list of dictionary of them.
    The arguments are parsed from the context of the CLI and the groups
    of parameters.


    :param ctx: The context of the CLI.
    :type ctx: click.Context

    :param groups_of_parameters: The groups of parameters to parse.
    :type groups_of_parameters: list

    :param runner_params_to_get: The parameters of the runner to get.
    :type runner_params_to_get: list

    :return: A tuple of the parsed parameters and the runner parameters.
    :rtype: tuple
    """

    # Get the arguments from the context
    fixed_args = parse_positional_optional_arguments(ctx.args)

    # Remove the runner params in a separate list
    runner_params = {}
    for param in runner_params_to_get:
        if param in fixed_args:
            runner_params[param] = fixed_args[param]
            del fixed_args[param]

    # Parse the arguments of the groups of parameters
    if len(groups_of_parameters) == 0:
        parsed_parameters = [fixed_args]
    else:
        parsed_parameters = []
        for group in groups_of_parameters:
            # Find the shift needed in the key of positional
            # arguments
            pos_shift = 0
            for key in fixed_args.keys():
                if key.startswith("pos_"):
                    pos_shift = max(pos_shift, int(key[-1]))

            # Parse the string of the group by splitting
            # it with the space character
            group = group.split(" ")
            varying_parameters = \
                parse_positional_optional_arguments(
                    group,
                    pos_shift=int(pos_shift)+1
                )
            parsed_parameters.append({**fixed_args, **varying_parameters})

    return parsed_parameters, runner_params


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
                          runner: str,
                          storage_path: str,
                          description: str = "",
                          tags: list = []) -> int:
    """Launch the run of the experiment with designated runner.


    :param experiment_name: The name of the experiment to run.
    :type experiment_name: str

    :param ctx: The context of the CLI.
    :type ctx: click.Context

    :param groups_of_parameters: The groups of parameters to parse.
    :type groups_of_parameters: list

    :param runner: The runner to use for the run.
    :type runner: str

    :param storage_path: The path to the storage.
    :type storage_path: str

    :param description: The description of the run.
    :type description: str

    :param tags: The tags of the run.
    :type tags: list

    :return: The id of the run.
    :rtype: int
    """

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
        parse_args_cli(ctx, groups_of_parameters)

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

    if "--n_threads" not in runner_params:
        runner_params["--n_threads"] = 1

    # Create the execution handler
    if runner == "local":
        execution_handler = LocalMachineExecutionHandler(
                database_sessionmaker=Session,
                run_id=run_id,
                n_threads=int(runner_params['--n_threads'])
        )

    else:
        raise NotImplementedError(f"Runner {runner} is not implemented yet.")

    # Setting up the run
    logger.info("Setting up the run...")
    execution_handler.setUp()

    # Setting singla handler for eventual cancel/halt/resume
    signal.signal(signal.SIGTERM,
                  handler=partial(
                      signals_experiment_handler, execution_handler))

    # Run the experiment
    logger.info("Running the experiment...")
    execution_handler.run_experiment()
