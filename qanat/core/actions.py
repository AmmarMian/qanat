import os
from sqlalchemy.orm import sessionmaker
import subprocess
import rich
import rich_click as click
from .database import (
        get_experiment_of_run, RunOfAnExperiment,
        find_action_id, Action
)
from ..utils.logging import setup_logger
from ..utils.parsing import parse_args_cli, parse_group_parameters

logger = setup_logger()


class ActionExecutionHandler:
    """A class to handle the execution of
    actions on a run of an experiment.
    """

    def __init__(self, database_sessionmaker: sessionmaker,
                 run_id: int, action_name: str,
                 experiment_name: str):
        self.session_maker = database_sessionmaker
        self.experiment_name = experiment_name
        self.run_id = run_id
        Session = self.session_maker()
        self.action_id = find_action_id(
            Session, action_name, experiment_name)

        if self.action_id == -1:
            raise AttributeError(f'Action {action_name} not found')

        self.action = Session.query(Action).get(
            self.action_id
        )
        self.experiment = get_experiment_of_run(
            Session, run_id)
        self.run = Session.query(
                RunOfAnExperiment).get(run_id)
        Session.close()

        self.command_base = [self.action.executable_command,
                             self.action.executable]

    def execute_action(self, ctx: click.Context):
        """Execute action with arguments.

        :param ctx: click context
        :type ctx: click.Context
        """
        logger.info(f"Executing action '{self.action.name}' "
                    f'on run {self.run_id} of experiment '
                    f'{self.experiment.name}')

        if ctx is not None:
            args = parse_group_parameters(parse_args_cli(ctx)[0][0])
        else:
            args = []
        storage_path_command = ["--storage_path", self.run.storage_path]

        logger.debug(f'Action arguments: {args}')
        logger.info(
            'Action command: '  + \
            " ".join(self.command_base + args + storage_path_command))

        subprocess.run(self.command_base + args + \
                       storage_path_command)
