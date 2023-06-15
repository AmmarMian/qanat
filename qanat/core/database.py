# ========================================
# FileName: database.py
# Date: 20 avril 2023 - 16:15
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Internal database manegement
# for Qanat.
# =========================================

import os
import shutil
from datetime import datetime
from dataclasses import dataclass
from sqlalchemy import (
        Column, Integer, String, ForeignKey, DateTime,
        create_engine
)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.sql import func

from sqlalchemy.types import TypeDecorator
import json
from rich.console import Console

from typing import Tuple, List

from ..utils.logging import setup_logger
logger = setup_logger()


# ------------------------------------------------------------
# Serialisation type for dicts
# ------------------------------------------------------------
class JSONEncodedDict(TypeDecorator):
    """Represents an mutable structure as a json-encoded string."""

    impl = String

    def process_bind_param(self, value, dialect):
        """Serialise the value to a JSON-encoded string.
        """
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        """Deserialise the value from a JSON-encoded string."""
        if value is not None:
            value = json.loads(value)
        return value


# ------------------------------------------------------------
# Dataclasses for Qanat
# ------------------------------------------------------------
Base = declarative_base()


@dataclass
class Experiment(Base):
    """Dataclass for type of experiments."""

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True)
    path = Column(String)
    name = Column(String)
    description = Column(String)
    created = Column(DateTime, server_default=func.now())
    updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    executable = Column(String)
    executable_command = Column(String)


