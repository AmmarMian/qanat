# ========================================
# FileName: database.py
# Date: 20 avril 2023 - 16:15
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Internal database manegement
# for Qanat.
# =========================================

# import os
# import git
# import shutil
# import sqlite3
from dataclasses import dataclass
from sqlalchemy import (
        Column, Integer, String, ForeignKey, DateTime,
        Text, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func

from sqlalchemy.types import TypeDecorator
import json

from ..utils.logging import setup_logger
logger = setup_logger()


# ------------------------------------------------------------
# Serialisation type for dicts
# ------------------------------------------------------------
class JSONEncodedDict(TypeDecorator):
    """Represents an mutable structure as a json-encoded string."""

    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
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
    parameters = Column(JSONEncodedDict)


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


# ------------------------------------------------------------
# Initialisation
# ------------------------------------------------------------
def init_database(path: str):
    """Initialize a new database for qanat.

    :param path: The path to the database.
    :type path: str

    :return: The engine of the database.
    :rtype: sqlalchemy.engine.base.Engine
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


def find_experiment_id(session: Session, experiment_path: str) -> int:
    """Find the id of an experiment in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_path: The path to the experiment.
    :type experiment_path: str

    :return: The id of the experiment.
    :rtype: int
    """

    # Query the database for the experiment
    experiment = session.query(Experiment).filter(
            Experiment.path == experiment_path).first()

    # If the experiment does not exist, return -1
    if experiment is None:
        experiment_id = -1
    else:
        experiment_id = experiment.id
    return experiment_id


def find_dataset_id(session: Session, dataset_path: str) -> int:
    """Find the id of a dataset in the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param dataset_path: The path to the dataset.
    :type dataset_path: str

    :return: The id of the dataset.
    :rtype: int
    """

    # Query the database for the dataset
    dataset = session.query(Dataset).filter(
            Dataset.path == dataset_path).first()

    # If the dataset does not exist, return -1
    if dataset is None:
        dataset_id = -1
    else:
        dataset_id = dataset.id
    return dataset_id


def find_action_id(session: Session, action_name: str) -> int:
    """Find the id of an action in the database."""

    # Query the database for the action
    action = session.query(Action).filter(
            Action.name == action_name).first()

    # If the action does not exist, return -1
    if action is None:
        action_id = -1
    else:
        action_id = action.id
    return action_id


def add_experiment(session: Session,
                   path: str, name: str, description: str, executable: str,
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

    :param tags: The tags (names) of the experiment. Default is [].
    :type tags: list

    :param datasets: The datasets (paths) of the experiment. Default is [].
    :type datasets: list

    :return: The experiment object.
    :rtype: qanat.core.dataset.Experiment
    """

    # Check if the experiment already exists
    experiment_id = find_experiment_id(session, path)
    if experiment_id != -1:
        logger.warning(f"Experiment {path} already exists in the database.")
        return

    # Create the experiment
    experiment = Experiment(path=path, name=name, description=description,
                            executable=executable)

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
    dataset_id = find_dataset_id(session, path)

    # If the dataset does not exist, add it to the database
    if dataset_id != -1:
        logger.warning(f"Dataset {path} already exists in the database.")
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
    impl = sqlalchemy.Text(SIZE)

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)

        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

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
               executable: str, experiment_path: str) -> Action:
    """Add an action to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param name: The name of the action.
    :type name: str

    :param description: The description of the action.
    :type description: str

    :param executable: The path to the executable of the action.
    :type executable: str

    :param experiment_path: The path to the experiment of the action.
    :type experiment_path: str

    :return: The action object.
    :rtype: qanat.core.dataset.Action
    """

    # Check if the action already exists in the database
    action_id = find_action_id(session, name)

    # If the action does not exist, add it to the database
    if action_id != -1:
        logger.warning(f"Action {name} already exists in the database.")
        return

    # Find experiment_id through path
    experiment_id = find_experiment_id(session, experiment_path)

    # Create the action
    action = Action(name=name, description=description, executable=executable,
                    experiment_id=experiment_id)

    # Add the action to the database
    session.add(action)
    session.commit()

    return action


def add_run(session: Session,
            experiment_path: str, storage_path: str,
            parameters_groups: list = [],
            description: str = "",
            tags: list = []) -> RunOfAnExperiment:
    """Add a run to the database.

    :param session: The session of the database.
    :type session: sqlalchemy.orm.session.Session

    :param experiment_path: The path to the experiment.
    :type experiment_path: str

    :param storage_path: The path to the storage of the run.
    :type storage_path: str

    :param parameters_groups: The parameters groups (as dict) of the run.
                              Default is [].
    :type parameters_groups: list

    :param description: The description of the run. Default is "".
    :type description: str

    :param tags: The tags (names) of the run. Default is [].
    :type tags: list

    :return: The run object.
    :rtype: qanat.core.dataset.RunOfAnExperiment
    """

    # Find experiment_id through path
    experiment_id = find_experiment_id(session, experiment_path)

    # Create the run
    run = RunOfAnExperiment(experiment_id=experiment_id, description=description,
                            storage_path=storage_path)
    session.add(run)

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
            tag_id = tag.id
        run_tag = RunsTags(run_id=run.id, tag_id=tag_id)
        session.add(run_tag)
    session.commit()

    return run
