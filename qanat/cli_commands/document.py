# ========================================
# FileName: document.py
# Date: 14 juin 2023 - 12:55
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Functions relative to the document
# command of qanat
# =========================================

import os
import rich
import git
import subprocess
from ._constants import (
    DOCUMENT, NAME, DESCRIPTION, PATH, TAGS, ID,
    EXEC, VIEW, RUNNER, available_runners, PARAMETERS,
    STATUS, COMMIT, FILE, ACTION
)
from ..core.database import (
        open_database, Document, Experiment,
        check_document_exists, check_document_dependency_exists,
        add_dependency_to_document, add_document,
        fetch_tags_of_document, get_dependencies_info_of_document,
        get_files_document_experiment, update_document,
        delete_document
)
from ..core.documents import DocumentCompiler
from ..utils.logging import setup_logger
from ..utils.parsing import parse_document_file
logger = setup_logger()


# ========================================
# Functions relative Document viewing
# ========================================
def command_view(document_name: str):
    """View a document.

    :param document_name: Name of the document to view
    :param type: str
    """

    # Open the database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Check if the document exists
    if not check_document_exists(session, document_name):
        logger.error(f"Document {document_name} does not exist")
        session.close()
        return

    # Get the document
    document = session.query(
            Document).filter_by(
                    name=document_name).first()

    # Check if the document is compiled
    if not document.compiled:
        logger.error(f"Document {document_name} is not compiled")
        session.close()
        return

    # Get the document path, view script and view script command
    document_path = document.path
    view_script = document.view_script
    view_script_command = document.view_script_command

    # Launch the view script
    logger.info(f"Viewing document {document_name}"
                f" with {view_script_command} {view_script}"
                f" in {document_path}")
    process = subprocess.Popen(
            [view_script_command, view_script],
            cwd=document_path)
    process.wait()

    session.close()


# ========================================
# Functions relative Document compiling
# ========================================
def command_compile(document_name: str,
                    compile_options: str,
                    view: bool = False):
    """Compile a document.

    :param document_name: Name of the document to compile
    :param type: str

    :param compile_options: Options to pass to the compiler
    :param type: str

    :param view: View the document after compiling
    :param type: bool
    """

    # Open the database
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()
    if not check_document_exists(session, document_name):
        logger.error(f"Document {document_name} does not exist")
        session.close()
        return

    compiler = DocumentCompiler(document_name)
    compiler.compile_document(compile_options)

    logger.info(f"Document {document_name} compiled")

    if view:
        logger.info(f"Viewing document {document_name}")
        command_view(document_name)


# ========================================
# Functions relative Document listing
# ========================================
def command_list():
    """List all the documents."""

    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    console = rich.console.Console()
    with console.status("[bold green]Loading documents...", spinner="dots"):
        documents = session.query(Document).all()

    grid = rich.table.Table.grid(expand=True, padding=(1, 2))
    grid.add_column("ID", justify="left", style="blue")
    grid.add_column("Name", justify="left", style="cyan")
    grid.add_column("Description", justify="left", style="magenta")
    grid.add_column("Path", justify="left", style="green")
    grid.add_column("Status", justify="left", style="yellow")
    grid.add_column("Compiled", justify="left", style="red")
    grid.add_column("Tags", justify="left", style="yellow")

    grid.add_row(
            f"{ID} ID", f"{NAME} Name", f"{DESCRIPTION} Description",
            f"{PATH} Path", f"{STATUS} Status", f"{EXEC} Compiled",
            f"{TAGS} Tags"
    )

    for document in documents:

        # Fetch tags from the database
        tags = fetch_tags_of_document(session, document.id)

        grid.add_row(
                f"{document.id}",
                f"{document.name}",
                f"{document.description}",
                f"{document.path}",
                f"{document.status}",
                f"{document.compiled}",
                ", ".join(tags)
        )

    rich.print(grid)
    session.close()