@dataclass
class Dataset(Base):
    """Dataclass for eventual datasets used in the project."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    path = Column(String)
    name = Column(String)
    description = Column(String)
    created = Column(DateTime, server_default=func.now())
    updated = Column(DateTime, server_default=func.now(), onupdate=func.now())


@dataclass
class Document(Base):
    """Dataclass for the documents of the project."""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    path = Column(String)
    name = Column(String)
    description = Column(String)
    created = Column(DateTime, server_default=func.now())
    updated = Column(DateTime, server_default=func.now(), onupdate=func.now())
    compile_script = Column(String)
    compile_script_command = Column(String)
    view_script = Column(String)
    view_script_command = Column(String)
    status = Column(String, server_default="Not compiled")
    compiled = Column(DateTime)


@dataclass
class ExperimentResultFiles(Base):
    """Dataclass to track Files that are results of experiments."""

    __tablename__ = "experiment_result_files"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    path = Column(String, nullable=False)


@dataclass
class Tags(Base):
    """Dataclass for tags for both experiments, runs and datasets."""

    __tablename__ = "tags"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)


@dataclass
class Action(Base):
    """Dataclass for actions performed on experiments."""

    __tablename__ = "actions"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    name = Column(String)
    executable = Column(String)
    executable_command = Column(String)
    description = Column(String)
    created = Column(DateTime, server_default=func.now())
    updated = Column(DateTime, server_default=func.now(), onupdate=func.now())


@dataclass
class RunOfAnExperiment(Base):
    """Dataclass for runs of experiments."""

    __tablename__ = "runs_of_experiments"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    launched = Column(DateTime)
    finished = Column(DateTime)
    status = Column(String, server_default="Not started")
    storage_path = Column(String)
    description = Column(String)
    metric = Column(String)
    commit_sha = Column(String)
    runner = Column(String)
    container_path = Column(String)
    runner_params = Column(JSONEncodedDict)
    progress = Column(String, server_default="")
    comment_file = Column(String)
    param_file = Column(String)


@dataclass
class RunsTags(Base):
    """Dataclass for the link between runs and tags."""

    __tablename__ = "runs_tags"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs_of_experiments.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))


@dataclass
class GroupOfParametersOfARun(Base):
    """Dataclass for groups of parameters used in the run of an
    experiment."""

    __tablename__ = "groups_of_parameters"

    id = Column(Integer, primary_key=True)
    run_id = Column(Integer, ForeignKey("runs_of_experiments.id"))
    values = Column(JSONEncodedDict)


@dataclass
class DocumentExperimentDependencies(Base):

    __tablename__ = "documents_experiments_dependencies"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    run_args_file = Column(String)
    runner = Column(String)
    runner_params = Column(JSONEncodedDict)
    container = Column(String)
    commit_sha = Column(String)
    action_name = Column(String)
    action_args = Column(String)


@dataclass
class DocumentExperimentFilesDependencies(Base):

    __tablename__ = "documents_experiments_files_dependencies"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    file_id = Column(Integer, ForeignKey("experiment_result_files.id"))


@dataclass
class DatasetExperiment(Base):
    """Dataclass for the link between experiments and datasets."""

    __tablename__ = "datasets_experiments"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    dataset_id = Column(Integer, ForeignKey("datasets.id"))


@dataclass
class ExperimentsTags(Base):
    """Dataclass for the link between experiments and tags."""

    __tablename__ = "experiments_tags"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))


@dataclass
class DatasetsTags(Base):
    """Dataclass for the link between datasets and tags."""

    __tablename__ = "datasets_tags"

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))


@dataclass
class DocumentsTags(Base):
    """Dataclass for the link between documents and tags."""

    __tablename__ = "documents_tags"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    tag_id = Column(Integer, ForeignKey("tags.id"))


# ------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------
def init_database(path: str):
    """Initialize a new database for qanat.

    :param path: The path to the database.
    :type path: str

    :return: The engine of the database.
    :rtype: sqlalchemy.engine.base.Engine

    :return: The base of the database.
    :rtype: sqlalchemy.ext.declarative.api.DeclarativeMeta
    """

    # Create the database
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)

    return engine, Base


def open_database(path: str):
    """Open an existing database for qanat.

    :param path: The path to the database.
    :type path: str

    :return: The engine of the database.
    :rtype: sqlalchemy.engine.base.Engine

    :return: The base of the database.
    :rtype: sqlalchemy.ext.declarative.api.DeclarativeMeta

    :return: The session maker of the database.
    :rtype: sqlalchemy.orm.session.sessionmaker
    """

    # Open the database with an engine
    engine = create_engine(f"sqlite:///{path}")
    Base = automap_base()
    Base.prepare(engine, reflect=True)

    # Create a session maker for use
    Session = sessionmaker(bind=engine)

    return engine, Base, Session


# ------------------------------------------------------------
# Database filling and updating functions
# ------------------------------------------------------------
def add_experiment(session: Session,
                   path: str, name: str, description: str, executable: str,
                   executable_command: str = "/usr/bin/bash",
                   tags: list = [], datasets: list = []) -> Experiment:
    """Add an experiment to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param path: The path to the experiment.
    :type path: str

    :param name: The name of the experiment.
    :type name: str

    :param description: The description of the experiment.
    :type description: str

    :param executable: The path to the executable of the experiment.
    :type executable: str

    :param executable_command: The progrma to use to execute executable.
                               Default is "/usr/bin/bash".
    :type executable_command: str.

    :param tags: The tags (names) of the experiment. Default is [].
    :type tags: list

    :param datasets: The datasets (paths) of the experiment. Default is [].
    :type datasets: list

    :return: The experiment object.
    :rtype: qanat.core.dataset.Experiment
    """

    # Check if the experiment already exists
    experiment_id = find_experiment_id(session, name)
    if experiment_id != -1:
        logger.warning(f"Experiment {name} already exists in the database.")
        return

    # Create the experiment
    experiment = Experiment(path=path, name=name, description=description,
                            executable=executable,
                            executable_command=executable_command)

    # Add the experiment to the database
    session.add(experiment)

    # Add the tags to the experiment
    for tag in tags:
        tag_id = find_tag_id(session, tag)
        if tag_id == -1:
            logger.warning(f"Tag {tag} does not exist in the database."
                           " Adding it with no description.")
            tag = Tags(name=tag)
            session.add(tag)
            session.commit()
            tag_id = tag.id
        experiment_tag = ExperimentsTags(experiment_id=experiment.id,
                                         tag_id=tag_id)
        session.add(experiment_tag)

    # Add the datasets to the experiment
    for dataset in datasets:
        dataset_id = find_dataset_id(session, dataset)
        if dataset_id == -1:
            logger.warning(f"Dataset {dataset} does not exist in the database."
                           " Please add it to the database before adding it to"
                           " the experiment.")
        else:
            experiment_dataset = DatasetExperiment(experiment_id=experiment.id,
                                                   dataset_id=dataset_id)
            session.add(experiment_dataset)

    session.commit()
    return experiment


def add_dataset(session: Session,
                path: str, name: str, description: str,
                tags: list = []) -> Dataset:
    """Add a dataset to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param path: The path to the dataset.
    :type path: str

    :param name: The name of the dataset.
    :type name: str

    :param description: The description of the dataset.
    :type description: str

    :param tags: The tags (names) of the dataset. Default is [].
    :type tags: list

    :return: The dataset object.
    :rtype: qanat.core.dataset.Dataset
    """

    # Check if the dataset already exists in the database
    dataset_id = find_dataset_id(session, name)

    # If the dataset does not exist, add it to the database
    if dataset_id != -1:
        logger.warning(f"Dataset {name} already exists in the database.")
        return

    # Create the dataset
    dataset = Dataset(path=path, name=name, description=description)

    # Add the dataset to the database
    session.add(dataset)

    # Add the tags to the dataset
    for tag in tags:
        tag_id = find_tag_id(session, tag)
        if tag_id == -1:
            tag = Tags(name=tag)
            session.add(tag)
            session.commit()
            tag_id = tag.id
        dataset_tag = DatasetsTags(dataset_id=dataset.id, tag_id=tag_id)
        session.add(dataset_tag)
    session.commit()

    return Dataset


def add_tag(session: Session, name: str, description: str) -> Tags:
    """Add a tag to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param name: The name of the tag.
    :type name: str

    :param description: The description of the tag.
    :type description: str

    :return: The tag object.
    :rtype: qanat.core.dataset.Tags
    """

    # Check if the tag already exists in the database
    tag_id = find_tag_id(session, name)

    # If the tag does not exist, add it to the database
    if tag_id != -1:
        logger.warning(f"Tag {name} already exists in the database.")
        return

    # Create the tag
    tag = Tags(name=name, description=description)

    # Add the tag to the database
    session.add(tag)
    session.commit()

    return tag


def add_action(session: Session, name: str, description: str,
               executable: str, executable_command: str,
               experiment_name: str) -> Action:
    """Add an action to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param name: The name of the action.
    :type name: str

    :param description: The description of the action.
    :type description: str

    :param executable: The path to the executable of the action.
    :type executable: str

    :param executable_command: The command to run the executable.
    :type executable_command: str

    :param experiment_name: The name of the experiment of the action.
    :type experiment_path: str

    :return: The action object.
    :rtype: qanat.core.dataset.Action
    """

    # Check if the action already exists in the database
    action_id = find_action_id(session, name, experiment_name)

    # If the action does not exist, add it to the database
    if action_id != -1:
        logger.warning(f"Action {name} already exists in the database.")
        return

    # Find experiment_id through name
    experiment_id = find_experiment_id(session, experiment_name)

    # Create the action
    action = Action(name=name, description=description, executable=executable,
                    executable_command=executable_command,
                    experiment_id=experiment_id)

    # Add the action to the database
    session.add(action)
    session.commit()

    return action


def add_run(session: Session,
            experiment_name: str, storage_path: str,
            commit_sha: str,
            parameters_groups: list = [],
            description: str = "",
            tags: list = [],
            runner: str = 'local',
            container_path: str = None,
            runner_params: dict = {},
            param_file: str = None) -> RunOfAnExperiment:
    """Add a run to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The naf of the experiment.
    :type experiment_path: str

    :param storage_path: The path to the storage of the run.
    :type storage_path: str

    :param commit_sha: The commit sha of the repo when running.
    :type commit_sha: str

    :param parameters_groups: The parameters groups (as dict) of the run.
                              Default is [].
    :type parameters_groups: list

    :param description: The description of the run. Default is "".
    :type description: str

    :param tags: The tags (names) of the run. Default is [].
    :type tags: list

    :param runner: The name of the runner. Default is 'local'.
    :type runner: str

    :param container_path: The path to the container of the runner.
    :type container_path: str

    :param runner_params: The parameters of the runner. Default is {}.
    :type runner_params: dict

    :param param_file: The path to the parameter file. Default is None.
    :type param_file: str

    :return: The run object.
    :rtype: qanat.core.dataset.RunOfAnExperiment
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(session, experiment_name)

    # Create the run
    run = RunOfAnExperiment(experiment_id=experiment_id,
                            description=description, commit_sha=commit_sha,
                            storage_path=storage_path,
                            runner=runner, runner_params=runner_params,
                            container_path=container_path,
                            param_file=param_file)
    session.add(run)
    session.commit()

    # Create Group of parameters for the run
    for parameters in parameters_groups:
        group_parameters = GroupOfParametersOfARun(values=parameters,
                                                   run_id=run.id)
        session.add(group_parameters)

    # Add the tags to the run
    for tag in tags:
        tag_id = find_tag_id(session, tag)
        if tag_id == -1:
            tag = Tags(name=tag)
            session.add(tag)
            session.commit()
            tag_id = tag.id
        run_tag = RunsTags(run_id=run.id, tag_id=tag_id)
        session.add(run_tag)
    session.commit()

    return run


