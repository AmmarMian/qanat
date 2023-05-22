# ========================================
# FileName: runs.py
# Date: 09 mai 2023 - 08:11
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Manging execution of the runs
# =========================================

import time
import sys
import shutil
import os
import signal
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
        update_run_status, update_run_finish_time,
        update_run_start_time
)
from ..utils.logging import setup_logger
from ..utils.misc import reverse_readline
from ..utils.parsing import parse_group_parameters
logger = setup_logger()

try:
    import warnings
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
    import htcondor
    from htcondor import (
        JobEventLog,
        JobEventType
    )

except ImportError:
    logger.info("HTCondor python bindings not available on system. "
                "Please install htcondor if available: "
                "pip install htcondor")


def parse_executionhandler(executionhandler: str):
    """Parse the execution handler from a string.

    :param executionhandler: The execution handler as a string.
    :type executionhandler: str
    """

    if executionhandler == 'local':
        return LocalMachineExecutionHandler
    elif executionhandler == 'htcondor':
        return HTCondorExecutionHandler
    else:
        raise ValueError(f"Unknown execution handler {executionhandler}")


class RunExecutionHandler:
    """Template class to handle the execution of the runs.

    Such a class must implement the following methods:
    * setUp(self, database_sessionmaker, run_id)
    * run_experiment(self)
    * cancel_experiment(self)
    * check_status(self)
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

        # Constructing the commands to run as subprocesses for local
        # execution
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
                'commands': self.commands,
                'groups_of_parameters': self.groups_of_parameters,
                'repertories': self.repertories}
        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'w') as f:
            yaml.dump(info, f)
        Session.close()

    def parse_yaml_file(self) -> dict:
        """Parse YAML info file

        :return dict: The info dictionary
        """
        try:
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'r') as f:
                info = yaml.load(f, Loader=yaml.FullLoader)
            return info

        except FileNotFoundError:
            logger.error(f"No info.yaml file found for run {self.run.id}.")
            return None

    def update_yaml_file(self, info: dict):
        """Update YAML info file

        :param dict info: The info dictionary
        """
        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'w') as f:
            yaml.dump(info, f)

    def run_experiment(self):
        """Run the run."""
        raise NotImplementedError

    def cancel_experiment(self):
        """Cancel the run."""
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
                 run_id: int, n_threads: int = 1):
        super().__init__(database_sessionmaker, run_id)
        self.n_threads = n_threads
        self.process_pid = os.getpid()
        signal.signal(signal.SIGINT, self.sigint_handler)
        self.console = rich.console.Console()
        self.progress = None

    def sigint_handler(self, signum, frame):
        """Handle the SIGINT signal."""
        self.cancel_experiment()


    def run_experiment(self):
        """Launch the execution of the run as subprocesses.
        To run after calling setUp().
        """
        logger.info("Launching the execution of the run")
        launched_time = datetime.now()

        info = self.parse_yaml_file()
        info['main_pid'] = self.process_pid
        self.update_yaml_file(info)

        Session = self.session_maker()
        Session.query(RunOfAnExperiment).filter(
                RunOfAnExperiment.id == self.run_id).update(
                {'launched': launched_time})
        if self.n_threads > 1:
            logger.info(
                    f"Running {len(self.commands)} executions in parallel:"
                    f" {max(self.n_threads, len(self.commands))} threads")
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
            status_list = []


            with self.console.status(
                    "[bold green]Running...", spinner='dots'):
                stdout_list = []
                stderr_list = []

                # Creating sequence of commands to runs at
                # different times
                commands_sequences = []
                command_one_sequence = []
                repertories_sequences = []
                repertories_one_sequence = []
                i_start = 0
                for i, command in enumerate(self.commands):
                    command_one_sequence.append(command)
                    repertories_one_sequence.append(self.repertories[i])
                    if (i+1) % self.n_threads == 0 or \
                        (i == len(self.commands)-1 and
                        (len(self.commands)-i_start) <= self.n_threads):
                        commands_sequences.append(command_one_sequence)
                        repertories_sequences.append(repertories_one_sequence)
                        command_one_sequence = []
                        repertories_one_sequence = []
                        i_start = i+1

                for i, (command_sequence, repertory_sequence) in \
                        enumerate(zip(
                            commands_sequences, repertories_sequences)):

                    logger.info(f"Running {i+1}/{len(commands_sequences)} "
                                "sequence of commands:")
                    for command in command_sequence:
                        logger.info("- " + " ".join(command))

                    for command, repertory in zip(command_sequence,
                                                  repertory_sequence):
                        stdout_file = open(os.path.join(repertory,
                                                        'stdout.txt'), 'w')
                        stderr_file = open(os.path.join(repertory,
                                                        'stderr.txt'), 'w')
                        stdout_list.append(stdout_file)
                        stderr_list.append(stderr_file)
                        process = subprocess.Popen(command,
                                                   stdout=stdout_file,
                                                   stderr=stderr_file)
                        pids.append(str(process.pid))
                        processes.append(process)
                        status_list.append('running')

                    if self.run.status != 'running':
                        self.run.status = 'running'
                        update_run_status(Session, self.run_id,
                                          "running")
                    Session.close()

                    # Add info in the yaml file
                    info = self.parse_yaml_file()
                    info['pids'] = pids
                    if 'start_time' not in info:
                        info['start_time'] = datetime.now()
                    info['status'] = status_list
                    self.update_yaml_file(info)

                    for i, process in enumerate(processes):
                        process.wait()
                        if process.returncode != 0:
                            status_list[i] = 'error'
                        else:
                            status_list[i] = 'finished'
                        stdout_list[i].close()
                        stderr_list[i].close()

            # Add info in the yaml file
            info = self.parse_yaml_file()
            info['end_time'] = datetime.now()
            info['status'] = status_list
            self.update_yaml_file(info)

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

            self.progress = Progress(
                 SpinnerColumn(),
                 TextColumn("[bold blue]{task.description}"),
                 BarColumn(bar_width=None),
                 "[progress.percentage]{task.percentage:>3.0f}%")
            with self.progress as progress:
                task = progress.add_task("Running..", total=len(self.commands))
                for i, command in enumerate(self.commands):
                    logger.info("Running '" + " ".join(command) + "'")
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
                    info = self.parse_yaml_file()
                    info['start_time'] = start_time_list
                    info['status'] = status_list
                    info['pids'] = pid_list
                    self.update_yaml_file(info)

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
                    info = self.parse_yaml_file()
                    info['end_time'] = end_time_list
                    info['status'] = status_list
                    self.update_yaml_file(info)

                    progress.update(task, advance=1)

        logger.info("Updating database with finished time")
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                          "finished")
        update_run_finish_time(Session, self.run_id)
        Session.close()

    def cancel_experiment(self):
        """Cancel the run."""

        # Check if run is running
        if self.check_status() != "running":
            logger.info("Run is not running. Nothing to cancel.")
            return 0
        elif self.check_status() == "finished" or \
                self.check_status() == "cancelled":
            logger.info(f"Run is {self.check_status()}. Nothing to cancel.")
            return 0

        # Get the pids of the processes
        try:
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'r') as f:
                info = yaml.load(f, Loader=yaml.FullLoader)
            pids = info['pids']

            # Kill the processes
            logger.info("Killing the processes: "
                        f"{', '.join(pids)}")
            for pid in pids:
                try:
                    if pid != '':
                        os.kill(int(pid), signal.SIGTERM)
                except ProcessLookupError:
                    logger.info(f"Process {pid} already killed or finished.")
            logger.info("Processes killed.")

            # Update the status of the run
            Session = self.session_maker()
            update_run_status(Session, self.run_id,
                              "cancelled")

            # Update the YAML file
            info['status'] = ['cancelled' for _ in info['status']]
            info['end_time'] = datetime.now()
            with open(os.path.join(self.run.storage_path,
                                   'info.yaml'), 'w') as f:
                yaml.dump(info, f)

            # Close the session
            Session.close()

            logger.info("Run cancelled.")

            # Quit the program
            sys.exit(-1)

        except FileNotFoundError:
            logger.info("Run was not started. Nothing to cancel.")
            return 0

    def check_status(self):
        """Check the status of the run."""

        status = "unknown"
        Session = self.session_maker()
        # Check if run in database is marked as finished or cancelled
        if Session.query(
                RunOfAnExperiment).filter_by(id=self.run_id).first().status \
                == "finished":
            status = "finished"
        elif Session.query(
                RunOfAnExperiment).filter_by(id=self.run_id).first().status \
                == "cancelled":
            status = "cancelled"

        Session.close()
        if status != "unknown":
            return status

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
            pids = info['pids']

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


class HTCondorExecutionHandler(RunExecutionHandler):
    """Class for excuting run as jobs through an HTCondor
    job submission system.

    Reminder for HTcondor job status:
    0	Unexpanded 	U
    1	Idle 	I
    2	Running 	R
    3	Removed 	X
    4	Completed 	C
    5	Held 	H
    6	Submission_err 	E
    """

    def __init__(self, database_sessionmaker, run_id,
                 htcondor_submit_options=None):
        super().__init__(database_sessionmaker, run_id)

        # Check wheter htcondor is available on system
        if not shutil.which('condor_submit'):
            logger.warning("HTCondor not available on system.")
            self.htcondor_available = False
        else:
            self.htcondor_available = True

        self.htcondor_submit_options = htcondor_submit_options

    def run_experiment(self):
        """Run the experiment."""

        if not self.htcondor_available:
            logger.error("HTCondor not available on system.")
            sys.exit(-1)

        # Getting schedd
        schedd = htcondor.Schedd()

        # Submit all jobs
        cluster_ids = []
        submit_dicts = []
        for command, repertory in zip(self.commands,
                                      self.repertories):

            str_command = " ".join(command)

            # Create new executable file
            executable = os.path.join(repertory, 'executable.sh')
            with open(executable, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write('echo "Running on host: $HOSTNAME"\n')
                f.write('echo "Starting at: $(date)"\n\n')

                f.write(f'echo "Moving to repertory {os.getcwd()}"\n')
                f.write(f'cd {os.getcwd()}\n\n')

                f.write(f'echo "Running command: {str_command}"\n')
                f.write(str_command + '\n\n' )
                f.write('echo "Done."')

            # TODO: bind paths of datasets and stuff...
            # TODO: Maybe not harcode some stuff...
            submit_dict = {
                'executable': executable,
                'output': os.path.join(repertory, 'stdout.txt'),
                'error': os.path.join(repertory, 'stderr.txt'),
                'log': os.path.join(repertory, 'log.txt'),
                'should_transfer_files': 'YES',
                'when_to_transfer_output': 'ON_EXIT',
                'batch_name': f"{self.experiment.name}_{self.run_id}"
            }
            if self.htcondor_submit_options is not None:
                submit_dict.update(self.htcondor_submit_options)

            # Submit the job
            logger.info(f"Submitting job for command {str_command}")
            job = htcondor.Submit(submit_dict)
            submit_result = schedd.submit(job)
            cluster_ids.append(submit_result.cluster())
            submit_dicts.append(submit_dict)

        # Update the database
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                          'running')
        Session.commit()
        Session.close()

        # Update the YAML file
        info = self.parse_yaml_file()
        info['status'] = 'running'
        info['start_time'] = datetime.now()
        info['cluster_ids'] = cluster_ids
        info['submit_dicts'] = submit_dicts
        self.update_yaml_file(info)

        logger.info("Jobs submitted to clusters " + " ".join(str(cluster_ids)))

    def check_status(self):
        """Check the status of the run."""

        # Read info from YAML file
        info = self.parse_yaml_file()
        if info is None:
            return "unknown"
        elif info['status'] == 'finished':
            return "finished"
        elif info['status'] == 'cancelled':
            return "cancelled"

        # Get the log files events for
        # each job
        status_list = ['unknown' for _ in info['cluster_ids']]
        launch_times = [None for _ in info['cluster_ids']]
        finish_times = [None for _ in info['cluster_ids']]
        for i, repertory in enumerate(info['repertories']):

            log_file = os.path.join(repertory, 'log.txt')
            if not os.path.exists(log_file):
                continue
            events = [event for event in JobEventLog(log_file).events(stop_after=0)]
            last_event = events[-1]

            # Adapt status in function of last event
            if last_event.type == JobEventType.SUBMIT:
                status = 'not_started'
            elif last_event.type == JobEventType.EXECUTE:
                status = 'running'
            elif last_event.type == JobEventType.JOB_TERMINATED:
                status = 'finished'
            elif last_event.type == JobEventType.JOB_HELD:
                status = 'held'
            elif last_event.type == JobEventType.JOB_RELEASED:
                status = 'running'
            elif last_event.type == JobEventType.JOB_ABORTED:
                status = 'cancelled'
            else:
                status = 'unknown'

            status_list[i] = status

            # Get launch time
            for event in events:
                if event.type == JobEventType.EXECUTE:
                    launch_times[i] = datetime.fromtimestamp(event.timestamp)
                    break

            # Get the finish time
            for event in events:
                if event.type == JobEventType.JOB_TERMINATED or \
                     event.type == JobEventType.JOB_ABORTED:
                    finish_times[i] = datetime.fromtimestamp(event.timestamp)
                    break

        # Update global status according to status of jobs
        if any([status == 'running' for status in status_list]):
            global_status = 'running'
        elif all([status == 'finished' for status in status_list]):
            global_status = 'finished'
        elif any([status == 'cancelled' for status in status_list]):
            global_status = 'cancelled'
        elif any([status == 'held' for status in status_list]):
            global_status = 'held'
        elif all([status == 'not_started' for status in status_list]):
            global_status = 'not_started'
        else:
            global_status = 'unknown'

        # Get first launch time
        launch_times = [launch_time for launch_time in launch_times
                        if launch_time is not None]
        if len(launch_times) > 0:
            launch_time = min(launch_times)
        else:
            launch_time = None

        # Get last finish time if all jobs are finished
        if global_status == 'finished':
            finish_times = [finish_time for finish_time in finish_times
                            if finish_time is not None]
            finish_time = max(finish_times)
        else:
            finish_time = None

        # Update the database
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                          global_status)
        if launch_time is not None:
            update_run_start_time(Session, self.run_id,
                                  launch_time)
        if finish_time is not None:
            update_run_finish_time(Session, self.run_id,
                                   finish_time)
        Session.commit()
        Session.close()

        # Update the YAML file
        info['status'] = global_status
        self.update_yaml_file(info)

        return global_status

    def cancel_experiment(self):
        """Cancel a run of the experiment."""

        info = self.parse_yaml_file()
        if info is None:
            logger.warning(f"Run {self.run_id} doesn't have a info.yaml file")
            logger.warning("Probably due to it being not started or some error")
            logger.info("Try waiting for it to launch or delete the run altogether")
            return

        # Removing jobs that are removable
        schedd = htcondor.Schedd()
        for cluster_id in info['cluster_ids']:
            query = schedd.query(f'ClusterId == {cluster_id}')
            if len(query) >= 1:
                if query[0]['JobStatus'] in [1, 2, 5]:
                    schedd.act(
                        htcondor.JobAction.Remove,
                        f"ClusterId == {cluster_id}")

        # Updating YAML file
        info["status"] = "cancelled"
        self.update_yaml_file(info)

        # Update database
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                            'cancelled')
        Session.close()
