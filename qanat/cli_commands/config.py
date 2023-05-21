import yaml
import rich
from rich.prompt import Confirm
from ..utils.logging import setup_logger

logger = setup_logger()

def command_show():
    """Show configuration."""
    with open(".qanat/config.yaml", "r") as f:
        config = yaml.safe_load(f)
    rich.print(config)


def command_edit(file_path: str):
    """Update .qanat/config.yaml with new configuration file.

    :param file_path: path to new configuration file
    :type file_path: str
    """
    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    rich.print("[bold]Old configuration is:")
    command_show()
    rich.print("[bold]New configuration is:")
    rich.print(config)

    if Confirm.ask("Do you want to update configuration?"
                    "This will overwrite the old configuration."
                    "[bold red]This action cannot be undone.[/bold red]",
                    default="n", show_default=True):
        with open(".qanat/config.yaml", "w") as f:
            yaml.dump(config, f)
        logger.info("Configuration updated.")