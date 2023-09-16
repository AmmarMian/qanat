"""Console script for qanat."""
import sys
import rich_click as click
import rich
import art

from .cli_commands.init import init_qanat
from .cli_commands import (
        experiment, dataset, status, run,
        config, cache, document
)
from .core.repo import check_directory_is_qanat

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.APPEND_METAVARS_HELP = True

ASCII_ART_use = art.text2art("Qanat", font="tarty4")
message_version = ASCII_ART_use + \
        "\n\n%(prog)s, version %(version)s\n" + \
        "Minimal experience management system.\n" + \
        "Author: %s\n" % rich.markup.escape("Ammar Mian") + \
        "License: %s\n" % rich.markup.escape("GNU AGPLv3") +\
        "Source: %s\n" % rich.markup.escape(
                "https://github.com/AmmarMian/qanat")


def check_cwd_is_qanat():
    """Check if current working directory is a Qanat repertory."""
    if not check_directory_is_qanat('./'):
        rich.print("[bold red] :warning: Current "
                   "working directory is not a Qanat repertory.")
        sys.exit(1)


@click.group()
@click.version_option(message=message_version, prog_name="Qanat")
def main(args=None):
    """Minimal experience management system."""
    return 0


# Main commands
@main.command(name="status")
def status_main():
    """Check status of experiments in this directory."""
    check_cwd_is_qanat()
    status.command_status()


@main.command()
@click.argument("directory", type=click.Path(exists=True), required=True)
@click.option('-y', '--yes', is_flag=True, help="Answer yes to all questions.")
def init(directory, yes):
    """Initialize experiment directory."""
    init_qanat(directory, yes)


def get_autocomplete_experiment_command(ctx, args, incomplete):
    """Get autocomplete for experiment command."""
    commands = [('list', 'List all experiments.'),
                ('new', 'Create new experiment.'),
                ('status', 'Show status of all runs from an experiment.'),
                ('delete', 'Delete experiment.'),
                ('update', 'Update experiment.'),
                ('run', 'Run experiment.'),
                ('rerun', 'Rerun a single run with exact same environment')
                ]
    return [k for k, v in commands if incomplete in k]


@main.group(name="experiment")
def experiment_main():
    """Experiment-level utility"""
    check_cwd_is_qanat()
    return 0


@main.group(name="dataset")
def dataset_main():
    """Dataset-level utility"""
    check_cwd_is_qanat()
    return 0


@main.group(name="document")
def document_main():
    """Document-level utility"""
    check_cwd_is_qanat()
    return 0


@main.group(name="config")
def config_main():
    """Repository configuration utility"""
    check_cwd_is_qanat()
    return 0


@main.group(name="cache")
def cache_main():
    """Cache management utility"""
    check_cwd_is_qanat()
    return 0


# Subcommands: cache
@cache_main.command(name="status")
def cache_status():
    """Show cache status."""
    cache.command_status()


@cache_main.command(name="clean")
def cache_clean():
    """Clean cache."""
    cache.command_clean()


# Subcommands: experiment
@experiment_main.command(name="list")
def experiment_list():
    """Show list of experiments in this repertory."""
    experiment.command_list()


@experiment_main.command(name="new")
@click.option('--prompt', '-p', is_flag=True,
              default=True, help='Prompt for adding experiment.')
@click.option('--file', '-f', type=click.Path(exists=True),
              required=False, help='Path to a YAML file'
              'containing the experiment definition.')
def experiment_new(prompt, file):
    """Create new experiment."""
    if file is not None:
        experiment.command_new_experiment_from_yaml(file)
    else:
        experiment.command_add_prompt()


@experiment_main.command(name="status")
@click.argument("name", type=click.STRING, required=True)
@click.option("--live", is_flag=True, default=False,
              help="Show live status of runs.")
def experiment_show(name, live):
    """Show status of all runs."""
    experiment.command_status(name, live)


@experiment_main.command(name="delete")
@click.argument("name", type=click.STRING, required=True)
def experiment_delete(name):
    """Delete experiment."""
    experiment.command_delete(name)


@experiment_main.command(name="update")
@click.argument("name", type=click.STRING, required=True)
def experiment_update(name):
    """Update experiment."""
    experiment.command_update(name)


@experiment_main.command(name="rerun")
@click.argument("name", type=click.STRING, required=True)
@click.argument("run_id", type=click.INT, required=True)
def experiment_rerun(name, run_id):
    """Rerun a single run with exact same environment
    and paraeters."""
    run.rerun_experiment(name, run_id)