def command_status(document_name: str):
    """Get the information of a document.

    :param document_name: Name of the document to get the status of
    :param type: str
    """

    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()
    if not check_document_exists(session, document_name):
        logger.error(f"Document {document_name} does not exist")
        session.close()
        return

    document = session.query(Document).filter_by(name=document_name).first()
    tags = fetch_tags_of_document(session, document.id)

    # Get dependency information
    runner_list, runner_params_list, run_args_file_list, commit_sha_list, \
        action_name_list, action_args_list, experiments_list = \
        get_dependencies_info_of_document(session, document.id)

    console = rich.console.Console()
    console.print(f"{DOCUMENT} Information of {document_name}:")
    console.print(f"{NAME} Name: {document.name}")
    console.print(f"{DESCRIPTION} Description: {document.description}")
    console.print(f"{PATH} Path: {document.path}")
    console.print(f"{EXEC} Compile script: {document.compile_script}")
    console.print(
        f"{EXEC} Compile script command: {document.compile_script_command}")
    console.print(f"{EXEC} View script: {document.view_script}")
    console.print(
            f"{EXEC} View script command: {document.view_script_command}")
    console.print(f"{STATUS} Status: {document.status}")
    console.print(f"{EXEC} Compiled: {document.compiled}")
    console.print(f"{TAGS} Tags: {tags}")

    grid = rich.table.Table.grid(expand=True, padding=(0, 2))
    grid.add_column("Experiment", justify="left", style="blue")
    grid.add_column("Runner", justify="left", style="cyan")
    grid.add_column("Runner Parameters", justify="left", style="magenta")
    grid.add_column("Run Args File", justify="left", style="green")
    grid.add_column("Commit SHA", justify="left", style="yellow")
    grid.add_column("Action Name", justify="left", style="red")
    grid.add_column("Action Parameters", justify="left", style="red")
    grid.add_column("Files", justify="left", style="red")

    grid.add_row(
            f"{NAME} Experiment", f"{RUNNER} Runner",
            f"{PARAMETERS} Runner Parameters", f"{PARAMETERS} Run Args File",
            f"{COMMIT} Commit SHA", f"{ACTION} Action Name",
            f"{PARAMETERS} Action Parameters", f"{FILE} Files"
    )

    for experiment, runner, runner_params, run_args_file, commit_sha, \
            action_name, action_args, experiment in zip(
                    experiments_list, runner_list, runner_params_list,
                    run_args_file_list, commit_sha_list, action_name_list,
                    action_args_list, experiments_list
            ):
        files = get_files_document_experiment(session, document.id,
                                              experiment.id)
        grid.add_row(
                f"{experiment.name}",
                f"{runner}",
                f"{runner_params}",
                f"{run_args_file}",
                f"{commit_sha}",
                f"{action_name}",
                f"{action_args}",
                ", ".join(files)
        )

    console.print(f"\n{DOCUMENT} Dependencies:")
    rich.print(grid)

    session.close()


# ===============================================
# Functions relative Document dependency adding
# ===============================================
def command_add_dependency(document_name: str,
                           experiment_name: str,
                           run_args_file: str,
                           files: list,
                           runner: str,
                           runner_params: str,
                           container: str,
                           commit_sha: str):
    """Add a dependency to a document

    :param document_name: Name of the document to add the dependency to
    :param type: str

    :param experiment_name: Name of the experiment corresponding to the
                            dependency
    :param type: str

    :param run_args_file: Path to the run args file
    :param type: str

    :param files: List of files to add to the dependency
    :param type: list

    :param runner: Name of the runner to use
    :param type: str

    :param runner_params: Parameters to pass to the runner
    :param type: str

    :param container: Name of the container to use
    :param type: str

    :param commit_sha: Commit sha of the dependency
    :param type: str
    """
    print("TODO")


