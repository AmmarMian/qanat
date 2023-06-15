# ========================================
# FileName: documents.py
# Date: 15 juin 2023 - 10:07
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Document compiling utilities
# =========================================

import os
import glob
import yaml
from datetime import datetime
import subprocess
import shutil
import git
from .database import (
        open_database,
        get_document_info_from_name,
        RunOfAnExperiment, Experiment, ExperimentResultFiles,
        Document
)
from ..utils.logging import setup_logger

logger = setup_logger()


def find_run_dependency(runs, file_ids, files, experiment_dependency,
                        commit_sha):
    """Find if a run corresponding to the param file at the same commit
    exists."""
    # Find if a run corresponding to the param file at the same commit
    # exists
    for run in runs:

        # Check if the run is at the same commit and has same
        # param file and is finished
        if run.commit_sha == commit_sha \
            and run.param_file == experiment_dependency.run_args_file \
                and run.status == 'finished':

            # Check if the run reuslt files contain the files
            # we need
            all_files_exist = True
            for file in files:
                if os.path.join(run.storage_path, file.path) not in \
                        glob.glob(
                            os.path.join(
                                run.storage_path, '*')):
                    all_files_exist = False
                    break

            # If all files exist, we can use this run
            if all_files_exist:
                return run

    return None


def get_info_run_dependency(Session, experiment_dependency,
                            file_dependencies):
    """Get the info of the experiment dependency."""
    experiment_id = experiment_dependency.experiment_id
    experiment = Session.query(Experiment).filter_by(
            id=experiment_id).first()

    runs = Session.query(
                RunOfAnExperiment).filter_by(
                    experiment_id=experiment_id).all()

    file_ids = [file_dependency.file_id for
                file_dependency in file_dependencies
                if file_dependency.experiment_id == experiment_id]
    files = [Session.query(ExperimentResultFiles).filter_by(
                id=file_id).first() for file_id in file_ids]

    # If the dependency has no commit sha, we need to get it
    # from the git repo
    if experiment_dependency.commit_sha is None:
        git_repo = git.Repo('.', search_parent_directories=True)
        commit_sha = \
            git_repo.head.object.hexsha
    else:
        commit_sha = experiment_dependency.commit_sha

    return experiment, runs, file_ids, files, commit_sha