@experiment_main.command(
    name="run",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("name", type=click.STRING, required=True)
@click.option("--runner", "-r", default="local",
              type=click.Choice(["local", "htcondor", "slurm"]),
              show_default=True,
              help="Runner to use for experiment.")
@click.option("--container", default=None, type=click.STRING,
              help="Container to use for experiment.")
@click.option("--param_file", "-f", default=None, type=click.STRING,
              help="File containing params to run experiment (one per line).")
@click.option("--group_param", "-g", default=None, type=click.STRING,
              help="Group of parameters to run.", multiple=True)
@click.option("--range_param", "-r", default=None, type=click.STRING,
              help="Range for a single parameter.", multiple=True)
@click.option("--storage_path", default=None, type=click.STRING,
              help="Path to store results.")
@click.option("--tag", "-t", default=None, type=click.STRING,
              help="Tag to assing this run", multiple=True)
@click.option("--description", default="", type=click.STRING,
              help="Description of this run.")
@click.option("--commit_sha", default=None, type=click.STRING,
              help="Commit sha to use for this run.")
@click.option("--dry_run", is_flag=True, default=False,
              help="Dry run, do not run experiment but show parameters.")
@click.pass_context
# TODO: Debug this
# fetched from:
# https://stackoverflow.com/questions/32944131/ ...
# add-unspecified-options-to-cli-command-using-python-click
def experiment_run(ctx, name, runner, group_param, range_param,
                   storage_path, tag, description, container,
                   commit_sha, param_file, dry_run):
    """Run an experiment with additional positional and option args.\n
    [bold red]WARNING: The following options are not available
    for your executable command:[/bold red]\n
    * [bold yellow]--runner[/bold yellow] to specify runner\n
    * [bold yellow]--container[/bold yellow] to specify container\n
    * [bold yellow]--n_threads[/bold yellow] for local runner, number of
    threads to use when several groups of parameters.\n
    * [bold yellow]--submit_template[/bold yellow] for htcondor runner,
    path to the submit template to use or name of the submit template in the
    config file.\n
    * [bold yellow]--wait[/bold yellow] for htcondor runner, wait for the
    experiment to finish.\n
    * [bold yellow]--param_file[/bold yellow] to specify a file containing
    parameters to run as a single run.\n
    * [bold yellow]--group_param[/bold yellow] to specify group of parameters
    to run as the same run.\n
    * [bold yellow]--range_param[/bold yellow] to specify to create groups of
    parameters as a range. Syntax is: -r '--param start end step'.\n
    * [bold yellow]--storage_path[/bold yellow] to override storage path for
    the run of the experiment.\n
    * [bold yellow]--tag[/bold yellow] to add tag to the run of the
    experiment.\n
    * [bold yellow]--description[/bold yellow] to add description to the run of
    the experiment.\n
    * [bold yellow]--commit_sha[/bold yellow] to run at a specific commit.\n
    """
    run.launch_run_experiment(
            name, ctx, group_param, range_param, runner,
            storage_path, dry_run, description, tag, container,
            commit_sha, param_file)


@experiment_main.command(
    name="run_delete",
)
@click.argument("experiment_name", type=click.STRING,
                required=True)
@click.argument("run_id", type=int, required=True)
def experiment_run_delete(experiment_name, run_id):
    """Delete run of experiment."""
    run.delete_run(experiment_name, run_id)


@experiment_main.command(
    name="run_explore",
)
@click.argument("experiment_name", type=click.STRING,
                required=True)
@click.argument("run_id", type=int, required=False,
                default=None)
def experiment_run_explore(experiment_name, run_id):
    """Explore run of an experiment."""
    try:
        if run_id is not None:
            run.explore_run(experiment_name, run_id)
        else:
            run.prompt_explore_runs(experiment_name)
    except ModuleNotFoundError:
        rich.print("Sorry thois functionality does not work"
                   " with your current terminal. Please use a linux"
                   " compatible terminal (WSL on windows).")
    sys.exit(-1)


@experiment_main.command(
    name="run_comment",
)
@click.argument("experiment_name", type=click.STRING,
                required=True)
@click.argument("run_id", type=int, required=True)
def experiment_run_comment(experiment_name, run_id):
    """Comment run of an experiment."""
    run.command_comment(experiment_name, run_id)


@experiment_main.command(
    name="action",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("experiment_name", type=click.STRING, required=True)
@click.argument("action_name", type=click.STRING, required=True)
@click.argument("run_id", type=int, required=True)
@click.option("--group_no", type=int, required=False, default=None,
              help="Group number to run action on when "
              "several groups are present in the run.")
@click.pass_context
def experiment_action(ctx, experiment_name, action_name, run_id,
                      group_no):
    """Run an action on a run of an experiment.
    Additional option args can be passed to the action after
    experiment and action name."""
    experiment.command_action(experiment_name, action_name, run_id, ctx,
                              group_no)


# Subcommands: document
@document_main.command(name="list")
def document_list():
    """Show list of documents in this repertory."""
    document.command_list()


@document_main.command(name="new")
@click.option("--file", '-f', type=click.Path(exists=True),
              help="Path to a YAML file containing the document definition.")
def document_new(file):
    """Create new document.

    DESCRIPTION_FILE is a file containing the description of the document. If
    not provided, a prompt will ask for the description.
    """
    if file is not None:
        document.command_add_from_file(file)
        return
    document.command_add_prompt()


@document_main.command(name="status")
@click.argument("name", type=click.STRING, required=True)
def document_status(name):
    """Show status of document."""
    document.command_status(name)


@document_main.command(name="view")
@click.argument("name", type=click.STRING, required=True)
def document_view(name):
    """View document."""
    document.command_view(name)


@document_main.command(name="compile")
@click.argument("name", type=click.STRING, required=True)
@click.option("--options", type=click.STRING, required=False,
              help="Options to pass to the compiler as str.")
@click.option("--view", type=click.BOOL, required=False,
              help="View document after compilation.",
              default=False, is_flag=True)
def document_compile(name, options, view):
    """Compile document."""
    document.command_compile(name, options, view)


@document_main.command(name="add_dependency")
@click.argument("document_name", type=click.STRING, required=False)
@click.argument("experiment_name", type=click.STRING, required=False)
@click.argument("run_args_file", type=click.STRING, required=False)
@click.argument("files", type=click.Path(exists=True), nargs=-1)
@click.option("--runner", type=click.STRING, required=False,
              help="Runner to use for running the experiment.",
              default="local")
@click.option("--runner_params", type=click.STRING, required=False,
              default=None, help="Parameters to pass to the runner.")
@click.option("--container", type=click.STRING, required=False,
              help="Container to use for running the experiment.",
              default=None)
@click.option("--commit_sha", type=click.STRING, required=False,
              help="Commit SHA to use for running the experiment.",
              default=None)
@click.option('--yes', is_flag=True, default=False,
              help="Skip confirmation prompt.")
def document_add_dependency(document_name, experiment_name, run_args_file,
                            files, runner, runner_params, container,
                            commit_sha, yes):
    """Add dependency to document."""
    if any([x is None for x in [document_name, experiment_name,
                                run_args_file]]):
        document.command_add_dependency_prompt()
    else:
        document.command_add_dependency(document_name, experiment_name,
                                        run_args_file, files, runner,
                                        runner_params, container, commit_sha,
                                        yes)


@document_main.command(name="delete_dependency")
@click.argument("document_name", type=click.STRING, required=False)
@click.argument("experiment_name", type=click.STRING, required=False)
@click.argument("run_args_file", type=click.STRING, required=False)
def document_delete_dependency(document_name, experiment_name,
                               run_args_file):
    """Delete dependency from document."""
    click.echo("Not implemented yet.")


@document_main.command(name="delete")
@click.argument("name", type=click.STRING, required=True)
def document_delete(name):
    """Delete document."""
    document.command_delete(name)


@document_main.command(name="update")
@click.argument("name", type=click.STRING, required=True)
def document_update(name):
    """Update document."""
    document.command_update(name)


# Subcommands: dataset
@dataset_main.command(name="list")
def dataset_list():
    """Show list of datasets in this repertory."""
    dataset.command_list()


@dataset_main.command(name="new")
@click.option("--file", "-f", type=click.Path(exists=True),
              help="Path to a YAML file containing the dataset definition.")
@click.option("--yes", is_flag=True, default=False,
              help="Skip confirmation prompt.")
def dataset_new(file, yes):
    """Create new dataset."""
    if file is not None:
        dataset.command_add_from_file(file,
                                      confirm=not yes)
    else:
        dataset.command_add_prompt()


@dataset_main.command(name="delete")
@click.argument("name", type=click.STRING, required=True)
def dataset_delete(name):
    """Delete dataset."""
    dataset.command_delete(name)


@dataset_main.command(name="update")
@click.argument("name", type=click.STRING, required=True)
@click.option("--yes", is_flag=True, default=False,
              help="Skip confirmation prompt.")
def dataset_update(name, yes):
    """Update dataset."""
    dataset.command_update(name, confirm=not yes)


# Subcommands: config
@config_main.command()
def show():
    """Show configuration."""
    config.command_show()


@config_main.command()
@click.argument("file", type=click.Path(exists=True),
                required=False)
def edit(file):
    """Edit configuration with YAML file."""

    if file is not None:
        # Check whether YAML file
        if not file.endswith(".yaml") or not file.endswith(".yml"):
            rich.print("[bold red]Configuration file must be YAML file.")
            return 1
    config.command_edit(file)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