def command_add_dependency_prompt():
    """Add a dependency to a document from a prompt."""

    console = rich.console.Console()
    prompt = rich.prompt.Prompt()
    confirm = rich.prompt.Confirm()
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    console.print(f"{DOCUMENT} New document dependency adding prompt:")
    document_name = prompt.ask(f"{NAME} Document name")

    # Check if the document exists in the database
    document = session.query(Document).filter_by(name=document_name).first()
    while document is None:
        console.print(f"[bold red]Document {document_name} does not exist")
        document_name = prompt.ask(f"{NAME} Document name")
        document = session.query(
                Document).filter_by(name=document_name).first()

    experiment_name = prompt.ask(f"{NAME} Experiment name")

    # Check if the experiment exists in the database
    experiment = session.query(
            Experiment).filter_by(name=experiment_name).first()
    while experiment is None:
        console.print(f"[bold red]Experiment {experiment_name} does not exist")
        experiment_name = prompt.ask(f"{NAME} Experiment name")
        experiment = session.query(
                Experiment).filter_by(name=experiment_name).first()

    commit_sha = prompt.ask(f"{RUNNER} Commit sha of run "
                            "(enter for always current)",
                            default=None)

    # Check if the commit sha exists in this git repository
    if commit_sha is not None:
        repo = git.Repo('.')
        while commit_sha not in [
                commit.hexsha for commit in repo.iter_commits()]:
            console.print(f"[bold red]Commit {commit_sha} does not exist")
            commit_sha = prompt.ask(
                    f"{RUNNER} Commit sha of run (enter for current)",
                    default=None)
            if commit_sha is None:
                break

    run_args_file = prompt.ask(f"{PARAMETERS} Run args file (enter for none)",
                               default=None)

    # Check if the run args file exists at the commit sha
    if run_args_file is not None:
        if commit_sha is None:
            if not os.path.isfile(run_args_file):
                console.print(
                        f"[bold red]Run args file {run_args_file} "
                        "does not exist")
                run_args_file = prompt.ask(f"{PARAMETERS} Run args file")
        else:
            repo = git.Repo()
            commit_tree = repo.commit(commit_sha).tree
            if run_args_file not in commit_tree:
                console.print(
                        f"{PARAMETERS} Run args file {run_args_file} does "
                        f"not exist at commit {commit_sha}")
                run_args_file = prompt.ask(f"{PARAMETERS} Run args file")

    files = prompt.ask(f"{PARAMETERS} Files (separated by a comma)")
    files = files.strip().split(",")

    runner = prompt.ask(f"{RUNNER} Runner", choices=available_runners)
    runner_params = prompt.ask(f"{RUNNER} Runner parameters")
    container = prompt.ask(f"{RUNNER} Container path (enter for none)",
                           default=None)
    if container is not None:
        while not os.path.isfile(container):
            console.print(f"[bold red]Container {container} does not exist")
            container = prompt.ask(f"{RUNNER} Container path (enter for none)",
                                   default=None)
            if container is None:
                break

    # Ask about action to perform before checking for dependencies
    action_name = prompt.ask(
            f"{DOCUMENT} Action to perform after running experiment and"
            " before compiling document (enter for none)",
            default=None)
    if action_name is not None:
        action_args = prompt.ask(
            f"{DOCUMENT} Action args (enter for none)", default=None)
    else:
        action_args = None

    # Check if the dependency already exists
    if check_document_dependency_exists(
            session, document_name, experiment_name, run_args_file):
        console.print(f"{DOCUMENT} Dependency already exists")
        return

    else:

        # Ask for confirmation
        console.print(f"\n{DOCUMENT} Dependency to add:")
        console.print(f"{NAME} Document name: {document_name}")
        console.print(f"{NAME} Experiment name: {experiment_name}")
        console.print(f"{PARAMETERS} Run args file: {run_args_file}")
        console.print(f"{PARAMETERS} Files: {files}")
        console.print(f"{RUNNER} Runner: {runner}")
        console.print(f"{RUNNER} Runner parameters: {runner_params}")
        console.print(f"{RUNNER} Container: {container}")
        console.print(f"{RUNNER} Commit sha: {commit_sha}")
        console.print(f"{DOCUMENT} Action name: {action_name}")
        console.print(f"{DOCUMENT} Action parameters: {action_args}")
        if not confirm.ask(f"{DOCUMENT} Do you want to add this dependency?"):
            session.close()
            return

        dependency = {
            'experiment_name': experiment_name,
            'run_args_file': run_args_file,
            'files': files,
            'runner': runner,
            'runner_params': runner_params,
            'container': container,
            'commit_sha': commit_sha,
            'action_name': action_name,
            'action_args': action_args
        }

        add_dependency_to_document(session, document_name, dependency)
        logger.info(f"Dependency added to document {document_name}:")
        logger.info(dependency)

    session.close()


# ========================================
# Functions relative Document creation
# ========================================
def command_add_from_file(file_path: str, yes: bool = False):
    """Add a document from a description file"""
    # Check if the file exists
    if not os.path.isfile(file_path):
        logger.error(f"File {file_path} does not exist")
        return

    # Parse the file
    document_info = parse_document_file(file_path)

    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Check if the document already exists
    if check_document_exists(session, document_info['name']):
        logger.error(f"Document {document_info['name']} already exists")
        return

    add_document(
            session, document_info['name'], document_info['path'],
            document_info['compile_script'],
            document_info['compile_script_command'],
            description=document_info['description'],
            view_script=document_info['view_script'],
            view_script_command=document_info['view_script_command'],
            experiment_dependencies=document_info['experiment_dependencies'])

    logger.info(f"Document '{document_info['name']}' added")
    session.close()


