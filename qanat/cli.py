"""Console script for qanat."""
import sys
import rich_click as click
import rich

from .cli_commands.init import init_qanat
from .cli_commands.experiment import (
        command_add_prompt, command_list)

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True

ASCII_ART_use = r"""
                        .
                       _|_
 .-.,  .-.  .--.  .-.   |
(   | (   ) |  | (   )  |
 `-'|  `-'`-'  `- `-'`- `-'
   -|-
    '
"""


@click.group()
@click.version_option(message=ASCII_ART_use + "%(prog)s, version %(version)s")
def main(args=None):
    """Minimal experience management system."""
    return 0


# Main commands
@main.command()
def status():
    """Check status of experiments in this directory."""
    click.echo("TODO")


@main.command()
@click.argument("directory", type=click.Path(exists=True), required=True)
def init(directory):
    """Initialize experiment directory."""
    init_qanat(directory)


@main.group()
def experiment():
    """Experiment-level utility"""
    return 0


@main.group()
def dataset():
    """Dataset-level utility"""
    return 0


@main.group()
def config():
    """Repository configuration utility"""
    click.echo("TODO")


# Subcommands: experiment
@experiment.command(name="list")
def experiment_list():
    """Show list of experiments in this repertory."""
    command_list()


@experiment.command(name="new")
def experiment_new():
    """Create new experiment."""
    command_add_prompt()

@experiment.command(name="show")
@click.argument("name", type=click.STRING, required=True)
def experiment_show():
    """Show runs of experiment."""
    click.echo("TODO")


@experiment.command(name="delete")
@click.argument("name", type=click.STRING, required=True)
def experiment_delete():
    """Delete experiment."""
    click.echo("TODO")


@experiment.command(name="update")
def experiment_update():
    """Update experiment."""
    click.echo("TODO")


@experiment.command(
    name="run",
    context_settings=dict(
        ignore_unknown_options=True,
        allow_extra_args=True,
    ),
)
@click.argument("name", type=click.STRING, required=True)
@click.pass_context
# TODO: Debug this
# fetched from:
# https://stackoverflow.com/questions/32944131/ ...
# add-unspecified-options-to-cli-command-using-python-click
def experiment_run(ctx, name):
    """Run experiment."""
    click.echo("TODO")
    click.echo(ctx.args)
    # click.echo(
    # {ctx.args[i][1:]: ctx.args[i+1] for i in range(0, len(ctx.args), 1)}
    # )


@experiment.command(
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
@dataset.command(name="list")
def dataset_list():
    """Show list of datasets in this repertory."""
    click.echo("TODO")


@dataset.command(name="new")
def dataset_new():
    """Create new dataset."""


@dataset.command(name="delete")
def dataset_delete():
    """Delete dataset."""
    click.echo("TODO")


@dataset.command(name="update")
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