def delete_experiment(session: Session, experiment_name: str):
    """Remove an experiment from the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str
    """

    # Find the experiment
    experiment_id = find_experiment_id(session, experiment_name)

    # If the experiment does not exist, return
    if experiment_id == -1:
        logger.warning(f"Experiment {experiment_name} does not exist in the "
                       f"database.")
        return

    # Rich console with status
    logger.info(f"Removing experiment {experiment_name} from the database.")
    console = Console()
    with console.status("[bold green]Removing experiment...") as status:

        # Find runs corresponding to the experiment
        runs = session.query(RunOfAnExperiment).filter(
            RunOfAnExperiment.experiment_id == experiment_id).all()

        console.print(
                f"Removing {len(runs)} runs of the "
                f"experiment {experiment_name}.")

        # Remove the groups_of_parameters of runs corresponding to the
        # experiment
        console.print("Removing the groups of parameters of the runs.")
        for run in runs:
            session.query(GroupOfParametersOfARun).filter(
                GroupOfParametersOfARun.run_id == run.id).delete()

        # Remove the tags of runs in the experiment
        console.print("Removing the tags of the runs.")
        for run in runs:
            session.query(RunsTags).filter(RunsTags.run_id == run.id).delete()

        # Removing the directories of runs
        console.print("Removing the directories of the runs.")
        for run in runs:
            shutil.rmtree(run.storage_path)

        # Remove the runs of the experiment
        console.print("Removing the runs of the experiment.")
        session.query(RunOfAnExperiment).filter(
            RunOfAnExperiment.experiment_id == experiment_id).delete()

        # Remove the actions of the experiment
        console.print("Removing the actions of the experiment.")
        session.query(Action).filter(
                Action.experiment_id == experiment_id).delete()

        # Remove the tags of the experiment
        console.print("Removing the tags of the experiment.")
        session.query(ExperimentsTags).filter(
            ExperimentsTags.experiment_id == experiment_id).delete()

        # Remove the datasets link of the experiment
        console.print("Removing the datasets link of the experiment.")
        session.query(DatasetExperiment).filter(
            DatasetExperiment.experiment_id == experiment_id).delete()

        # Remove the experiment
        console.print("Removing the experiment.")
        session.query(Experiment).filter(
                Experiment.id == experiment_id).delete()
        session.commit()

    status.update(f"[bold green]Experiment {experiment_name} removed.")