class DocumentCompiler:
    """Class to handle the compilation of a document
    that depends upon experiment runs dependencies."""

    def __init__(self, document_name):

        self.document_name = document_name
        self.engine, self.Base, self.sessionmaker = open_database(
                '.qanat/database.db')
        with self.sessionmaker() as Session:
            self.document, self.experiment_dependencies, \
                self.file_dependencies = \
                get_document_info_from_name(Session, document_name)
            Session.close()

        self.pre_compile_tasks = []
        self.copy_files_tasks = []
        self.action_tasks = []

    def setUpPrecompileTasks(self):
        """Set up the tasks to be done before compiling the document."""

        Session = self.sessionmaker()

        # For each experiment dependency, we need to check if the experiment
        # has been run, and if not, run it.
        for experiment_dependency in self.experiment_dependencies:

            # Get the info of the experiment dependency
            experiment, runs, file_ids, files, commit_sha = \
                get_info_run_dependency(Session, experiment_dependency,
                                        self.file_dependencies)

            # Find if a run corresponding to the param file at the same commit
            # exists
            run = find_run_dependency(runs, file_ids, files,
                                      experiment_dependency, commit_sha)
            run_exists = run is not None

            # If the run doesn't exist, we add it to the list of tasks
            # to be done before compiling the document
            if not run_exists:
                logger.info(f'Run for experiment {experiment.name} '
                            f'with commit {commit_sha} '
                            f'and param file '
                            f'{experiment_dependency.run_args_file} '
                            f'does not exist. '
                            f'Adding to the list of tasks to be done '
                            f'before compiling the document.')
                runner = experiment_dependency.runner
                runner_params = experiment_dependency.runner_params
                container = experiment_dependency.container
                args_file = experiment_dependency.run_args_file
                task = ['qanat', 'experiment', 'run', experiment.name,
                        '--runner', runner, runner_params, '--wait', 'True']
                if experiment_dependency.commit_sha is not None:
                    task.extend(
                            ['--commit_sha',
                             experiment_dependency.commit_sha])

                if container is not None:
                    task.extend(['--container', container])

                task.extend(['--param_file', args_file])

                # Adding tag and description
                task.extend(['--tag',
                             f'{self.document_name}', '--tag', 'compile'])
                task.extend(['--description',
                             'Run for compilation of document '
                             f'{self.document_name}'])

                # Adding the task to the list of tasks to be done
                self.pre_compile_tasks.append(task)

            # Adding the action to be done after the run is done
            # if needed
            if experiment_dependency.action_name is not None:
                task = ['qanat', 'experiment', 'action', experiment.name,
                        experiment_dependency.action_name]
                if experiment_dependency.action_args is not None:
                    task.extend(experiment_dependency.action_args)
                self.action_tasks.append(task)

        Session.close()

    def setUpCopyFilesTasks(self):
        """Set up the tasks to copy files after runs of experiments"""

        Session = self.sessionmaker()
        for experiment_dependency in self.experiment_dependencies:

            # Get the info of the experiment dependency
            experiment, runs, file_ids, files, commit_sha = \
                get_info_run_dependency(Session, experiment_dependency,
                                        self.file_dependencies)

            # Find if a run corresponding to the param file at the same commit
            # exists. It should exist since we have already checked it and run
            # it if needed
            run = find_run_dependency(runs, file_ids, files,
                                      experiment_dependency, commit_sha)
            run_exists = run is not None

            if not run_exists:
                raise Exception('Run does not exist. '
                                'This should not happen.')

            for file in files:
                # Adding the files to be copied to the list of files to be
                # copied AFTER the run are done if needed
                param_file_name = os.path.splitext(os.path.basename(
                        experiment_dependency.run_args_file))[0]
                self.copy_files_tasks.append(
                    {
                        'src': os.path.join(run.storage_path, file.path),
                        'dest': os.path.join(
                            self.document.path, 'exports/'
                            f'{experiment.name}/{param_file_name}'
                            ),
                        'param_file_name': param_file_name,
                        'experiment_name': experiment.name,
                        'commit_sha': commit_sha,
                        'action_name': experiment_dependency.action_name,
                        'action_args': experiment_dependency.action_args
                    }
                )

        Session.close()

    def execute_pre_compile_tasks(self):
        """Execute the tasks to be done before compiling the document."""

        if len(self.pre_compile_tasks) > 0:
            logger.info('Executing pre-compile tasks')
            for task in self.pre_compile_tasks:
                logger.info(f'Executing task: {task}')
                process = subprocess.Popen(task)
                process.wait()

                if process.returncode != 0:
                    raise Exception(f'Error executing task {task}')

            logger.info("Done.")
        else:
            logger.info('No pre-compile tasks to execute.')

    def execute_actions_tasks(self):
        """Execute actions after the runs have been done."""

        if len(self.action_tasks) > 0:
            logger.info('Executing post-run actions tasks')
            for task in self.action_tasks:
                logger.info(f'Executing task: {task}')
                process = subprocess.run(task)
                process.wait()

                if process.returncode != 0:
                    raise Exception(f'Error executing task {task}')
            logger.info("Done.")

        else:
            logger.info('No post-run actions tasks to execute.')

    def copy_files_to_document(self):
        """Copy the files to the document."""

        logger.info('Copying files to document')
        for file in self.copy_files_tasks:
            logger.info(f'Copying {file["src"]} to {file["dest"]}')

            # Create destination directory if it doesn't exist
            if not os.path.exists(file['dest']):
                os.makedirs(file['dest'])

            # Copy the file
            shutil.copy2(file['src'], file['dest'])

            # Adding metadata to the file for trackability
            time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            metadata_text = (f'File generated by Qanat for document '
                             f'{self.document_name} by running '
                             f'{file["experiment_name"]} experiment '
                             f'with {file["param_file_name"]} param file '
                             f'at {file["commit_sha"]} commit sha. '
                             f'Action {file["action_name"]} '
                             f'with args {file["action_args"]}. '
                             f'Generated on {time_str}.')

            os.setxattr(os.path.join(file['dest'],
                        os.path.basename(file['src'])),
                        'user.qanat.metadata', metadata_text.encode('utf-8'))

            # In casemetadata is not readable we also do a file
            # with the same name but with .qanat.txt extension
            with open(os.path.join(
                file['dest'],
                os.path.splitext(os.path.basename(file['src']))[0] +
                    '.qanat.txt'), 'w') as f:
                f.write(metadata_text)

        logger.info("Done.")

    def compile_document(self, compile_args: str):
        """Compile the document."""

        self.setUpPrecompileTasks()
        self.execute_pre_compile_tasks()
        self.execute_actions_tasks()
        self.setUpCopyFilesTasks()
        self.copy_files_to_document()

        logger.info('Compiling document')
        command = [
            self.document.compile_script_command,
            self.document.compile_script,
        ]
        if compile_args is not None:
            command.extend(compile_args.split(' '))

        logger.info(f'Executing command: {command}'
                    f' in directory {self.document.path}')
        process = subprocess.Popen(command,
                                   cwd=self.document.path)
        process.wait()

        if process.returncode != 0:
            raise Exception(f'Error executing command {command}')

        # Update database with compile info
        Session = self.sessionmaker()
        document = Session.query(Document).filter_by(
            name=self.document_name).first()
        document.status = 'Compiled'
        document.compiled = datetime.now()
        Session.commit()
        Session.close()
