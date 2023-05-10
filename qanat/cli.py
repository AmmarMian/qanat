"""Console script for qanat."""
import sys
import rich_click as click
import rich

from .cli_commands.init import init_qanat
from .cli_commands import (
        experiment, dataset, status, run
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


@main.group()
def config():
    """Repository configuration utility"""
    check_cwd_is_qanat()
    click.echo("TODO")


# Subcommands: experiment
@experiment_main.command(name="list")
def experiment_list():
    """Show list of experiments in this repertory."""
    experiment.command_list()


@experiment_main.command(name="new")
def experiment_new():
    """Create new experiment."""
    experiment.command_add_prompt()


@experiment_main.command(name="show")
@click.argument("name", type=click.STRING, required=True)
@click.option("--prompt", "-p", is_flag=True, default=False)
def experiment_show(name, prompt):
    """Show runs of experiment + prompt."""
    experiment.command_show(name, prompt)


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


@experiment_main.command(
    name="run",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("name", type=click.STRING, required=True)
@click.option("--runner", "-r", default="local",
              type=click.Choice(["local", "MUST"]), show_default=True,
              help="Runner to use for experiment.")
@click.option("--group_param", "-g", default=None, type=click.STRING,
              help="Group of parameters to run.", multiple=True)
@click.option("--storage_path", default=None, type=click.STRING)
@click.option("--tag", "-t", default=None, type=click.STRING,
              help="Tag to assing this run", multiple=True)
@click.option("--description", default="", type=click.STRING)
@click.pass_context
# TODO: Debug this
# fetched from:
# https://stackoverflow.com/questions/32944131/ ...
# add-unspecified-options-to-cli-command-using-python-click
def experiment_run(ctx, name, runner, group_param, storage_path,
                   tag, description):
    """Run an experiment with additional positional and option args.\n
    [bold red]WARNING: The following options are not available "
    "for your executable command:[/bold red]\n"
    - [bold red]'--runner'[/bold red] to specify runner\n
    - [bold red]'--parallel'[/bold red] for local runner to run in parallel\n
    - [bold red]'--group_param'[/bold red] to specify group of parameters to
    run as the same run.\n
    - [bold red]'--storage_path'[/bold red] to override storage path for
    the run of the experiment.\n
    - [bold red]'--tag'[/bold red] to add tag to the run of the experiment.\n
    - [bold red]'--description'[/bold red] to add description to the run of
    the experiment.\n
    """
    run.launch_run_experiment(
            name, ctx, group_param, runner, storage_path, description, tag)


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
    name="action",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("experiment_name", type=click.STRING, required=True)
@click.argument("action_name", type=click.STRING, required=True)
@click.pass_context
def experiment_action(ctx, experiment_name, action_name):
    """Run an action on a run of an experiment.
    Additional option args can be passed to the action after
    experiment and action name."""
    click.echo("TODO")
    click.echo(ctx.args)


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
@config.command()
def show():
    """Show configuration."""
    click.echo("TODO")


@config.command()
@click.argument("file", type=click.Path(exists=True))
def edit(file):
    """Edit configuration with YAML file."""

    # Check whether YAML file
    if not file.endswith(".yaml"):
        rich.print("[bold red]Configuration file must be YAML file.")
        return 1
    click.echo("TODO")


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