def delete_dataset(session: Session, dataset_name: str):
    """Remove a dataset from the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param dataset_name: The name of the dataset.
    :type dataset_name: str
    """

    dataset_id = find_dataset_id(session, dataset_name)

    # If the dataset does not exist, return
    if dataset_id == -1:
        logger.warning(f"Dataset {dataset_name} does not exist in the "
                       f"database.")
        return

    # Rich console with status
    logger.info(f"Removing dataset {dataset_name} from the database.")
    console = Console()
    with console.status("[bold green]Removing dataset...") as status:

        # Remove the link between datasets and experiments
        console.print("Removing the link between datasets and experiments.")
        session.query(DatasetExperiment).filter(
            DatasetExperiment.dataset_id == dataset_id).delete()

        # Remove the tags of the dataset
        console.print("Removing the tags of the dataset.")
        session.query(DatasetsTags).filter(
            DatasetsTags.dataset_id == dataset_id).delete()

        # Remove the dataset
        console.print("Removing the dataset.")
        session.query(Dataset).filter(
            Dataset.id == dataset_id).delete()
        session.commit()

    status.update(f"[bold green]Dataset {dataset_name} removed.")


def delete_action(session: Session, action_name: str,
                  experiment_name) -> bool:
    """Delete an action from the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param action_name: The name of the action.
    :type action_name: str

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :return: True if the action has been deleted, False otherwise.
    :rtype: bool
    """

    # Find the experiment_id
    experiment_id = find_experiment_id(session, experiment_name)

    # If the experiment does not exist, return
    if experiment_id == -1:
        logger.warning(f"Experiment {experiment_name} does not exist in the "
                       f"database.")
        return

    # Find the action_id
    action_id = find_action_id(session, action_name, experiment_name)

    # If the action does not exist, return
    if action_id == -1:
        logger.warning(f"Action {action_name} does not exist in the "
                       f"database.")
        return False

    # Deleting the action
    session.query(Action).filter(Action.id == action_id).delete()
    session.commit()
    return True


def delete_run_from_id(session: Session, run_id: int):
    """Delete a run from the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int
    """

    # Get run from id
    run = session.query(RunOfAnExperiment).filter(
            RunOfAnExperiment.id == run_id).first()

    if run is None:
        logger.warning(f"Run {run_id} does not exist in the database.")
        return

    # Remove the groups_of_parameters of run corresponding to the
    # run_id
    session.query(GroupOfParametersOfARun).filter(
            GroupOfParametersOfARun.run_id == run_id).delete()

    # Remove the tags of run in the experiment
    session.query(RunsTags).filter(RunsTags.run_id == run_id).delete()

    # Removing the directories of runs
    if os.path.exists(run.storage_path):
        shutil.rmtree(run.storage_path)

    # Remove the run
    session.query(RunOfAnExperiment).filter(
            RunOfAnExperiment.id == run_id).delete()
    session.commit()


