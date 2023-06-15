# ========================================
# FileName: run.py
# Date: 09 mai 2023 - 14:38
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Managin run subcommand of
#        qanat experiment
# =========================================

import sys
import os
import pathlib
import time
import signal
import sqlalchemy
import yaml
import rich_click as click
import rich
from rich.prompt import Confirm
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape
from rich.tree import Tree
import git
import subprocess
from simple_term_menu import TerminalMenu
from sqlalchemy import func
from functools import partial
from ._constants import (
        get_run_status_emoji,
        RUN_LAUNCH_DATE, PARAMETERS,
        ID, DESCRIPTION, PATH, TAGS,
        STATUS, RUNNER, COMMIT, RUN_METRIC,
        CONTAINER, PROGRESS, COMMENT
)
from ..core.database import (
     open_database,
     add_run,
     RunOfAnExperiment,
     find_experiment_id,
     delete_run_from_id,
     fetch_tags_of_run,
     fetch_groupofparameters_of_run,
     fetch_runs_of_experiment,
     fetch_actions_of_experiment
    )
from ..core.runs import (
        parse_executionhandler, RunExecutionHandler,
        LocalMachineExecutionHandler, HTCondorExecutionHandler)
from ..utils.logging import setup_logger
from ..utils.parsing import (
    parse_args_cli, parse_positional_optional_arguments,
    parse_args_string, parse_yaml_command_file
)
from .experiment import command_action
from ..utils.misc import walk_directory

logger = setup_logger()


# ==============================
# Run comments stuff
# ==============================
def create_comment_file(session: sqlalchemy.orm.Session,
                        experiment_name: str,
                        run: RunOfAnExperiment) -> str:
    """Create a comment file for a run.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run: The run to create the comment file for.
    :type run: RunOfAnExperiment

    :return: The path to the comment file.
    :rtype: str
    """

    comment_file = os.path.join(run.storage_path, "comment.md")
    with open(comment_file, 'w') as f:
        f.write(
                f"# Comment for run {run.id} of "
                f"experiment \"{experiment_name}\"\n"
        )

        # Horizontal line
        f.write("\n---\n\n")

        f.write(f"Launched on {run.launched}\n")
        f.write(f"Tags: {' '.join(fetch_tags_of_run(session, run.id))}\n")
        f.write(f"Description: {run.description}\n")
        if run.finished is not None:
            f.write(f"Finished on {run.finished}\n")
        if run.metric is not None:
            f.write(f"Metric: {run.metric}\n")

        # Horizontal line
        f.write("\n---\n\n")

    # Add comment file to database
    run.comment_file = comment_file
    session.commit()

    return comment_file


def edit_comment_file(comment_file: str):
    """Edit a comment file.

    :param comment_file: The path to the comment file.
    :type comment_file: str
    """
    with open('.qanat/config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    if 'default_editor' in config or config['default_editor'] is not None:
        editor = config['default_editor']
    else:
        logger.error("No default editor found in config file")
        logger.error("Before proceeding, please specify a default_editor "
                     "in the config file: .qanat/config.yaml")
        sys.exit(1)
    subprocess.call([editor, comment_file])


def command_comment(experiment_name: str, run_id: int):
    """Command comment.

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run_id: The id of the run.
    :type run_id: int
    """
    # Open database
    engine, Base, Session = open_database(".qanat/database.db")
    session = Session()

    # Check if experiment exists
    experiment_id = find_experiment_id(session, experiment_name)
    if experiment_id == -1:
        logger.error(f"Experiment {experiment_name} does not exist")
        return

    # Fetch run
    run = session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).first()

    if run is None:
        logger.error(f"Run {run_id} does not exist")
        return

    # Check if run belongs to experiment
    if run.experiment_id != experiment_id:
        logger.error(f"Run {run_id} does not belong to experiment "
                     f"{experiment_name}")
        return

    # Create comment file if does not exist
    comment_file = os.path.join(run.storage_path, "comment.md")
    if not os.path.exists(comment_file):
        logger.info(f'Creating comment file for run {run_id}')
        comment_file = create_comment_file(session, experiment_name, run)
    session.close()

    # Edit comment file
    edit_comment_file(comment_file)


