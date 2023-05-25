import os
import sys
from sqlalchemy.orm import sessionmaker
import subprocess
import rich_click as click
from .database import (
        get_experiment_of_run, RunOfAnExperiment,
        find_action_id, Action, fetch_groupofparameters_of_run
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
                 experiment_name: str,
                 group_no: int = None,):
        self.session_maker = database_sessionmaker
        self.experiment_name = experiment_name
        self.run_id = run_id

        self.group_no = group_no
        Session = self.session_maker()
        self.action_id = find_action_id(
            Session, action_name, experiment_name)
        self.group_parameters = [group.values for group in
                                 fetch_groupofparameters_of_run(
                                  Session, run_id)]

        if self.group_no is not None:
            if self.group_no >= len(self.group_parameters):
                logger.error(
                    f'Group {self.group_no} not found')
                sys.exit(-1)

        if self.action_id == -1:
            logger.error(
                f'Action {action_name} not found')
            sys.exit(-1)

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

        if self.group_no is not None:
            params = self.group_parameters[self.group_no]
            logger.info(f"Executing action '{self.action.name}' "
                        f'on run {self.run_id} of experiment '
                        f'{self.experiment.name} '
                        f'for group {self.group_no}:\n'
                        f'{params}')
        else:
            logger.info(f"Executing action '{self.action.name}' "
                        f'on run {self.run_id} of experiment '
                        f'{self.experiment.name}')

        if ctx is not None:
            args = parse_group_parameters(parse_args_cli(ctx)[0][0])
        else:
            args = []

        if self.group_no is not None:
            folder = os.path.join(
                self.run.storage_path,
                f'group_{self.group_no}'
            )
        else:
            folder = self.run.storage_path

        storage_path_command = ["--storage_path", folder]

        logger.debug(f'Action arguments: {args}')
        logger.info(
            'Action command: ' +
            " ".join(self.command_base + args + storage_path_command))

        subprocess.run(self.command_base + args +
                       storage_path_command)