def update_experiment(session: Session, experiment_name: str,
                      new_experiment_name: str = None,
                      new_experiment_description: str = None,
                      new_experiment_path: str = None,
                      new_experiment_executable: str = None,
                      new_experiment_executable_command: str = None,
                      new_experiment_tags: list = None,
                      new_experiment_datasets: list = None,
                      new_experiment_actions: list = None):
    """Update an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param new_experiment_name: The new name of the experiment.
    :type new_experiment_name: str

    :param new_experiment_description: The new description of the experiment.
    :type new_experiment_description: str

    :param new_experiment_path: The new path of the experiment.
    :type new_experiment_path: str

    :param new_experiment_executable: The new executable of the experiment.
    :type new_experiment_executable: str

    :param new_experiment_executable_command: The new executable command of the
        experiment.
    :type new_experiment_executable_command: str

    :param new_experiment_tags: The new tags of the experiment.
    :type new_experiment_tags: list

    :param new_experiment_datasets: The new datasets of the experiment.
    :type new_experiment_datasets: list

    :param new_experiment_actions: The new actions of the experiment.
    :type new_experiment_actions: list
    """

    # Find the id of the experiment
    experiment_id = find_experiment_id(session, experiment_name)

    # If the experiment does not exist, return
    if experiment_id == -1:
        logger.warning(f"Experiment {experiment_name} does not exist in the "
                       "database.")
        return

    # Update elements only if needed
    # ------------------------------
    for element in zip(
            ["name", "description", "path", "executable",
             "executable_command"],
            [new_experiment_name, new_experiment_description,
             new_experiment_path, new_experiment_executable,
             new_experiment_executable_command]):
        if element[1] is not None:

            # Update desired properties
            session.query(Experiment).filter(
                Experiment.id == experiment_id).update(
                {element[0]: element[1]})

    # Update the tags of the experiment
    # ---------------------------------
    # Find the tags of the experiment
    experiment_tags = session.query(Tags).join(ExperimentsTags).filter(
        ExperimentsTags.experiment_id == experiment_id).all()

    if new_experiment_tags is not None:
        # Delete the link between the experiment and the tags
        # that are not in the new tags
        for tag in experiment_tags:
            if tag.name not in new_experiment_tags:
                session.query(ExperimentsTags).filter(
                    ExperimentsTags.experiment_id == experiment_id,
                    ExperimentsTags.tag_id == tag.id).delete()

        # Adding new tags to the experiment
        for tag in new_experiment_tags:
            if tag not in [x.name for x in experiment_tags]:
                tag_id = find_tag_id(session, tag)
                if tag_id == -1:
                    logger.warning(f"Tag {tag} does not exist in the "
                                   "database.")
                    logger.info(f"Creating tag {tag} in the database.")
                    tag = add_tag(session, tag)
                    tag_id = tag.id
                session.add(ExperimentsTags(
                    experiment_id=experiment_id, tag_id=tag_id))

    # Update the datasets of the experiment
    # -------------------------------------
    # Find the datasets of the experiment
    experiment_datasets = session.query(Dataset).join(
            DatasetExperiment).filter(
        DatasetExperiment.experiment_id == experiment_id).all()

    if new_experiment_datasets is not None:
        # Delete the link between the experiment and the datasets
        # that are not in the new datasets
        for dataset in experiment_datasets:
            if dataset.name not in new_experiment_datasets:
                session.query(DatasetExperiment).filter(
                    DatasetExperiment.experiment_id == experiment_id,
                    DatasetExperiment.dataset_id == dataset.id).delete()

        # Adding new datasets to the experiment
        for dataset in new_experiment_datasets:
            if dataset not in [x.name for x in experiment_datasets]:
                dataset_id = find_dataset_id(session, dataset)
                if dataset_id == -1:
                    logger.warning(f"Dataset {dataset} does not exist in the "
                                   "database. Please add it first using "
                                   " 'qanat dataset new'.")
                    continue
                session.add(DatasetExperiment(
                    experiment_id=experiment_id, dataset_id=dataset_id))

    # Update the actions of the experiment
    # ------------------------------------
    # Find the actions of the experiment
    experiment_actions = session.query(Action).filter(
        Action.experiment_id == experiment_id).all()

    if new_experiment_actions is not None:
        # Delete the actions not in the new actions
        for action in experiment_actions:
            if action.id not in [x.id for x in new_experiment_actions]:
                delete_action(session, action.name, experiment_name)

        # Add the new actions
        for action in new_experiment_actions:
            if action.id not in [x.id for x in experiment_actions]:
                add_action(session, action.name, experiment_name,
                           action.description, action.command,
                           action.arguments, action.tags)

    session.commit()


def update_run_status(session: Session, run_id: int,
                      new_status: str) -> None:
    """Update the status of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :param new_status: The new status of the run.
    :type new_status: str
    """

    session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).update(
        {"status": new_status})
    session.commit()


def update_run_finish_time(session: Session, run_id: int,
                           new_finish_time: datetime = None) -> None:
    """Update the finish time of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :param new_finish_time: The new finish time of the run.
    :type new_finish_time: datetime.datetime
    """

    if new_finish_time is None:
        new_finish_time = datetime.now()

    session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).update(
        {"finished": new_finish_time})
    session.commit()


def update_run_start_time(session: Session, run_id: int,
                          new_start_time: datetime = None) -> None:
    """Update the start time of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :param new_start_time: The new start time of the run.
    :type new_start_time: datetime.datetime
    """
    if new_start_time is None:
        return
    session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).update(
        {"launched": new_start_time})
    session.commit()


def update_run_progress(session: Session, run_id: int,
                        new_progress: float) -> None:
    """Update the progress of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :param new_progress: The new progress of the run.
    :type new_progress: float
    """
    session.query(RunOfAnExperiment).filter(
        RunOfAnExperiment.id == run_id).update(
        {"progress": f"{new_progress} %"})
    session.commit()


