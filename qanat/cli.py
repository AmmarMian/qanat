"""Console script for qanat."""
import sys
import rich_click as click
import rich

from .cli_commands.init import init_qanat
from .cli_commands import (
        experiment, dataset, status, run,
        config, cache
)
from .core.repo import check_directory_is_qanat

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.APPEND_METAVARS_HELP = True

ASCII_ART_use = r"""
                        .
                       _|_
 .-.,  .-.  .--.  .-.   |
(   | (   ) |  | (   )  |
 `-'|  `-'`-'  `- `-'`- `-'
   -|-
    '
"""


def check_cwd_is_qanat():
    """Check if current working directory is a Qanat repertory."""
    if not check_directory_is_qanat('./'):
        click.echo("Current working directory is not a Qanat repertory.")
        sys.exit(1)


@click.group()
@click.version_option(message=ASCII_ART_use + "%(prog)s, version %(version)s")
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
def init(directory):
    """Initialize experiment directory."""
    init_qanat(directory)


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
def experiment_new():
    """Create new experiment."""
    experiment.command_add_prompt()


@experiment_main.command(name="status")
@click.argument("name", type=click.STRING, required=True)
@click.option("--prompt", "-p", is_flag=True, default=False)
def experiment_show(name, prompt):
    """Show status of all runs."""
    experiment.command_status(name, prompt)


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
              type=click.Choice(["local", "htcondor"]), show_default=True,
              help="Runner to use for experiment.")
@click.option("--container", default=None, type=click.STRING,
              help="Container to use for experiment.")
@click.option("--group_param", "-g", default=None, type=click.STRING,
              help="Group of parameters to run.", multiple=True)
@click.option("--range_param", "-r", default=None, type=click.STRING,
              help="Range for a single parameter.", multiple=True)
@click.option("--storage_path", default=None, type=click.STRING)
@click.option("--tag", "-t", default=None, type=click.STRING,
              help="Tag to assing this run", multiple=True)
@click.option("--description", default="", type=click.STRING)
@click.option("--commit_sha", default=None, type=click.STRING)
@click.pass_context
# TODO: Debug this
# fetched from:
# https://stackoverflow.com/questions/32944131/ ...
# add-unspecified-options-to-cli-command-using-python-click
def experiment_run(ctx, name, runner, group_param, range_param,
                   storage_path, tag, description, container,
                   commit_sha):
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
    * [bold yellow]--group_param[/bold yellow] to specify group of parameters
    to run as the same run.\n
    * [bold yellow]--range_param[/bold yellow] to specify to create groups of
    parameters as a range. Syntax is: -r '--param start end step'.\n
    * [bold yellow] --storage_path[/bold yellow] to override storage path for
    the run of the experiment.\n
    * [bold yellow]--tag[/bold yellow] to add tag to the run of the
    experiment.\n
    * [bold yellow]--description[/bold yellow] to add description to the run of
    the experiment.\n
    * [bold yellow]--commit_sha[/bold yellow] to run at a specific commit.\n
    """
    run.launch_run_experiment(
            name, ctx, group_param, range_param, runner,
            storage_path, description, tag, container, commit_sha)


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
    name="action",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("experiment_name", type=click.STRING, required=True)
@click.argument("action_name", type=click.STRING, required=True)
@click.argument("run_id", type=int, required=True)
@click.pass_context
def experiment_action(ctx, experiment_name, action_name, run_id):
    """Run an action on a run of an experiment.
    Additional option args can be passed to the action after
    experiment and action name."""
    experiment.command_action(experiment_name, action_name, run_id, ctx)


# Subcommands: dataset
@dataset_main.command(name="list")
def dataset_list():
    """Show list of datasets in this repertory."""
    dataset.command_list()


@dataset_main.command(name="new")
def dataset_new():
    """Create new dataset."""
    dataset.command_add_prompt()


@dataset_main.command(name="delete")
@click.argument("name", type=click.STRING, required=True)
def dataset_delete(name):
    """Delete dataset."""
    dataset.command_delete(name)


@dataset_main.command(name="update")
def dataset_update():
    """Update dataset."""
    click.echo("TODO")


# Subcommands: config
@config_main.command()
def show():
    """Show configuration."""
    config.command_show()


@config_main.command()
@click.argument("file", type=click.Path(exists=True))
def edit(file):
    """Edit configuration with YAML file."""

    # Check whether YAML file
    if not file.endswith(".yaml"):
        rich.print("[bold red]Configuration file must be YAML file.")
        return 1
    config.command_edit(file)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
