# ========================================
# FileName: runs.py
# Date: 09 mai 2023 - 08:11
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Manging execution of the runs
# =========================================

import git
import sys
import shutil
import time
import os
import signal
from filelock import FileLock
from sqlalchemy.orm import sessionmaker
import subprocess
from datetime import datetime, timedelta
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
        update_run_start_time, fetch_datasets_of_experiment
)
from .containers import get_container_run_command
from ..utils.logging import setup_logger
from ..utils.parsing import (
        parse_group_parameters,
        get_absolute_path)
from ..utils.misc import reverse_readline
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

    if os.path.exists(os.path.join('.qanat/config.yaml')):
        with open(os.path.join('.qanat/config.yaml'), 'r') as f:
            config = yaml.safe_load(f)
        if not config.get('nohtcondorwarning', False):
            logger.info("HTCondor python bindings not available on system. "
                        "Please install htcondor if available: "
                        "pip install htcondor")
            logger.info("To silence this message, add the following line "
                        "to your .qanat/config.yml file:")
            logger.info("nohtcondorwarning: True")


WAIT_TIME_INTERVAL_CHECK = 10  # seconds


def get_progress(repertory_path: str) -> float:
    """Get the progress of the run thanks to a progress.txt
    file in the repertory.

    :param repertory_path: The path to the repertory.
    :type repertory_path: str

    :return: The progress of the run in percent.
    :rtype: float
    """
    progress_path = os.path.join(repertory_path, "progress.txt")
    if not os.path.exists(progress_path):
        return None

    # If last line contains keyword "finished"
    # then the run is finished
    reader = reverse_readline(progress_path)
    last_line = next(reader)
    if 'finished' in last_line:
        return 100

    # First line to parse gives the total count
    # Then each line gives a count progress
    # Total is the sum of all counts
    with open(progress_path, 'r') as f:
        lines = f.readlines()

        # Fetching type of progress
        try:
            progress_type = lines[0].split('=')[0].strip()
        except NameError:
            logger.debug(f"Could not parse progress type in {progress_path}")
            return None
        if progress_type.lower() == 'count_total':
            total = int(lines[0].split('count_total=')[1].strip())
            counts = [int(line.split()[0]) for line in lines[1:]
                      if line.strip() != '']
            percent = sum(counts) / total * 100
        elif progress_type.lower() == 'tqdm':
            last_progress_line = 1
            found = False
            while not found and last_progress_line < len(lines):
                try:
                    percent = float(
                            lines[-last_progress_line].strip(' ').split(
                                ' ')[0].split('|')[0][:-1])
                    found = True
                except ValueError:
                    last_progress_line += 1
            if not found:
                logger.debug(f"Could not parse progress in {progress_path}")
                return None
        else:
            logger.debug(f"Unknown progress type {progress_type}")
            return None
    return percent


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
    * check_progress(self)
    """
    def __init__(self, database_sessionmaker: sessionmaker,
                 run_id: int,
                 container_path: str = None,
                 commit_sha: str = None):
        self.session_maker = database_sessionmaker
        self.run_id = run_id
        self.commit_sha = commit_sha
        self.experiment = get_experiment_of_run(self.session_maker(),
                                                run_id)
        self.container_path = container_path
        Session = self.session_maker()
        self.run = Session.query(
                RunOfAnExperiment).get(run_id)
        Session.close()

        #  Transfrom run storage_path to absolute path
        self.run.storage_path = get_absolute_path(self.run.storage_path)
        self.working_dir = os.getcwd()

    def setup_specific_commit_run(self):
        """Set up things if we are running a specific commit.
        We create a copy of the git repository in .qanat/cache/commit_sha
        and we checkout the specific commit.
        """

        if self.commit_sha is None:
            return

        # Create a copy of the git repository in .qanat/cache/commit_sha
        # and checkout the specific commit
        cache_path = os.path.join(os.getcwd(), '.qanat', 'cache')
        logger.info(f"Setting up specific commit {self.commit_sha}"
                    f"in {cache_path}")
        if not os.path.exists(cache_path):
            os.makedirs(cache_path)
        repo_cwd = git.Repo(os.getcwd())
        repo_path = os.path.join(cache_path, self.commit_sha)
        if not os.path.exists(repo_path):
            repo_commit = repo_cwd.clone(repo_path, no_checkout=True)
        else:
            repo_commit = git.Repo(repo_path)
        logger.info(f"Checking out {self.commit_sha}")
        repo_commit.git.checkout(self.commit_sha)
        self.working_dir = repo_path

    def setUp(self):
        """Set up the execution of the run."""

        # If we need to run a specific commit
        self.setup_specific_commit_run()

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

        # Constructing the commands to run
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

        # Managing container execution
        if self.container_path is not None:
            if os.path.exists(self.container_path):
                bind_paths = {
                        self.run.storage_path:
                        self.run.storage_path,
                        self.working_dir:
                        self.working_dir
                }

                # Get datasets paths to bind as well
                Session = self.session_maker()
                datasets = fetch_datasets_of_experiment(
                        Session, self.experiment.name)
                Session.close()

                for dataset in datasets:
                    absolute_path = get_absolute_path(dataset.path)
                    bind_paths[absolute_path] = absolute_path

                self.commands = [get_container_run_command(
                    get_absolute_path(self.container_path),
                    command, bind_paths)
                    for command in self.commands]
            else:
                raise FileNotFoundError(f"Container path {self.container_path}"
                                        " does not exist")

        # Saving info about the run in a yaml file
        # To be able to resume the run later or check
        # the status of the run
        self.write_groups_info()

        info = {'run_id': self.run_id,
                'experiment_id': self.experiment.id,
                'executable': self.experiment.executable,
                'executable_command': self.experiment.executable_command,
                'storage_path': self.run.storage_path,
                'commands': [" ".join([str(c) for c in command])
                             for command in self.commands],
                'groups_of_parameters': self.groups_of_parameters,
                'repertories': self.repertories,
                'working_directory': self.working_dir}
        if self.commit_sha is not None:
            info['commit_sha'] = self.commit_sha
        else:
            info['commit_sha'] = git.Repo(os.getcwd()).head.commit.hexsha

        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'w') as f:
            yaml.dump(info, f)
        Session.close()

    def write_groups_info(self):
        """Write group information in the repertory"""

        for command, group_of_parameters, repertory in zip(
                self.commands, self.groups_of_parameters, self.repertories):
            group_info = {'command': " ".join([str(c) for c in command]),
                          'parameters': group_of_parameters}
            with open(os.path.join(repertory, 'group_info.yaml'), 'w') as f:
                yaml.dump(group_info, f)

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

        except yaml.YAMLError as exc:
            logger.error(f"Error while parsing info.yaml file for run "
                         f"{self.run.id}.")
            logger.error(exc)
            return None

    def update_yaml_file(self, info: dict):
        """Update YAML info file

        :param dict info: The info dictionary
        """
        with open(os.path.join(self.run.storage_path,
                               'info.yaml'), 'w') as f:
            yaml.dump(info, f)

    def check_progress(self) -> float:
        """Check the progress of the run.

        :return float: The progress of the run
        """

        info = self.parse_yaml_file()
        if info is None:
            return None

        repertories = info['repertories']

        # Check if all repertories have a progress file
        repertories_with_progress = []
        for repertory in repertories:
            if os.path.exists(os.path.join(repertory, 'progress.txt')):
                repertories_with_progress.append(repertory)

        if len(repertories_with_progress) == 0:
            return None

        progress = 0
        for repertory in repertories_with_progress:
            try:
                progress_group = get_progress(repertory)
                progress += progress_group
                if progress_group is None:
                    return None
            except Exception as e:
                logger.error(f"Error while getting progress of run"
                             f" {self.run.id}: {e}")
                return None
        return progress / len(repertories)

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
                 run_id: int, n_threads: int = 1, container_path: str = None,
                 commit_sha: str = None,
                 only_check_status: bool = False):
        super().__init__(database_sessionmaker, run_id, container_path,
                         commit_sha)
        self.n_threads = n_threads
        self.process_pid = os.getpid()
        if not only_check_status:
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
                command = [str(c) for c in command]
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
                        command_str = " ".join([str(c) for c in command])
                        logger.info(f"- {command_str}")

                    for command, repertory in zip(command_sequence,
                                                  repertory_sequence):
                        command = [str(c) for c in command]
                        stdout_file = open(os.path.join(repertory,
                                                        'stdout.txt'), 'w')
                        stderr_file = open(os.path.join(repertory,
                                                        'stderr.txt'), 'w')
                        stdout_list.append(stdout_file)
                        stderr_list.append(stderr_file)
                        process = subprocess.Popen(command,
                                                   stdout=stdout_file,
                                                   stderr=stderr_file,
                                                   cwd=self.working_dir)
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
                    command_str = " ".join([str(x) for x in command])
                    logger.info(f"Running '{command_str}'")
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
                    command = [str(x) for x in command]
                    process = subprocess.Popen(command, stdout=stdout,
                                               stderr=stderr,
                                               cwd=self.working_dir)

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
        elif self.check_status() == "finished" or \
                self.check_status() == "cancelled":
            logger.info(f"Run is {self.check_status()}. Nothing to cancel.")

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
            info['status'] = ['cancelled' for _ in info['pids']]
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
        if info is None:
            return "unknown"

        if 'status' not in info.keys():
            return "not_started"

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
                 htcondor_submit_options=None,
                 container_path: str = None,
                 commit_sha: str = None,
                 wait: bool = False):
        super().__init__(database_sessionmaker, run_id, container_path,
                         commit_sha)

        # Check wheter htcondor is available on system
        if not shutil.which('condor_submit'):
            logger.warning("HTCondor not available on system.")
            self.htcondor_available = False
        else:
            self.htcondor_available = True

        self.htcondor_submit_options = htcondor_submit_options
        self.wait = wait

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

            str_command = " ".join([str(x) for x in command])

            # Create new executable file
            executable = os.path.join(repertory, 'executable.sh')
            with open(executable, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write('echo "Running on host: $HOSTNAME"\n')
                f.write('echo "Starting at: $(date)"\n\n')

                f.write(f'echo "Moving to repertory {self.working_dir}"\n')
                f.write(f'cd {self.working_dir}\n\n')
                f.write('pwd\n')

                f.write(f'echo "Running command: {str_command}"\n')
                f.write(str_command + '\n\n')
                f.write('echo "Done."')

            # TODO: Maybe not hardcode some stuff...
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

        self.cluster_ids = cluster_ids

        logger.info("Jobs submitted to clusters " + " ".join(str(cluster_ids)))

        if self.wait:
            self.wait_end()

    def wait_end(self):
        """Wait until all jobs are finished."""

        logger.info("Wait flag has been activated.")
        console = rich.console.Console()
        with console.status("Waiting for jobs to finish...",
                            spinner="dots") as status:
            last_status = self.check_status()
            while last_status in ["running", "unknown",
                                  "not_started"]:
                time.sleep(WAIT_TIME_INTERVAL_CHECK)
                progress = self.check_progress()
                if progress is not None:
                    status.update(
                            status=f"Waiting for jobs to finish... Status: "
                            f"{last_status}. "
                            f"Progress: {progress}%")
                else:
                    status.update(
                            status=f"Waiting for jobs to finish... Status: "
                                   f"{last_status}.")

                last_status = self.check_status()
            status.update(status="Jobs finished")

        logger.info(f"Jobs finished with status {self.check_status()}")

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
            events = [event for event in JobEventLog(log_file).events(
                stop_after=0)]
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
            elif last_event.type == JobEventType.JOB_RELEASED or \
                    last_event.type == JobEventType.IMAGE_SIZE:
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
        # Locking in case other processes want to check the status at
        # the same time
        info['status'] = global_status

        lock = FileLock(
                os.path.join(self.run.storage_path, 'info.yaml.lock'))
        lock.acquire()
        try:
            self.update_yaml_file(info)
        finally:
            lock.release()

        return global_status

    def cancel_experiment(self):
        """Cancel a run of the experiment."""

        info = self.parse_yaml_file()
        if info is None:
            logger.warning(f"Run {self.run_id} doesn't have a info.yaml file")
            logger.warning(
                    "Probably due to it being not started or some error")
            logger.info(
                    "Try waiting for it to launch or delete"
                    " the run altogether")
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
        info["finish_time"] = datetime.now()
        self.update_yaml_file(info)

        # Update database
        Session = self.session_maker()
        update_run_status(Session, self.run_id,
                          'cancelled')
        update_run_finish_time(Session, self.run_id,
                               datetime.now())
        Session.close()


class SlurmExecutionHandler(RunExecutionHandler):
    """Execution handler for Slurm."""

    def __init__(self, database_sessionmaker, run_id: int,
                 slurm_options: dict = None,
                 container_path: str = None,
                 commit_sha: str = None,
                 wait: bool = False):
        super().__init__(database_sessionmaker, run_id, container_path,
                         commit_sha)

        # Check that slurm is available
        if not shutil.which('sbatch'):
            logger.warning("Slurm is not available on this machine")
            self.slurm_available = False
        else:
            self.slurm_available = True

        self.slurm_options = slurm_options
        self.wait = wait

    def run_experiment(self):

        if not self.slurm_available:
            logger.error("Slurm is not available on this machine")
            sys.exit(-1)

        # Creating the executed script in run storage_path
        script_path = os.path.join(self.run.storage_path,
                                   'slurm_script.sh')
        with open(script_path, 'w') as f:
            f.write('#!/bin/bash\n')
            f.write("# Slurm execution script for Qanat run"
                    f" {self.run_id}\n\n")

            # Slurm options
            if self.slurm_options is not None:
                for option, value in self.slurm_options.items():
                    # If -- or -
                    if option.startswith('-') and not option.startswith('--'):
                        f.write(f"#SBATCH {option} {value}\n")
                    else:
                        f.write(f"#SBATCH {option}={value}\n")

            # Add job name
            f.write(f"#SBATCH --job-name=qanat_{self.run_id}\n")

            # Add output and error files
            f.write(
                f"#SBATCH --output={os.path.join(self.run.storage_path, '%x.%j.stdout.txt')}\n")
            f.write(
                f"#SBATCH --error={os.path.join(self.run.storage_path, '%x.%j.stderr.txt')}\n\n")

        # Separating a regular job from an array job
        if len(self.commands) > 1:

            logger.info(f"Submitting an array job with {len(self.commands)} "
                        f"commands")

            # Creating a commands config file to parse thanks to
            # SLURM_ARRAY_TASK_ID
            commands_config_path = os.path.join(
                    self.run.storage_path, 'slurm_commands_config.txt')
            with open(commands_config_path, 'w') as f:
                f.write(f"Commands file for run {self.run_id}\n")
                f.write(f"Number of commands: {len(self.commands)}\n\n")
                f.write("-" * 80 + "\n")
                f.write("ArrayTaskId\tCommand\n")
                for i, command in enumerate(self.commands):
                    str_command = " ".join([str(x) for x in command])
                    f.write(f"{i+1}\t{str_command}\n")
                f.write("-" * 80)

            with open(script_path, 'a') as f:
                # Adding the array option to slurm script
                f.write(f"#SBATCH --array=1-{len(self.commands)}\n\n")

                # Parsing the commands file for the right command
                # to execute from the SLURM_ARRAY_TASK_ID
                f.write(
                    f'COMMAND=$(awk -v ARRAY_TASK_ID=$SLURM_ARRAY_TASK_ID '
                    f'\'$1==ARRAY_TASK_ID {{print substr($0,index($0,$2))}}\' '
                    f'{commands_config_path})\n')

        # Case: only one command
        else:

            logger.info(f"Submitting a single job with command "
                        f"{self.commands[0]}")
            with open(script_path, 'a') as f:
                str_command = " ".join([str(x) for x in self.commands[0]])
                f.write(f'COMMAND="{str_command}"\n')

        # Finishing the slurm script
        with open(script_path, 'a') as f:

            # Some info and moving to the working directory
            f.write('echo "Running on host: $HOSTNAME"\n')
            f.write('echo "Starting at: $(date)"\n\n')

            f.write(f'echo "Moving to repertory {self.working_dir}"\n')
            f.write(f'cd {self.working_dir}\n\n')
            f.write('pwd\n')

            # Executing the command
            f.write('echo "Executing command: $COMMAND"\n')
            f.write('eval "$COMMAND"\n\n')
            f.write('echo "Finished at: $(date)"\n')

        # Submitting the job
        logger.info(f"Submitting job for run {self.run_id}")
        logger.info(f"Working directory: {self.working_dir}")
        logger.info(f"Script path: {script_path}")
        logger.info(f"Slurm options: {self.slurm_options}")
        logger.info(f"Commands: {self.commands}")

        # Submitting the job
        submit = ['sbatch', script_path]
        if self.wait:
            submit.append('--wait')
        try:
            output = subprocess.check_output(submit)
        except subprocess.CalledProcessError as e:
            logger.error("Error while submitting the job")
            logger.error(e)
            info = self.parse_yaml_file()
            info['status'] = 'cancelled'
            self.update_yaml_file(info)
            sys.exit(-1)

        # Getting the job id
        job_id = output.decode('utf-8').split()[-1]
        logger.info(f"Job submitted with id {job_id}")

        # Updating the YAML file
        info = self.parse_yaml_file()
        info['status'] = 'running'
        info['job_id'] = job_id
        info['start_time'] = datetime.now()
        self.update_yaml_file(info)

    def check_status(self):

        # Read info from YAML file
        info = self.parse_yaml_file()
        if info is None:
            return "unknown"
        elif info['status'] == 'finished':
            return "finished"
        elif info['status'] == 'cancelled':
            return "cancelled"

        if not self.slurm_available:
            return "unknown"

        # Getting the job id
        job_id = info['job_id']

        # Checking the job status with sacct -j <job_id>
        try:
            output = subprocess.check_output(['sacct', '-j', job_id,
                                              '--format=JobIDRaw,Start,State,Elapsed'])
            output = output.decode('utf-8')


            # Getting the status by parsing the output lines
            status = []
            start_times = []
            elapsed_times = []
            for line in output.split('\n')[2:]:
                if line.startswith(job_id) and not line.startswith(f'{job_id}.'):
                    status.append(line.split()[2])
                    start_times.append(line.split()[1])
                    elapsed_times.append(line.split()[3])

            # Getting the global status
            if len(status) == 0:
                global_status = 'unknown'
            elif any(['CANCELLED' in x for x in status]):
                global_status = 'cancelled'
            elif any(['FAILED' in x for x in status]):
                global_status = 'cancelled'
            elif any(['TIMEOUT' in x for x in status]):
                global_status = 'cancelled'
            elif all(['COMPLETED' in x for x in status]):
                global_status = 'finished'
            elif any(['RUNNING' in x for x in status]):
                global_status = 'running'
            else:
                global_status = 'unknown'

            # Update the database
            Session = self.session_maker()
            update_run_status(Session, self.run_id,
                            global_status)
            Session.commit()
            Session.close()

            # Getting the start time if not set
            if self.run.launched is None:
                start_time = min([datetime.strptime(x, '%Y-%m-%dT%H:%M:%S')
                                  for x in start_times])

                info['start_time'] = start_time

                # Update database if the start time isn't already set
                Session = self.session_maker()

                # Getting the start time from the database
                run = Session.query(RunOfAnExperiment).filter(
                    RunOfAnExperiment.id == self.run_id).first()

                update_run_start_time(Session, self.run_id,
                                        start_time)
                Session.close()

            # Getting the elapsed time if the job is finished or cancelled
            if self.run.finished is None and \
                global_status == 'finished' or global_status == 'cancelled':
                elapsed_time = max([datetime.strptime(x, '%H:%M:%S')
                                    for x in elapsed_times])
                time_delta = timedelta(hours=elapsed_time.hour,
                                    minutes=elapsed_time.minute,
                                    seconds=elapsed_time.second)

                info['finish_time'] = info['start_time'] + time_delta
                Session = self.session_maker()
                update_run_finish_time(Session, self.run_id,
                                    info['start_time'] + time_delta)
                Session.close()

        except subprocess.CalledProcessError as e:
            logger.error("Error while checking the job status"
                         f" for run {self.run_id}")
            logger.error(e)
            global_status = 'unknown'

        # Updating the YAML file
        info['status'] = global_status
        self.update_yaml_file(info)

        return global_status

    def cancel_experiment(self):

        # Read info from YAML file
        info = self.parse_yaml_file()
        if info is None:
            return

        # Getting the job id
        job_id = info['job_id']

        # Cancelling the job with scancel
        try:
            subprocess.run(['scancel', job_id])
        except subprocess.CalledProcessError as e:
            logger.error("Error while cancelling the job")
            logger.error(e)

        # Updating the YAML file
        info['status'] = 'cancelled'
        self.update_yaml_file(info)