def add_document(session: Session, name: str, path: str,
                 compile_script: str, compile_script_command: str,
                 description: str = "",
                 view_script: str = "", view_script_command: str = "",
                 experiment_dependencies: list = None,
                 tags: list = None) -> None:

    """Add a document to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param name: The name of the document.
    :type name: str

    :param path: The path of the document.
    :type path: str

    :param compile_script: The path of the compile script.
    :type compile_script: str

    :param compile_script_command: The command of the compile script.
    :type compile_script_command: str

    :param description: The description of the document.
    :type description: str

    :param view_script: The path of the view script.
    :type view_script: str

    :param view_script_command: The command of the view script.
    :type view_script_command: str

    :param experiment_dependencies: The dependencies of the document.
                                    list of dict with keys 'exepriment_name',
                                    'run_args_file', 'files'
    :type experiment_dependencies: list

    :param tags: The tags of the document.
    :type tags: list
    """

    # Create the document
    document = Document(name=name, path=path,
                        description=description,
                        compile_script=compile_script,
                        compile_script_command=compile_script_command,
                        view_script=view_script,
                        view_script_command=view_script_command)
    session.add(document)
    session.commit()

    # Add the tags
    if tags is not None:
        for tag in tags:
            add_tag(session, tag, "")
            tag_id = find_tag_id(session, tag)

            # Add the tag to the document
            doctag = DocumentsTags(document_id=document.id, tag_id=tag_id)
            session.add(doctag)
        session.commit()

    # Add the dependencies
    if experiment_dependencies is not None:
        for dependency in experiment_dependencies:
            add_dependency_to_document(session, document.id,
                                       dependency)


def add_dependency_to_document(session: Session, document_name: str,
                               dependency: dict) -> None:
    """Add a dependency to a document in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :param dependency: The dependency to add. dict with keys 'exepriment_name',
                        'run_args_file', 'files', "runner", "runner_params",
                        "container", "commit_sha", "action_name", 'action_args'
    :type dependency: dict
    """

    # Find the document id
    document_id = find_document_id(session, document_name)

    # Find the experiment id
    experiment_id = find_experiment_id(session,
                                       dependency["experiment_name"])

    # Default values for the runner and container
    if "runner" not in dependency:
        dependency["runner"] = "local"
    if "runner_params" not in dependency:
        dependency["runner_params"] = {}
    if "container" not in dependency:
        dependency["container"] = None
    if "commit_sha" not in dependency:
        dependency["commit_sha"] = None
    if "action_name" not in dependency:
        dependency["action_name"] = None
    if 'action_args' not in dependency:
        dependency['action_args'] = ""

    # Add the experiment dependency
    experiment_dependency = DocumentExperimentDependencies(
        document_id=document_id,
        experiment_id=experiment_id,
        run_args_file=dependency["run_args_file"],
        runner=dependency["runner"],
        runner_params=dependency["runner_params"],
        container=dependency["container"],
        commit_sha=dependency["commit_sha"],
        action_name=dependency["action_name"],
        action_args=dependency["action_args"])
    session.add(experiment_dependency)

    # Add the files
    for file_name in dependency["files"]:

        # Check if the file already exists for this experiment
        file = session.query(ExperimentResultFiles).filter(
            ExperimentResultFiles.path == file_name).filter(
            ExperimentResultFiles.experiment_id ==
            experiment_id).first()

        # If the file does not exist, add it
        if file is None:
            file = ExperimentResultFiles(
                    path=file_name,
                    experiment_id=experiment_id)
            session.add(file)
            session.commit()

            file.id = session.query(ExperimentResultFiles).filter(
                ExperimentResultFiles.path == file.path).filter(
                ExperimentResultFiles.experiment_id ==
                experiment_id).first().id

        # Add the file to the document/experiment dependency
        dep = DocumentExperimentFilesDependencies(
            document_id=document_id,
            experiment_id=experiment_id,
            file_id=file.id)
        session.add(dep)
    session.commit()


# ------------------------------------------------------------
# Useful lookup functions
# ------------------------------------------------------------
def find_tag_id(session: Session, tag_name: str) -> int:
    """Find the id of a tag in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param tag_name: The name of the tag.
    :type tag_name: str

    :return: The id of the tag.
    :rtype: int
    """

    # Query the database for the tag
    tag = session.query(Tags).filter(Tags.name == tag_name).first()

    # If the tag does not exist, return -1
    if tag is None:
        tag_id = -1
    else:
        tag_id = tag.id
    return tag_id


def find_experiment_id(session: Session, experiment_name: str) -> int:
    """Find the id of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :return: The id of the experiment.
    :rtype: int
    """

    # Query the database for the experiment
    experiment = session.query(Experiment).filter(
            Experiment.name == experiment_name).first()

    # If the experiment does not exist, return -1
    if experiment is None:
        experiment_id = -1
    else:
        experiment_id = experiment.id
    return experiment_id