# ==============================
# Exploring runs stuff
# ==============================
def create_menu_entry(
        session: sqlalchemy.orm.Session, run: RunOfAnExperiment) -> str:
    """Create a menu entry for a run.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param run: The run to create the menu entry for.
    :type run: RunOfAnExperiment

    :return: The menu entry.
    :rtype: str
    """
    return f"{run.id} - {run.launched} - {run.status} - " + \
           " ".join(fetch_tags_of_run(session, run.id))


def parse_menu_entry(menu_entry: str) -> int:
    """Parse a menu entry to get the run id.

    :param menu_entry: The menu entry.
    :type menu_entry: str

    :return: The run id.
    :rtype: int
    """
    return int(menu_entry.split("-")[0].strip())


def run_explore_menu(session: sqlalchemy.orm.Session, experiment_name: str,
                     run_id: int):
    """Display a menu on run explore command.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run_id: The id of the run.
    :type run_id: int
    """

    # Fetch run
    run = session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).first()

    # Display menu
    menu_entries = [
            "[a] Show output(s)",
            "[b] Show error(s)",
            "[c] Show parameters",
            "[d] Show comment",
            "[e] Explore run directory"]

    if run.runner == 'htcondor':
        menu_entries.append(
                f"[{chr(ord('a')+len(menu_entries))}] Show HTCondor log(s)")

    # Fetch actions of experiment
    actions = fetch_actions_of_experiment(session, experiment_name)

    # Add delete run to menu
    menu_entries.append(f"[{chr(ord('a')+len(menu_entries))}] Delete run")

    # Add actions to menu
    for action in actions:
        menu_entries.append(
                f"[{chr(ord('a')+len(menu_entries))}] Action: {action.name}")

    # Preview of the menu
    def preview_command(menu_entry):
        if menu_entry == "Show output(s)":
            return 'Show output(s) of the run with less'
        elif menu_entry == "Show error(s)":
            return 'Show error(s) of the run with less'
        elif menu_entry == "Show parameters":
            return 'Print parameters used for the run'
        elif menu_entry == "Show comment":
            return 'Show comment of the run'
        elif menu_entry == "Explore run directory":
            return 'Explore run directory contents'
        elif menu_entry == "Show HTCondor log(s)":
            return 'Show HTCondor log(s) of the run with less'
        elif menu_entry == "Delete run":
            return 'Delete the run'
        elif menu_entry.startswith("Action:"):
            action_name = menu_entry.split(':')[1].strip()
            action = None
            for action in actions:
                if action.name == action_name:
                    break
            description = action.description if action is not None else ""
            return f"Run action {menu_entry.split(':')[1].strip()}:" \
                   f" {description}"
        else:
            return menu_entry

    # Create menu
    while True:
        menu = TerminalMenu(menu_entries, title=f"Run {run_id} of experiment "
                            f"{experiment_name} - Explore menu",
                            preview_command=preview_command)
        choice = menu.show()
        if choice is None:
            break
        res = parse_choice_explore_menu(session, experiment_name, run, actions,
                                        menu_entries[choice])
        if res == -1:
            break


