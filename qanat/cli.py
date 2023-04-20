"""Console script for qanat."""
import argparse
import sys


ASCII_ART_alt = r"""
      ___           ___           ___           ___           ___
     /\  \         /\  \         /\__\         /\  \         /\  \
    /::\  \       /::\  \       /::|  |       /::\  \        \:\  \
   /:/\:\  \     /:/\:\  \     /:|:|  |      /:/\:\  \        \:\  \
   \:\~\:\  \   /::\~\:\  \   /:/|:|  |__   /::\~\:\  \       /::\  \
    \:\ \:\__\ /:/\:\ \:\__\ /:/ |:| /\__\ /:/\:\ \:\__\     /:/\:\__\
     \:\/:/  / \/__\:\/:/  / \/__|:|/:/  / \/__\:\/:/  /    /:/  \/__/
      \::/  /       \::/  /      |:/:/  /       \::/  /    /:/  /
      /:/  /        /:/  /       |::/  /        /:/  /     \/__/
     /:/  /        /:/  /        /:/  /        /:/  /
     \/__/         \/__/         \/__/         \/__/

"""

ASCII_ART_use = r"""

                        .
                       _|_
 .-.,  .-.  .--.  .-.   |
(   | (   ) |  | (   )  |
 `-'|  `-'`-'  `- `-'`- `-'
   -|-
    '
"""


class QanatCli:
    """Qanat Command Line Tools Interface class to handle several
    commands as per argparse subcommands:
    https://docs.python.org/3/library/argparse.html#sub-commands
    """

    def __init__(self):
        self.main_parser = argparse.ArgumentParser(
            prog="qanat",
            description=ASCII_ART_use
            + "Qanat cli interface for experiment tracking.\n",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        self.main_parser.add_argument(
            "--version",
            action="version",
            version="%(prog)s 0.1.0",
        )
        self.subparsers = self.main_parser.add_subparsers(
            title="commands",
            dest="command",
        )

        # init subcommands
        self.init_parser = self.subparsers.add_parser(
            "init",
            help="Initialize a new qanat project.",
        )
        self.init_parser.add_argument(
            "path",
            help="Path to the project directory.",
        )

        # status subcommands
        self.status_parser = self.subparsers.add_parser(
            "status",
            help="Show the status of the current project.",
        )

    def run(self):
        args = self.main_parser.parse_args()
        if args.command == "init":
            print("init")
        elif args.command == "status":
            print("status")
        else:
            self.main_parser.print_help()


def main():
    """Console script for qanat."""
    cli = QanatCli()
    cli.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
