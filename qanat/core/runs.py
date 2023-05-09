# ========================================
# FileName: runs.py
# Date: 09 mai 2023 - 08:11
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Manging execution of the runs
# =========================================

import os
from sqlalchemy.orm import sessionmaker
import subprocess
import datetime
import psutil
import rich
from rich.progress import track
import yaml
from .database import (
        get_experiment_of_run, RunOfAnExperiment,
        fetch_groupofparameters_of_run,
        update_run_status
)
from ..utils.logging import setup_logger

logger = setup_logger()


def parse_group_parameters(group_parameters: dict) -> list:
    """Parse dictionary of parameters of a run to
    a list to passe as arguments to subprocess.

    :param group_parameters: Dictionary of parameters
    :type group_parameters: dict

    :return: List of parameters
    :rtype: list
    """

    list_pos_arguments = []
    list_options = []
    for key, value in group_parameters.items():

        # Positional arguments
        if not key.startswith('--'):
            list_pos_arguments.append(value)
        else:
            list_options += [key, value]

    return list_pos_arguments + list_options


class RunExecutionHandler:
    """Template class to handle the execution of the runs.

    Such a class must implement the following methods:
    * setUp(self, database_sessionmaker, run_id)
    * run(self)
    * update_status(self)
    * check_status(self)
    * update_metrics(self)
    """
    def __init__(self, database_sessionmaker: sessionmaker,
                 run_id: int):
        self.session_maker = database_sessionmaker
        self.run_id = run_id
        self.experiment = get_experiment_of_run(self.session_maker(),
                                                run_id)
        self.run = self.session_maker().query(
                RunOfAnExperiment).get(run_id)

    def setUp(self):
        """Set up the execution of the run."""

        # Fetch parameters of the run
        groups_of_parameters = fetch_groupofparameters_of_run(
                self.session_maker(), self.run_id)

        # Constructing directory structure depending on the
        # number of groups of parameters
        if len(groups_of_parameters) == 1:
            logger.info("Single group of parameters detected")
            logger.info(f"Creating {self.run.storage_path}")
            if not os.path.exists(self.run.storage_path):
                os.makedirs(self.run.storage_path)
            self.repertories = [self.run.storage_path]
        else:
            logger.info("Multiple groups of parameters detected:"
                        f" {len(groups_of_parameters)}")
            logger.infot(f"Creating {len(groups_of_parameters)} repertories "
                         "in {self.run.storage_path}")
            if not os.path.exists(self.run.storage_path):
                os.makedirs(self.run.storage_path)

            self.repertories = []
            for i in range(len(groups_of_parameters)):
                path = os.path.join(self.run.storage_path,
                                    'group_'+str(i))
                if not os.path.exists(path):
                    os.makedirs(path)
                self.repertories.append(path)

        # Constructing the commands to run as subprocesses
        self.groups_of_parameters = [parameters.values for
                                     parameters in
                                     fetch_groupofparameters_of_run(
                                         self.session_maker(), self.run_id)]
        self.commands = []
        for i, group_of_parameters in enumerate(self.groups_of_parameters):
            command = [self.experiment.executable_command,
                       self.experiment.executable]
            command += parse_group_parameters(group_of_parameters)
            command += ['--storage_path', self.repertories[i]]
            self.commands.append(command)

        # Saving info about the run in a yaml file
        # To be able to resume the run later or check
        # the status of the run
        info = {'run_id': self.run_id,
                'experiment_id': self.experiment.id,
                'executable': self.experiment.executable,
                'executable_command': self.experiment.executable_command,
                'storage_path': self.run.storage_path,
                'groups_of_parameters': self.groups_of_parameters,
                'commands': self.commands,
                'repertories': self.repertories}
        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'w') as f:
            yaml.dump(info, f)

    def run(self):
        """Run the run."""
        raise NotImplementedError

    def check_status(self):
        """Check the status of the run. Should be independent
        of the execution of the run and hence do not require
        setUp."""
        raise NotImplementedError

    def update_metrics(self):
        """Update the metrics of the run."""
        raise NotImplementedError