def parse_choice_explore_menu(session: sqlalchemy.orm.Session,
                              experiment_name: str, run: RunOfAnExperiment,
                              actions: list, menu_entry: str):
    """Parse the choice of the explore menu.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run: The run.
    :type run: RunOfAnExperiment

    :param action: The list of actions.
    :type action: list

    :param menu_entry: The menu entry.
    :type menu_entry: str
    """

    menu_entry = menu_entry.strip().split(']')[1].strip()

    # Show output(s)
    if menu_entry == "Show output(s)":
        logger.info(f"Show output(s) of run {run.id}")
        storage_path = run.storage_path

        # List subdirectories
        subdirectories = [x for x in os.listdir(storage_path)
                          if os.path.isdir(os.path.join(storage_path,x))]
        if len(subdirectories) == 0:
            wildcard = f"{storage_path}/stdout.txt"
        else:
            wildcard = f"{storage_path}/**/stdout.txt"
        subprocess.run(f"less {wildcard}", shell=True)

    # Show error(s)
    elif menu_entry == "Show error(s)":
        logger.info(f"Show error(s) of run {run.id}")
        storage_path = run.storage_path
        subdirectories = [x for x in os.listdir(storage_path)
                          if os.path.isdir(os.path.join(storage_path,x))]
        if len(subdirectories) == 0:
            wildcard = f"{storage_path}/stderr.txt"
        else:
            wildcard = f"{storage_path}/**/stderr.txt"
        subprocess.run(f"less {wildcard}", shell=True)

    # Show parameters
    elif menu_entry == "Show parameters":
        groupofparameters = fetch_groupofparameters_of_run(session, run.id)

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
                string_parameters += f"{key} {value} "
            grid.add_row(f"{i}", string_parameters, repertory)
        rich.print(f"  - {PARAMETERS} Parameters:")
        rich.print(grid)

    # Show comment
    elif menu_entry == "Show comment":
        if run.comment_file is None or not os.path.exists(run.comment_file):
            if Confirm.ask("Comment file does not exist. Create it?"):
                command_comment(experiment_name, run.id)
                run.comment_file = os.path.join(
                    run.storage_path, 'comment.md')
            else:
                return
        console = Console()
        with open(run.comment_file, 'r') as f:
            comment = f.read()
        console.print('\n')
        console.print(Markdown(comment))
        console.print('\n')

    # Explore run directory
    elif menu_entry == "Explore run directory":
        result_directory = pathlib.Path(run.storage_path)
        tree = Tree(
            f"[bold blue]:open_file_folder: "
            f"[link file://{result_directory}]{escape(result_directory.name)}",
            guide_style="bold bright_blue")
        walk_directory(result_directory, tree)
        rich.print(tree)

    # Show HTCondor log(s)
    elif menu_entry == "Show HTCondor log(s)":
        logger.info(f"Show HTCondor log(s) of run {run.id}")
        storage_path = run.storage_path
        subdirectories = [x for x in os.listdir(storage_path)
                          if os.path.isdir(os.path.join(storage_path, x))]
        if len(subdirectories) == 0:
            wildcard = f"{storage_path}/log.txt"
        else:
            wildcard = f"{storage_path}/**/log.txt"
        subprocess.run(f"less {wildcard}", shell=True)

    # Delete run
    elif menu_entry == "Delete run":
        logger.info(f"Delete run {run.id}")
        delete_run(experiment_name, run.id)
        return -1

    # Run action
    elif menu_entry.startswith("Action:"):

        # Find action
        action_name = menu_entry.split(':')[1].strip()

        # Run action
        # TODO: pass arguments to action with input
        logger.info(f"Run action {action_name} on run {run.id}")
        group_no = rich.prompt.Prompt.ask(
                "Group number to run the action on "
                "(default execute at run storage level)",
                default=None, show_default=True)
        if group_no is not None:
            group_no = int(group_no)
        arguments = rich.prompt.Prompt.ask("Arguments to pass to the action",
                                           default=None, show_default=True)
        if arguments is not None:
            ctx = click.Context(click.Command(action_name), info_name=action_name)
            ctx.args = arguments.split(' ')
        else:
            ctx = None

        command_action(experiment_name, action_name,
                       run.id, ctx, group_no)

    else:
        raise ValueError(f"Choice {menu_entry} not recognized")


