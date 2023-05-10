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
from datetime import datetime
import psutil
import rich
from rich.progress import (
        Progress, SpinnerColumn, BarColumn, TextColumn
)
import yaml
from .database import (
        get_experiment_of_run, RunOfAnExperiment,
        fetch_groupofparameters_of_run,
        update_run_status, update_run_finish_time
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
    * run_experiment(self)
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
        Session = self.session_maker()
        self.run = Session.query(
                RunOfAnExperiment).get(run_id)
        Session.close()

    def setUp(self):
        """Set up the execution of the run."""

        # Fetch parameters of the run
        Session = self.session_maker()
        groups_of_parameters = fetch_groupofparameters_of_run(
                Session, self.run_id)

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
            logger.info(f"Creating {len(groups_of_parameters)} repertories "
                        f"in {self.run.storage_path}")
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
                                         Session, self.run_id)]
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

        Session.close()

    def run_experiment(self):
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

    def run_experiment(self):
        """Launch the execution of the run as subprocesses.
        To run after calling setUp().
        """
        logger.info("Launching the execution of the run")
        launched_time = datetime.now()

        Session = self.session_maker()
        Session.query(RunOfAnExperiment).filter(
                RunOfAnExperiment.id == self.run_id).update(
                {'launched': launched_time})
        if self.parallel:
            logger.info(
                    f"Running {len(self.commands)} executions in parallel:")
            logger.info("The output of the executions will be "
                           f"redirected to {self.run.storage_path}")
            logger.warning('Do not interrupt the program or the '
                           'executions will be interrupted')

            # Print list of commands
            rich.print('[bold]List of commands to run:[/bold]')
            for command in self.commands:
                rich.print('- [bold]'+' '.join(command)+'[/bold]')

            processes = []
            pids = []

            console = rich.console.Console()
            with console.status(
                    "[bold green]Running...", spinner='dots') as status:
                stdout_list = []
                stderr_list = []
                for i, command in enumerate(self.commands):
                    stdout_file = open(os.path.join(self.repertories[i],
                                                    'stdout.txt'), 'w')
                    stderr_file = open(os.path.join(self.repertories[i],
                                                    'stderr.txt'), 'w')
                    stdout_list.append(stdout_file)
                    stderr_list.append(stderr_file)
                    process = subprocess.Popen(command,
                                               stdout=stdout_file,
                                               stderr=stderr_file)
                    pids.append(str(process.pid))
                    processes.append(process)

                update_run_status(Session, self.run_id,
                                  "running")
                Session.close()

                # Add info in the yaml file
                with open(os.path.join(self.run.storage_path,
                                       'info.yaml'), 'r') as f:
                    info = yaml.load(f, Loader=yaml.FullLoader)
                info['pids'] = pids
                info['start_time'] = datetime.now()
                info['status'] = 'running'
                with open(os.path.join(self.run.storage_path,
                                       'info.yaml'), 'w') as f:
                    yaml.dump(info, f)

                for i, process in enumerate(processes):
                    process.wait()
                    stdout_list[i].close()
                    stderr_list[i].close()

            # Add info in the yaml file
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'r') as f:
                info = yaml.load(f, Loader=yaml.FullLoader)
            info['end_time'] = datetime.now()
            info['status'] = 'finished'
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'w') as f:
                yaml.dump(info, f)

            Session = self.session_maker()
            update_run_status(Session, self.run_id,
                              "finished")
            Session.close()

        else:
            logger.info(
                    f"Running {len(self.commands)} executions sequentially")
            logger.info("The output of the executions will be "
                        f"redirected to {self.run.storage_path}")

            update_run_status(Session, self.run_id,
                              "running")
            Session.close()

            status_list = ['not_started' for _ in self.commands]
            pid_list = ['' for _ in self.commands]
            start_time_list = ['' for _ in self.commands]
            end_time_list = ['' for _ in self.commands]

            with Progress(
                 SpinnerColumn(),
                 TextColumn("[bold blue]{task.description}"),
                 BarColumn(bar_width=None),
                 "[progress.percentage]{task.percentage:>3.0f}%") as progress:
                task = progress.add_task("Running..", total=len(self.commands))
                for i, command in enumerate(self.commands):
                    logger.info(f"Running {command}")
                    logger.warning("Do not close the terminal window. "
                                   "It will cancel the execution of the run.")

                    # Redirect stdout and stderr of the subprocess
                    # to a file
                    stdout_file = os.path.join(self.repertories[i],
                                               'stdout.txt')
                    stderr_file = os.path.join(self.repertories[i],
                                               'stderr.txt')
                    stdout = open(stdout_file, 'w')
                    stderr = open(stderr_file, 'w')
                    process = subprocess.Popen(command, stdout=stdout,
                                               stderr=stderr)

                    pid = process.pid
                    status_list[i] = 'running'
                    pid_list[i] = str(pid)
                    start_time_list[i] = datetime.now()
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

                    # Close the files
                    stdout.close()
                    stderr.close()

                    # Command finished
                    status_list[i] = 'finished'
                    end_time_list[i] = datetime.now()
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

                    progress.update(task, advance=1)

        logger.info("Updating databse with finished time")
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                          "finished")
        update_run_finish_time(Session, self.run_id)
        Session.close()

    def check_status(self):
        """Check the status of the run."""

        Session = self.session_maker()
        # Check if run in database is marked as finished
        if Session.query(
                RunOfAnExperiment).filter(
                    RunOfAnExperiment.id == self.run_id).first().status == \
                'finished':
            return "finished"
        Session.close()

        # Otherwhise we need more checks

        # Check if yaml file exists
        if not os.path.exists(os.path.join(self.run.storage_path,
                                           'info.yaml')):
            return "not_started"

        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'r') as f:
            info = yaml.load(f, Loader=yaml.FullLoader)

        # Test wheter cancelled, running or finished
        if any(status == "running" for status in info['status']):
            pids = info['pid']

            # Check if at least one pid is still running
            if not any(psutil.pid_exists(int(pid))
                       for pid in pids if pid != ''):
                return "cancelled"
            else:
                return "running"
        else:
            if all(status == 'finished' for status in info['status']):
                return "finished"
            else:
                return "running"