class LocalMachineExecutionHandler(RunExecutionHandler):
    """Handle the execution of the runs on the local machine."""

    def __init__(self, database_sessionmaker: sessionmaker,
                 run_id: int, parallel: bool = False):
        super().__init__(database_sessionmaker, run_id)
        self.parallel = parallel

    def run(self):
        """Launch the execution of the run as subprocesses.
        To run after calling setUp().
        """
        logger.info("Launching the execution of the run")
        if self.parallel:
            logger.info(
                    f"Running {len(self.commands)} executions in parallel:")

            # Print list of commands
            rich.print('[bold]List of commands to run:[/bold]')
            for command in self.commands:
                rich.print('- [bold]'+command+'[/bold]')

            processes = []
            pids = []
            for i, command in enumerate(self.commands):
                process = subprocess.Popen(command)
                pids.append(str(process.pid))

            update_run_status(self.session_maker(), self.run_id,
                              "running")

            # Add info in the yaml file
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'r') as f:
                info = yaml.load(f, Loader=yaml.FullLoader)
            info['pids'] = pids
            info['start_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            info['status'] = 'running'
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'w') as f:
                yaml.dump(info, f)

            for process in processes:
                self.pids.append(process.pid)
                process.wait()

            # Add info in the yaml file
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'r') as f:
                info = yaml.load(f, Loader=yaml.FullLoader)
            info['end_time'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            info['status'] = 'finished'
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'w') as f:
                yaml.dump(info, f)

        else:
            logger.info(
                    f"Running in {len(self.commands)} executions sequentially")

            update_run_status(self.session_maker(), self.run_id,
                              "running")

            status_list = ['not_started' for _ in self.commands]
            pid_list = ['' for _ in self.commands]
            start_time_list = ['' for _ in self.commands]
            end_time_list = ['' for _ in self.commands]

            for i, command in track(enumerate(self.commands),
                                    description="Running..."):
                logger.info(f"Running {command}")
                logger.warning("Do not close the terminal window. "
                               "It will cancel the execution of the run.")

                process = subprocess.Popen(command)

                pid = process.pid
                status_list[i] = 'running'
                pid_list[i] = str(pid)
                start_time_list[i] = datetime.now(
                        ).strftime("%d/%m/%Y %H:%M:%S")
                # Add info in the yaml file
                with open(os.path.join(self.run.storage_path,
                                       'info.yaml'), 'r') as f:
                    info = yaml.load(f, Loader=yaml.FullLoader)
                info['start_time'] = start_time_list
                info['status'] = status_list
                info['pid'] = pid_list
                with open(os.path.join(self.run.storage_path,
                                       'info.yaml'), 'w') as f:
                    yaml.dump(info, f)

                # Wait for the process to finish
                process.wait()

                # Command finished
                status_list[i] = 'finished'
                end_time_list[i] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                logger.info(f"Finished {command}\n")

                # Add info in the yaml file
                with open(os.path.join(self.run.storage_path,
                                       'info.yaml'), 'r') as f:
                    info = yaml.load(f, Loader=yaml.FullLoader)
                info['end_time'] = end_time_list
                info['status'] = status_list
                with open(os.path.join(self.run.storage_path,
                          'info.yaml'), 'w') as f:
                    yaml.dump(info, f)

        update_run_status(self.session_maker(), self.run_id,
                          "finished")

    def check_status(self):
        """Check the status of the run."""

        # Check if run in database is marked as finished
        if self.session_maker().query(
                RunOfAnExperiment).filter(
                    RunOfAnExperiment.id == self.run_id).first().status == \
                'finished':
            return "finished"

        # Otherwhise we need more checks

        # Check if yaml file exists
        if not os.path.exists(os.path.join(self.run.storage_path,
                                           'info.yaml')):
            return "not_started"

        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'r') as f:
            info = yaml.load(f, Loader=yaml.FullLoader)

        # Test wheter cancelled or running
        pids = info['pids']

        # Check if all processes are finished
        if not all(psutil.pid_exists(pid) for pid in pids):
            return "cancelled"
        else:
            return "running"