def run_selection_menu(session: sqlalchemy.orm.Session, experiment_name: str,
                       runs: list):
    """Display a menu to select a run. Preview as well, run information.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param runs: The list of runs to display.
    :type runs: list
    """

    if len(runs) == 0:
        rich.print(f"[red]No run found for experiment {experiment_name} "
                   "Corresponding to the current filter")
        return

    def output_command(menu_entry):
        """Output the command to run the run."""
        run_id = parse_menu_entry(menu_entry)
        # Find run in list with id
        run = None
        for run in runs:
            if run.id == run_id:
                break
        if run is None:
            return "Run not found"

        tags = fetch_tags_of_run(session, run.id)
        string_preview = f"Run ID: {run.id}\n" + \
                         f"Run Description: {run.description}\n" + \
                         f"Run launched: {run.launched}\n" + \
                         f"Run status: {run.status}\n" + \
                         f"Run progress: {run.progress}\n" + \
                         f"Run tags: {', '.join(tags)}\n" + \
                         f"Run commit: {run.commit_sha}\n" + \
                         f"Run runner: {run.runner}\n" + \
                         f"Run container: {run.container_path}\n"
        if run.finished is not None:
            string_preview += f"Run finished: {run.finished}\n"
        if run.metric is not None:
            string_preview += f"Run metric: {run.metric}\n"

        groupofparameters = fetch_groupofparameters_of_run(session, run.id)
        string_preview += "Run parameters: " + \
                          f"({len(groupofparameters)} group(s))\n"
        for parameter in groupofparameters:
            line = "    "
            for key, value in parameter.values.items():
                line += f"{key} {value} "
            string_preview += line + "\n"
        return string_preview

    # Create the menu
    menu_entries = [create_menu_entry(session, run) for run in runs]
    menu = TerminalMenu(menu_entries, preview_command=output_command,
                        title="Select a run",
                        preview_size=0.5)
    run_index = menu.show()
    if run_index is None:
        return
    explore_run(experiment_name, runs[run_index].id)


def search_runs(
        session: sqlalchemy.orm.Session, experiment_name: str, runs: list):
    """Search for runs.

    :param session: The database session.
    :type session: sqlalchemy.orm.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param runs: The list of runs to search from.
    :type runs: list
    """

    runs_selected = runs
    current_filter = {
        "tags": [],
        "description": [],
        "status": [],
        "runner": [],
        "commit": [],
        "parameters": []
            }
    while True:

        # Menu to ask for tag, description, status, runner, commit, parameters
        menu = TerminalMenu(["[a] Tag", "[b] Description", "[c] Status",
                             "[d] Runner", "[e] Commit", "[f] Parameters",
                             "[g] Menu with remaining runs",
                             "[h] Reset filters",
                             "[q] Exit"],
                            title="Search runs prompt")
        choice = menu.show()
        if choice is None or choice == 8:
            return

        prompt = rich.prompt.Prompt()

        # Tag
        if choice == 0:
            tags = prompt.ask("Tag to search for (separated by a comma)")
            tags = tags.strip().split(",")
            runs_selected = [run for run in runs_selected
                             if any(tag
                                    in fetch_tags_of_run(session, run.id)
                                    for tag in tags)]
            current_filter["tags"] = list(set(current_filter["tags"] + tags))

        # Description
        elif choice == 1:
            description = prompt.ask("Description to search for")
            runs_selected = [run for run in runs_selected
                             if description in run.description]
            current_filter["description"].append(description)

        # Status
        elif choice == 2:
            status = prompt.ask("Status to search for")
            runs_selected = [run for run in runs_selected
                             if status == run.status]
            current_filter["status"].append(status)

        # Runner
        elif choice == 3:
            runner = prompt.ask("Runner to search for")
            runs_selected = [run for run in runs_selected
                             if runner == run.runner]
            current_filter["runner"].append(runner)

        # Commit
        elif choice == 4:
            commit = prompt.ask("Commit to search for")
            runs_selected = [run for run in runs_selected
                             if commit == run.commit_sha]
            current_filter["commit"].append(commit)

        # Parameters
        elif choice == 5:
            parameters = prompt.ask("Parameters to search for "
                                    "(value or key:value "
                                    "for checking optional parameters name)."
                                    "\nPut multiple parameters"
                                    " separated by a comma")
            parameters = parameters.strip().split(",")

            # Filter runs
            compatible_runs = []
            for i, run in enumerate(runs_selected):
                groupofparameters = fetch_groupofparameters_of_run(session,
                                                                   run.id)
                for parameter in parameters:
                    for parameter_group in groupofparameters:
                        if ":" not in parameter:
                            if parameter in parameter_group.values.values():
                                compatible_runs.append(run)
                                break
                        else:
                            key, value = parameter.split(":")
                            if key in parameter_group.values.keys() and \
                               value == parameter_group.values[key]:
                                compatible_runs.append(run)
                                break
            runs_selected = compatible_runs
            parameters_new = current_filter["parameters"] + parameters
            current_filter["parameters"] = list(set(parameters_new))

        elif choice == 6:
            run_selection_menu(session, experiment_name, runs_selected)

        elif choice == 7:
            runs_selected = runs
            current_filter = {
                "tags": [],
                "description": [],
                "status": [],
                "runner": [],
                "commit": [],
                "parameters": []
                    }

        filter_print = "Current filter: \n"
        for filter_element, value in current_filter.items():
            if len(value) > 0:
                values_str = [str(v) for v in value]
                filter_print += \
                    f" :black_medium_square: {filter_element} : " + \
                    f"{', '.join(values_str)}\n"

        rich.print(filter_print)
        rich.print(f"Found [bold red]{len(runs_selected)}[/bold red] runs")