def command_add_prompt():
    """Add a document from a prompt."""

    console = rich.console.Console()
    prompt = rich.prompt.Prompt()
    confirm = rich.prompt.Confirm()
    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    console.print(f"{DOCUMENT} New document adding prompt:")

    # Get the document info
    document_name = prompt.ask(f"{NAME} Document name")
    document_description = prompt.ask(f"{DESCRIPTION} Document description")
    document_path = prompt.ask(f"{PATH} Document path (from project root)")

    while not os.path.isdir(document_path):
        console.print(f"{PATH} Directory {document_path} does not exist")
        document_path = prompt.ask(f"{PATH} Document path (from project root)")

    document_tags = prompt.ask(f"{TAGS} Document tags (separated by a comma)")
    document_tags = document_tags.strip().split(",")
    document_compile_script = prompt.ask(f"{EXEC} Document compile script",
                                         default="compile.sh")
    document_compile_command = prompt.ask(f"{EXEC} Document compile command",
                                          default="bash")
    document_view_script = prompt.ask(f"{VIEW} Document view script",
                                      default=os.path.join(document_path,
                                                           "view.sh"))
    document_view_command = prompt.ask(f"{VIEW} Document view command",
                                       default="bash")

    # Confirm the document info
    console.print(f"\n{DOCUMENT} Document info:")
    console.print(f"{NAME} Document name: {document_name}")
    console.print(
            f"{DESCRIPTION} Document description: {document_description}")
    console.print(f"{PATH} Document path (from project root): {document_path}")
    console.print(
            f"{TAGS} Document tags (separated by a comma): {document_tags}")
    console.print(f"{EXEC} Document compile script: {document_compile_script}")
    console.print(
            f"{EXEC} Document compile command: {document_compile_command}")
    console.print(f"{VIEW} Document view script: {document_view_script}")
    console.print(f"{VIEW} Document view command: {document_view_command}")

    if not confirm.ask("[bold red]Is this information correct?"):
        return

    # Check if the document already exists
    if check_document_exists(session, document_name):
        logger.error(f"[bold red]Document {document_name} already exists")
        return

    # Add the document to the database
    add_document(session, document_name, document_path,
                 document_compile_script, document_compile_command,
                 document_description, document_view_script,
                 document_view_command, tags=document_tags)
    logger.info(f"Document '{document_name}' added to the database")

    # Asking for dependencies
    while confirm.ask("[bold red]Do you want to add a dependency?"):
        command_add_dependency_prompt(session, document_name)

    session.close()


# ========================================
# Functions relative Document edition
# ========================================
def command_update(document_name: str):
    """Update a document

    :param document_name: Name of the document to update
    :type document_name: str
    """

    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()

    # Check if the document exists in the database
    document = session.query(Document).filter_by(name=document_name).first()
    if document is None:
        logger.error(f"Document {document_name} does not exist")
        return

    console = rich.console.Console()
    prompt = rich.prompt.Prompt()

    console.print(f"{DOCUMENT} Document update prompt:")
    command_status(document_name)

    # Asking what to update
    choices = [
        "Name", "Description", "Path", "Compile script", "Compile command",
        "View script", "View command", "Tags", "Dependencies", "Exit"]
    choice = prompt.ask(f"{DOCUMENT} What do you want to update?",
                        choices=choices)

    while choice != "Exit":

        new_name, new_description, new_path, new_compile_script, \
            new_compile_command, new_view_script, new_view_command, \
            new_tags = None, None, None, None, None, None, \
            None, None

        if choice == "Name":
            new_name = prompt.ask(f"{NAME} New name")
        elif choice == "Description":
            new_description = prompt.ask(f"{DESCRIPTION} New description")
        elif choice == "Path":
            new_path = prompt.ask(f"{PATH} New path (from project root)")
            while not os.path.isdir(new_path):
                console.print(f"{PATH} Directory {new_path} does not exist")
                new_path = prompt.ask(f"{PATH} New path (from project root)")
        elif choice == "Compile script":
            new_compile_script = prompt.ask(f"{EXEC} New compile script")
        elif choice == "Compile command":
            new_compile_command = prompt.ask(f"{EXEC} New compile command")
        elif choice == "View script":
            new_view_script = prompt.ask(f"{VIEW} New view script")
        elif choice == "View command":
            new_view_command = prompt.ask(f"{VIEW} New view command")
        elif choice == "Tags":
            new_tags = prompt.ask(f"{TAGS} New tags (separated by a comma)")
            new_tags = new_tags.strip().split(",")
        elif choice == "Dependencies":
            console.print("Sorry, this feature is not implemented yet"
                          " You can delete the dependency with the command"
                          " 'qanat document delete_dependency'"
                          " and add it again with the command"
                          " 'qanat document add_dependency'")

        # Update
        update_document(session, document_name, new_name=new_name,
                        new_description=new_description,
                        new_path=new_path,
                        new_compile_script=new_compile_script,
                        new_compile_script_command=new_compile_command,
                        new_view_script=new_view_script,
                        new_view_script_command=new_view_command,
                        new_tags=new_tags)

        choice = prompt.ask(f"{DOCUMENT} What do you want to update?",
                            choices=choices)

    session.close()


# ========================================
# Functions relative Document deletion
# ========================================
def command_delete(document_name):
    """Delete a document

    :param document_name: Name of the document to delete
    :type document_name: str
    """

    confirm = rich.prompt.Confirm()

    logger.info(f"Deleting document '{document_name}'")
    logger.warning("This action is irreversible")

    command_status(document_name)

    if not confirm.ask("[bold red]Are you sure?"):
        return

    engine, Base, Session = open_database('.qanat/database.db')
    session = Session()
    delete_document(session, document_name)
    session.close()