def find_dataset_id(session: Session, dataset_name: str) -> int:
    """Find the id of a dataset in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param dataset_name: The name of the dataset.
    :type dataset_path: str

    :return: The id of the dataset.
    :rtype: int
    """

    # Query the database for the dataset
    dataset = session.query(Dataset).filter(
            Dataset.name == dataset_name).first()

    # If the dataset does not exist, return -1
    if dataset is None:
        dataset_id = -1
    else:
        dataset_id = dataset.id
    return dataset_id


def find_document_id(session: Session, document_name: str) -> int:
    """Find the id of a document in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :return: The id of the document.
    :rtype: int
    """

    # Query the database for the document
    document = session.query(Document).filter(
            Document.name == document_name).first()

    # If the document does not exist, return -1
    if document is None:
        document_id = -1
    else:
        document_id = document.id
    return document_id


def find_action_id(session: Session, action_name: str,
                   experiment_name: str) -> int:
    """Find the id of an action in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param action_name: The name of the action.
    :type action_name: str

    :param experiment_name: The name of the experiment.
    :type experiment_name: str
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(session, experiment_name)

    # Query the database for the action
    action = session.query(Action).filter(
            Action.name == action_name,
            Action.experiment_id == experiment_id).first()

    # If the action does not exist, return -1
    if action is None:
        action_id = -1
    else:
        action_id = action.id
    return action_id


def count_number_runs_experiment(session: Session,
                                 experiment_name: str) -> int:
    """Count the number of runs of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_path: str

    :return: The number of runs of the experiment.
    :rtype: int
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(session, experiment_name)

    # Query the database for the number of runs
    number_runs = session.query(RunOfAnExperiment).filter(
            RunOfAnExperiment.experiment_id == experiment_id).count()

    return number_runs


def fetch_tags_of_experiment(Session: Session,
                             experiment_name: str) -> list:
    """Fetch the tags of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_path: str

    :return: The tags of the experiment.
    :rtype: list
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(Session, experiment_name)

    # Query the database for the tags
    tags = [tag.name for tag in
            Session.query(Tags).join(ExperimentsTags).filter(
                ExperimentsTags.experiment_id == experiment_id).distinct()]
    return tags


def fetch_tags_of_dataset(Session: Session,
                          dataset_name: str) -> list:
    """Fetch the tags of a dataset in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param dataset_name: The name of the dataset.
    :type dataset_path: str

    :return: The tags of the dataset.
    :rtype: list
    """

    # Find dataset_id through name
    dataset_id = find_dataset_id(Session, dataset_name)

    # Query the database for the tags
    tags = [tag.name for tag in
            Session.query(Tags).join(DatasetsTags).filter(
                DatasetsTags.dataset_id == dataset_id).distinct()]
    return tags


def fetch_tags_of_document(Session: Session,
                           document_name: str) -> list:
    """Fetch the tags of a document in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :return: The tags of the document.
    :rtype: list
    """

    # Find document_id through name
    document_id = find_document_id(Session, document_name)

    # Query the database for the tags
    tags = [tag.name for tag in
            Session.query(Tags).join(DocumentsTags).filter(
                DocumentsTags.document_id == document_id).distinct()]
    return tags


def fetch_datasets_of_experiment(Session: Session,
                                 experiment_name: str) -> list:
    """Fetch the datasets of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_path: str

    :return: The datasets of the experiment.
    :rtype: list
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(Session, experiment_name)

    # Query the database for the datasets
    datasets = Session.query(Dataset).join(DatasetExperiment).filter(
            DatasetExperiment.experiment_id == experiment_id).distinct()
    return list(datasets)


