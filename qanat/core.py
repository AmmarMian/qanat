# ========================================
# FileName: core.py
# Date: 20 avril 2023 - 16:15
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Core functionalities of Qanat.
# =========================================

import os
import git
import shutil
import sqlite3
from dataclasses import dataclass
from sqlalchemy import (
        Column,
        Integer,
        String,
        ForeignKey,
        create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .utils import setup_logger

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
    created = Column(String)
    executable = Column(String)


@dataclass
class Dataset(Base):
    """Dataclass for eventual datasets used in the project."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True)
    path = Column(String)
    name = Column(String)
    description = Column(String)


@dataclass
class Tags(Base):
    """Dataclass for tags for both experiments and datasets."""

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


@dataclass
class GroupOfParametersExperiment(Base):
    """Dataclass for groups of parameters for experiments."""

    __tablename__ = "groups_of_parameters"

    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id"))
    name = Column(String)
    description = Column(String)


@dataclass
class Parameter(Base):
    """Dataclass for parameters for experiments."""

    __tablename__ = "parameters"

    id = Column(Integer, primary_key=True)
    group_id = Column(Integer, ForeignKey("groups_of_parameters.id"))
    name = Column(String)
    description = Column(String)


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


def init_database(path):
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


# # TODO: Add tests for this function
# # Tests:
# # - Test that the database is created
# # - Test that the database is created in the right place
# # - Test that the database is created with the right tables
# # - Test that the database is created with the right columns
# def init_database(path):
    # """Initialize a new database for qanat.

    # :param path: The path to the database.
    # :type path: str
    # """

    # # Create the database
    # conn = sqlite3.connect(path)
    # c = conn.cursor()

    # # Create the tables
    # # ------------------------------------------------------------

    # # Experiments : Table containing info on available experiments
    # # in the project.
    # # id : Unique identifier of the experiment.
    # # path : Path to the experiment.
    # # name : Name of the experiment.
    # # description : Description of the experiment.
    # # created : Date of creation of the experiment.
    # # executable : Path to the executable of the experiment.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Experiments (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # path TEXT NOT NULL,
        # name TEXT NOT NULL,
        # description TEXT,
        # created DATETIME DEFAULT CURRENT_TIMESTAMP,
        # executable TEXT
    # );"""
    # )

    # # Actions : Table containing info on the different
    # # actions performed on the experiments beside the main execution.
    # # id : Unique identifier of the action.
    # # experiment_id : Unique identifier of the experiment.
    # # action : Name of the action.
    # # executable : Path to the executable of the action.
    # # description : Description of the action.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Actions (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # experiment_id INTEGER NOT NULL,
        # action TEXT NOT NULL,
        # executable TEXT,
        # description TEXT,
        # FOREIGN KEY (experiment_id) REFERENCES Experiments(id)
    # );"""
    # )

    # # Runs : Table containing info on the different runs of the
    # # experiments.
    # # id : Unique identifier of the run.
    # # experiment_id : Unique identifier of the experiment.
    # # run_date : Date of the run.
    # # run_duration : Duration of the run.
    # # run_status : Status of the run.
    # # run_dir : Path to the directory of the run.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Runs (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # experiment_id INTEGER NOT NULL,
        # run_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        # run_duration FLOAT,
        # run_status TEXT,
        # run_dir TEXT,
        # FOREIGN KEY (experiment_id) REFERENCES Experiments(id)
    # );"""
    # )

    # # GroupOfParameters : Table containing info on one group of parameter
    # # used in the run an experiments. (A single run can have multiple groups).
    # # id : Unique identifier of the parameters group.
    # # run_id : Unique identifier of the run.
    # # name : Name of the group of parameters.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS GroupOfParameters (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # run_id INTEGER NOT NULL,
        # name TEXT NOT NULL,
        # FOREIGN KEY (run_id) REFERENCES Runs(id)
    # );"""
    # )

    # # Parameters : Table containing info one parameter used in one
    # # group of parameters in the run of an experiment.
    # # id : Unique identifier of the parameter.
    # # group_id : Unique identifier of the group of parameters.
    # # name : Name of the parameter.
    # # value : Value of the parameter.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Parameters (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # group_id INTEGER NOT NULL,
        # name TEXT NOT NULL,
        # value TEXT NOT NULL,
        # FOREIGN KEY (group_id) REFERENCES GroupOfParameters(id)
    # );"""
    # )

    # # Datasets : Table containing info on potential datasets
    # # in the project.
    # # id : Unique identifier of the dataset.
    # # path : Path to the dataset.
    # # name : Name of the dataset.
    # # description : Description of the dataset.
    # # version : Version of the dataset.
    # # url : URL of the dataset.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Datasets (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # path TEXT NOT NULL,
        # name TEXT NOT NULL,
        # description TEXT,
        # version TEXT,
        # url TEXT
        # );"""
    # )

    # # Experiment_datasets : Table containing info on which datasets
    # # are used by which experiments.
    # # experiment_id : Unique identifie/home/ammarmian/test/.qanat/qanat.dbr of the experiment.
    # # dataset_id : Unique identifier of the dataset.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Experiment_datasets (
        # experiment_id INTEGER,
        # dataset_id INTEGER,
        # PRIMARY KEY (experiment_id, dataset_id),
        # FOREIGN KEY (experiment_id) REFERENCES Experiments(id),
        # FOREIGN KEY (dataset_id) REFERENCES Datasets(id)
    # );"""
    # )

    # # Tags : Table containing tags used for both experiments
    # # and datasets.
    # # id : Unique identifier of the tag.
    # # name : Name of the tag.
    # # description : Description of the tag.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS Tags (
        # id INTEGER PRIMARY KEY AUTOINCREMENT,
        # name TEXT NOT NULL,
        # description TEXT
    # );"""
    # )

    # # ExperimentsTags : Table containing the relation between
    # # experiments and tags.
    # # tag_id : Unique identifier of the tag.
    # # experiment_id : Unique identifier of the experiment.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS ExperimentsTags (
        # tag_id INTEGER,
        # experiment_id INTEGER,
        # PRIMARY KEY (tag_id, experiment_id),
        # FOREIGN KEY (experiment_id) REFERENCES Experiments(id),
        # FOREIGN KEY (tag_id) REFERENCES Tags(id)
    # );"""
    # )

    # # DatasetsTags : Table containing the relation between
    # # datasets and tags.
    # # tag_id : Unique identifier of the tag.
    # # dataset_id : Unique identifier of the dataset.
    # c.execute(
        # """CREATE TABLE IF NOT EXISTS DatasetsTags (
        # tag_id INTEGER,
        # dataset_id INTEGER,
        # PRIMARY KEY (tag_id, dataset_id),
        # FOREIGN KEY (dataset_id) REFERENCES Datasets(id),
        # FOREIGN KEY (tag_id) REFERENCES Tags(id)
    # );"""
    # )
    # conn.commit()
    # conn.close()


# TODO: Add tests for this function
# Tests:
# - Check for error when the path already exists
# - Check if the directory is created
# - Check if the database is created
def init_qanatdir(path, logger=None):
    """Initialize a new Qanat repository.

    :param path: The path to the new repository.
    :type path: str

    :param logger: The logger to use for information display.
    :type logger: logging.Logger
    """

    if logger is None:
        logger = setup_logger("Init")

    # Check if the path is valid
    if os.path.exists(os.path.join(path, ".qanat")):
        logger.error(f"The path: {path} already exists.")
        raise FileExistsError("The path already exists.")

    # Create the directory
    logger.info(f"Creating the directory: {os.path.join(path, '.qanat')}")
    os.mkdir(os.path.join(path, ".qanat"))

    # Create the database
    logger.info(f"Creating the dB: {os.path.join(path, '.qanat', 'qanat.db')}")
    engine, Base = init_database(os.path.join(path, ".qanat", "qanat.db"))

    return engine, Base