def prompt_explore_runs(experiment_name: str):
    """Prompt the user to search for a run of an experiment.
    And then explore it.

    :param experiment_name: The name of the experiment.
    :type experiment_name: str
    """

    # Opening database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Find the experiment id
    experiment_id = find_experiment_id(session, experiment_name)
    if experiment_id == -1:
        logger.error("Experiment does not exist")
        return

    # Get all runs of the experiment
    runs = fetch_runs_of_experiment(session, experiment_name)

    # Print number of runs
    rich.print(f"Experiment [bold yellow]{experiment_name}[/bold yellow] "
               f"has [bold red]{len(runs)}[/bold red] runs.")

    # If no runs, return
    if len(runs) == 0:
        return

    # Menu to ask if user wants to explore a run by a menu or
    # by doing a search
    menu = TerminalMenu(
            ["Search", "Menu"],
            title="How do you want to explore the runs?")
    menu_entry = menu.show()

    # If menu
    if menu_entry == 1:
        run_selection_menu(session, experiment_name, runs)
    else:
        search_runs(session, experiment_name, runs)
    session.close()


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

    rich.print(f"Run [bold red]{run_id}[/bold red] of experiment "
               f"[bold yellow]{experiment_name}[/bold yellow] informations:")
    rich.print(f"  - {ID} Id: {run.id}")
    rich.print(f"  - {DESCRIPTION} description: {run.description}")
    tags_string = f"  - {TAGS} Tags: "
    for tag in tags:
        tags_string += f"[bold green]{tag}[/bold green], "
    tags_string = tags_string[:-2]
    rich.print(tags_string)

    rich.print(f"  - {RUNNER} Runner: {run.runner}")
    if len(run.runner_params) > 0:
        rich.print(f"  - {PARAMETERS} Runner parameters:")
        for key, value in run.runner_params.items():
            rich.print(f"        :black_medium-small_square: {key}: {value}")
    rich.print(f"  - {PATH} Path: {run.storage_path}")
    rich.print(f"  - {STATUS} Status: {get_run_status_emoji(run.status)}")
    if run.progress != "":
        rich.print(f"  - {PROGRESS} Progress: {run.progress}")
    rich.print(f"  - {RUN_LAUNCH_DATE} Start time: {run.launched}")
    rich.print(f"  - {RUN_LAUNCH_DATE} End time: {run.finished}")
    rich.print(f"  - {COMMIT} Commit: {run.commit_sha}")
    if run.metric is not None:
        rich.print(f"  - {RUN_METRIC} Metric: {run.metric}")
    if run.container_path is not None:
        rich.print(f"  - {CONTAINER} Container path: {run.container_path}")
    if run.comment_file is not None:
        rich.print(f"  - {COMMENT} Comment file: {run.comment_file}")

    # Show run_explore_menu
    print('\n')
    run_explore_menu(session, experiment_name, run_id)


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
    logger.info(f"  - commit_sha: {run.commit_sha}")
    logger.info(f"  - metric: {run.metric}")
    logger.info(f"  - runner_params: {run.runner_params}")
    logger.info(f"  - container_path: {run.container_path}")
    if rich.prompt.Confirm.ask("Are you sure?"):

        console = rich.console.Console()

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

        with console.status('Deleting run in database and storage...'):
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
                          container_path: str = None,
                          commit_sha: str = None,
                          param_file: str = None,
                          parsed_parameters: list = None,
                          runner_params: dict = None) -> int:
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
    :type storage_path: str"1.0", "--std": "0.0"}

    :param description: The description of the run.
    :type description: str

    :param tags: The tags of the run.
    :type tags: list

    :param container_path: The path to the container.
    :type container_path: str

    :param commit_sha: The commit sha at which the run is launched.
    :type commit_sha: str

    :param param_file: The path to the parameter file when groups of
                       commands are given in a file.
    :type param_file: str

    :param parsed_parameters: The parsed parameters, for a rerun
    :type parsed_parameters: dict

    :param runner_params: The runner parameters for a rerun.
    :type runner_params: dict

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
    if commit_sha is None:
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
                sys.exit(-1)

        commit_sha_dB = repo.head.commit.hexsha

    else:
        if commit_sha not in [commit.hexsha for commit in repo.iter_commits()]:
            logger.error(
                    f"Commit {commit_sha} not found in the repository.")
            return -1
        commit_sha_dB = commit_sha

    # Get the parsed parameters
    if ctx is not None and \
            ((parsed_parameters is None) or (runner_params is None)):
        parsed_parameters, runner_params = \
            parse_args_cli(ctx, groups_of_parameters,
                           range_of_parameters)

    # Deal with param_file which override the parsed parameters
    # For rerun no need as alredy parsed: we check ctx is None to know
    # if it is a rerun
    if (ctx is not None) and (param_file is not None):
        parsed_parameters = parse_yaml_command_file(param_file)

    # Check whether storage_path is not None
    if storage_path is None:
        # Get the storage path from the config.yaml
        with open(".qanat/config.yaml", "r") as f:
            config = yaml.safe_load(f)

        # Get last id of experiments in the database
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
            commit_sha_dB, parsed_parameters, description,
            tags, runner, container_path, runner_params,
            param_file
        )
    run_id = run.id
    logger.info(f"Run {run_id} created.")

    # Create the execution handler
    if runner == "local":
        if "--n_threads" not in runner_params:
            runner_params["--n_threads"] = 1
        execution_handler = LocalMachineExecutionHandler(
                database_sessionmaker=Session,
                run_id=run_id,
                n_threads=int(runner_params['--n_threads']),
                container_path=container_path,
                commit_sha=commit_sha
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

        # Wait or not end of execution
        if "--wait" in runner_params:
            wait = runner_params["--wait"].lower() in [
                    "true", "yes", "1", "y"]
        else:
            wait = False

        execution_handler = HTCondorExecutionHandler(
                database_sessionmaker=Session,
                run_id=run_id,
                htcondor_submit_options=submit_info,
                container_path=container_path,
                commit_sha=commit_sha,
                wait=wait)

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


def rerun_experiment(experiment_name: str,
                     run_id: int):
    """Rerun an experiment with the exact same conditions
    as another run."""

    # Opening database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Check if the experiment exists
    experiment_id = find_experiment_id(Session(), experiment_name)
    if experiment_id == -1:
        logger.error(f"Experiment {experiment_name} does not exist.")
        return -1

    # Check if the run exists
    run = session.query(RunOfAnExperiment).filter_by(id=run_id).first()
    if run is None:
        logger.error(f"Run {run_id} does not exist.")
        return -1

    # Check if run is associated to the experiment
    if run.experiment_id != experiment_id:
        logger.error(f"Run {run_id} is not associated to experiment "
                     f"{experiment_name}.")
        return -1

    # Get the parsed parameters
    parsed_parameters = [group.values for group in
                         fetch_groupofparameters_of_run(session, run_id)]

    # Get the runner and runner_params
    runner = run.runner
    runner_params = run.runner_params

    # Get the commit_sha
    commit_sha = run.commit_sha

    # Get the storage_path
    # Get last id of experiments in the database
    storage_path = os.path.dirname(run.storage_path)
    last_id = session.query(func.max(RunOfAnExperiment.id)).scalar()
    if last_id is None:
        last_id = 0
    storage_path = os.path.join(
            storage_path,
            f"run_{last_id+1}"
    )

    # Get the description
    description = run.description

    # Get the container_path
    container_path = run.container_path

    # Get the tags
    tags = fetch_tags_of_run(session, run_id)
    tags += [f"rerun id {run_id}"]

    # Launch the experiment
    launch_run_experiment(experiment_name, None, None, None, runner,
                          storage_path, description, tags, container_path,
                          commit_sha, None, parsed_parameters, runner_params)