def fetch_actions_of_experiment(Session: Session,
                                experiment_name: str) -> list:
    """Fetch the actions of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_path: str

    :return: The actions of the experiment.
    :rtype: list
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(Session, experiment_name)

    # Query the database for the actions
    actions = Session.query(Action).filter_by(
            experiment_id=experiment_id).distinct()
    return list(actions)


def fetch_runs_of_experiment(Session: Session,
                             experiment_name: str) -> list:
    """Fetch the runs of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_name: The name of the experiment.
    :type experiment_path: str

    :return: The runs of the experiment.
    :rtype: list
    """

    # Find experiment_id through name
    experiment_id = find_experiment_id(Session, experiment_name)

    # Query the database for the runs
    runs = Session.query(RunOfAnExperiment).filter_by(
            experiment_id=experiment_id).distinct()
    return list(runs)


def fetch_tags_of_run(Session: Session,
                      run_id: int) -> list:
    """Fetch the tags of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :return: The tags of the run.
    :rtype: list
    """

    # Query the database for the tags
    tags = [tag.name for tag in
            Session.query(Tags).join(RunsTags).filter(
                RunsTags.run_id == run_id).distinct()]
    return tags


def fetch_groupofparameters_of_run(
        Session: Session, run_id: int) -> list:
    """Fetch the group of parameters of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :return: The group of parameters of the run.
    :rtype: list
    """

    # Query the database for the group of parameters
    groups_of_parameters = Session.query(GroupOfParametersOfARun).filter_by(
            run_id=run_id).distinct()
    return list(groups_of_parameters)


def get_experiment_of_run(Session: Session,
                          run_id: int) -> Experiment:
    """Get the experiment of a run in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param run_id: The id of the run.
    :type run_id: int

    :return: The experiment of the run.
    :rtype: Experiment
    """

    # Query the database for the experiment
    experiment = Session.query(Experiment).join(RunOfAnExperiment).filter(
            RunOfAnExperiment.id == run_id).first()
    return experiment


def get_dependencies_info_of_document(
        Session: Session, document_id: int) -> tuple:
    """Get the infos on the dependencies to a document in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_id: The id of the document.
    :type document_id: int

    :return: The info on the dependencies as lists.
    :rtype: tuple
    """

    # Query the database for the dependecies
    dependencies_info = Session.query(
        DocumentExperimentDependencies).filter(
            DocumentExperimentDependencies.document_id ==
            document_id).distinct()
    runner = [dependency.runner for dependency in dependencies_info]
    runner_params = [
            dependency.runner_params for dependency in dependencies_info]
    run_args_file = [
            dependency.run_args_file for dependency in dependencies_info]
    commit_sha = [dependency.commit_sha for dependency in dependencies_info]
    action_name = [dependency.action_name for dependency in dependencies_info]
    action_args = [
            dependency.action_args for dependency in dependencies_info]

    ids = [dependency.experiment_id for dependency in dependencies_info]
    experiments = [Session.query(Experiment).filter(
        Experiment.id == id).first() for id in ids]
    return runner, runner_params, run_args_file, commit_sha, action_name, \
        action_args, experiments


def get_files_document_experiment(
        Session: Session, document_id: int, experiment_id: int) -> list:
    """Get the files relative to a document and an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_id: The id of the document.
    :type document_id: int

    :param experiment_id: The id of the experiment.
    :type experiment_id: int

    :return: The files of the document and the experiment.
    :rtype: list
    """

    # Check whether experiment_id is associated to document_id
    experiments = get_dependencies_info_of_document(Session, document_id)[-1]
    if experiment_id not in [experiment.id for experiment in experiments]:
        logger.error(
            "Experiment {} is not associated to document {}".format(
                experiment_id, document_id))
        return []

    # Query the database for the files
    files_ids = [
            dependency.file_id for dependency in Session.query(
                DocumentExperimentFilesDependencies).filter(
                    DocumentExperimentFilesDependencies.document_id ==
                    document_id).filter(
                        DocumentExperimentFilesDependencies.experiment_id ==
                        experiment_id).distinct()]

    files = [Session.query(ExperimentResultFiles).filter(
                ExperimentResultFiles.id == file_id).first().path
             for file_id in files_ids]

    return files


def check_document_exists(
        Session: Session, document_name: str) -> bool:
    """Check whether a document exists in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :return: Whether the document exists or not.
    :rtype: bool
    """

    # Query the database for the document
    document = Session.query(Document).filter_by(name=document_name).first()
    return document is not None


def check_document_dependency_exists(
        Session: Session, document_name: int, experiment_name: int,
        run_args_file: str) -> bool:
    """Check whether a document dependency exists in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :param experiment_name: The name of the experiment.
    :type experiment_name: str

    :param run_args_file: The run args file.
    :type run_args_file: str

    :return: Whether the dependency exists or not.
    :rtype: bool
    """

    # Query the database for the document, experiment
    document = Session.query(Document).filter_by(name=document_name).first()
    experiment = Session.query(Experiment).filter_by(
        name=experiment_name).first()

    if document is None or experiment is None:
        logger.error(
            "Document {} or experiment {} does not exist".format(
                document_name, experiment_name))
        return False

    # Query the tables for the dependency
    dependency_doc_experiment = Session.query(
            DocumentExperimentDependencies).filter_by(
        document_id=document.id, experiment_id=experiment.id,
        run_args_file=run_args_file).first()
    return dependency_doc_experiment is not None


def get_document_info_from_name(
        Session: Session, document_name: str) -> Tuple[
                Document, List[DocumentExperimentDependencies],
                List[DocumentExperimentFilesDependencies]]:
    """Get the info of a document from its name.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param document_name: The name of the document.
    :type document_name: str

    :return: The info of the document.
    :rtype: Document

    :return: The info of the document experiment dependencies.
    :rtype: list of DocumentExperimentDependencies

    :return: The info of the document experiment files dependencies.
    :rtype: list of DocumentExperimentFilesDependencies
    """

    # Get document from its name
    document = Session.query(Document).filter_by(name=document_name).first()

    # Get document experiment dependencies from document
    dependencies = [
            x for x in Session.query(DocumentExperimentDependencies).filter_by(
                document_id=document.id).all()]

    # Get document experiment files dependencies from document
    file_dependencies = [
            x for x in Session.query(
                DocumentExperimentFilesDependencies).filter_by(
                    document_id=document.id).all()]

    return document, dependencies, file_dependencies
