# ========================================
# FileName: test_core_database.py
# Date: 04 mai 2023 - 13:00
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Test databas of the core module
# =========================================

from qanat.core import database
import tempfile
import unittest
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import DeclarativeMeta
from sqlalchemy.orm.session import Session
from sqlalchemy import inspect
from ._common import get_scenario


class TestDatabaseBasics(unittest.TestCase):
    """Test database related functionalities."""

    def test_init_database(self):
        """Test the creation of a database."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            engine, Base = database.init_database(tmp.name)

            assert engine is not None
            assert Base is not None
            assert isinstance(engine, Engine)
            assert isinstance(Base, DeclarativeMeta)

    def test_open_existing_database(self):
        """Test opening an existing database."""
        with tempfile.NamedTemporaryFile(suffix=".db") as tmp:
            engine, Base = database.init_database(tmp.name)
            engine, Base, session = database.open_database(tmp.name)

            session_ = session()

            assert engine is not None
            assert Base is not None
            assert isinstance(engine, Engine)
            assert isinstance(Base, DeclarativeMeta)
            assert isinstance(session_, Session)

            # Check whether the database structure correspond to
            # the expected one.
            assert inspect(engine).has_table("experiments")
            assert inspect(engine).has_table("datasets")
            assert inspect(engine).has_table("tags")
            assert inspect(engine).has_table("experiments_tags")
            assert inspect(engine).has_table("datasets_tags")
            assert inspect(engine).has_table("datasets_experiments")
            assert inspect(engine).has_table("actions")
            assert inspect(engine).has_table("groups_of_parameters")
            assert inspect(engine).has_table("runs_of_experiments")
            assert inspect(engine).has_table("runs_tags")


class TestDatabaseAddingStuffDummy(unittest.TestCase):
    """Testing adding stuff to the database."""

    def setUp(self):
        """Set up the database."""
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db")
        self.engine, self.Base = database.init_database(self.temp_db_file.name)
        self.engine, self.Base, session = database.open_database(
                self.temp_db_file.name)
        self.session = session()

    def tearDown(self):
        """Close the database and remove tempfile."""
        self.session.close()

    def test_add_experiment(self):
        """Test adding a dummy experiment."""
        database.add_experiment(
            self.session,
            path="test path",
            name="test name",
            description="this is a test description",
            executable="test executable.sh",
            executable_command="/usr/bin/bash",
        )

        # Check whether the experiment has been added.
        exp = self.session.query(database.Experiment).first()
        self.assertEqual(exp.path, "test path")
        self.assertEqual(exp.name, "test name")
        self.assertEqual(exp.description, "this is a test description")
        self.assertEqual(exp.executable, "test executable.sh")
        self.assertEqual(exp.executable_command, "/usr/bin/bash")

    def test_add_dataset(self):
        """Test adding a dummy dataset."""
        database.add_dataset(
            self.session,
            path="test path",
            name="test name",
            description="this is a test description",
        )

        # Check whether the dataset has been added.
        dataset = self.session.query(database.Dataset).first()
        self.assertEqual(dataset.path, "test path")
        self.assertEqual(dataset.name, "test name")
        self.assertEqual(dataset.description, "this is a test description")

    def test_add_tag(self):
        """Test adding a dummy tag."""
        database.add_tag(
            self.session, name="test tag",
            description="this is a test description"
        )

        # Check whether the tag has been added.
        tag = self.session.query(database.Tags).first()
        self.assertEqual(tag.name, "test tag")

    def test_add_action(self):
        """Test adding a dummy action."""
        database.add_experiment(
            self.session,
            path="test path",
            name="test experiment action",
            description="this is a test description",
            executable="test executable.sh",
            executable_command="/usr/bin/bash",
        )
        database.add_action(
            self.session,
            name="test action",
            description="this is a test description",
            executable="test executable.sh",
            executable_command="/usr/bin/bash",
            experiment_name="test experiment action",
        )

        # Find experiment id
        exp_id = database.find_experiment_id(self.session,
                                             "test experiment action")

        # Check whether the action has been added.
        action = self.session.query(database.Action).first()
        self.assertEqual(action.name, "test action")
        self.assertEqual(action.description, "this is a test description")
        self.assertEqual(action.executable, "test executable.sh")
        self.assertEqual(action.executable_command, "/usr/bin/bash")
        self.assertEqual(action.experiment_id, exp_id)


class TestDatabaseCreationScenario(unittest.TestCase):
    """Test the creation of a database with the
    expected use-case scenarios."""

    def setUp(self):
        """Set up the database."""
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db")
        self.engine, self.Base = database.init_database(self.temp_db_file.name)
        self.engine, self.Base, session = database.open_database(
                self.temp_db_file.name)
        self.session = session()

    def tearDown(self):
        """Close the database and remove tempfile."""
        self.session.close()

    def construct_scenario(self, scenario_number: int):
        """Helper method to construct all the elements
        of the scenario."""

        scenario = get_scenario(scenario_number)

        # Start with tags to have them in the database
        for tag in scenario["tags"]:
            database.add_tag(
                self.session, name=tag["name"], description=tag["description"]
            )

        # Add datasets
        for i, dataset in enumerate(scenario["datasets"]):

            # Find if a tag corresponds to this dataset
            tag_names = []
            for tag in scenario["tags"]:
                if "dataset_no" in tag.keys():
                    for number in tag["dataset_no"]:
                        if number == i + 1:
                            tag_names.append(tag["name"])

            database.add_dataset(
                self.session,
                path=dataset["path"],
                name=dataset["name"],
                description=dataset["description"],
                tags=tag_names
            )

        # Add experiments
        for i, experiment in enumerate(scenario["experiments"]):

            # Find if a dataset references this experiment
            dataset_names = []
            for dataset in scenario["datasets"]:
                if "experiment_no" in dataset.keys():
                    for number in dataset["experiment_no"]:
                        if number == i + 1:
                            dataset_names.append(dataset["name"])

            # Find if a tag corresponds to this experiment
            tag_names = []
            for tag in scenario["tags"]:
                if "experiment_no" in tag.keys():
                    for number in tag["experiment_no"]:
                        if number == i + 1:
                            tag_names.append(tag["name"])

            # Add experiment
            database.add_experiment(
                self.session,
                path=experiment["path"],
                name=experiment["name"],
                description=experiment["description"],
                executable=experiment["executable"],
                executable_command=experiment["executable_command"],
                tags=tag_names,
                datasets=dataset_names
            )

        # Add actions
        for action in scenario["actions"]:
            experiment_name = \
                    scenario["experiments"][action['experiment_no']-1]["name"]
            database.add_action(
                self.session,
                name=action["name"],
                description=action["description"],
                executable=action["executable"],
                executable_command=action["executable_command"],
                experiment_name=experiment_name
            )

        # Add runs and group of experiments if needed
        for i, run in enumerate(scenario["runs"]):

            # Find if a tag corresponds to this run
            tag_names = []
            for tag in scenario["tags"]:
                if "run_no" in tag.keys():
                    for number in tag["run_no"]:
                        if number == i + 1:
                            tag_names.append(tag["name"])

            # Add run
            experiment_name = \
                scenario["experiments"][run['experiment_no']-1]["name"]
            database.add_run(
                self.session,
                experiment_name=experiment_name,
                storage_path=run["storage_path"],
                commit_sha=run["commit_sha"],
                parameters_groups=run["parameters_groups"],
                description=run["description"],
                tags=tag_names
            )

        return scenario

    def test_scenario_1(self):
        """Testing with scenario number 1:
        1 experiment and nothing else."""
        scenario = self.construct_scenario(1)

        # Assert one experience in database, no datasets, no tags,
        # no actions and no runs.
        self.assertEqual(self.session.query(database.Experiment).count(), 1)
        self.assertEqual(self.session.query(database.Dataset).count(), 0)
        self.assertEqual(self.session.query(database.Tags).count(), 0)
        self.assertEqual(self.session.query(database.Action).count(), 0)
        self.assertEqual(
                self.session.query(database.RunOfAnExperiment).count(), 0)

        # Assert the experiment is the one expected
        experiment = self.session.query(database.Experiment).first()
        self.assertEqual(experiment.path, scenario["experiments"][0]["path"])
        self.assertEqual(experiment.name, scenario["experiments"][0]["name"])
        self.assertEqual(
            experiment.description, scenario["experiments"][0]["description"]
        )
        self.assertEqual(
            experiment.executable, scenario["experiments"][0]["executable"]
        )
        self.assertEqual(
            experiment.executable_command,
            scenario["experiments"][0]["executable_command"],
        )

    def test_scenario_2(self):
        """Testing with scenario number 2:
        1 experiment, 1 dataset and nothing else."""
        scenario = self.construct_scenario(2)

        # Assert one experience in database, one dataset, no tags,
        # no actions and no runs.
        self.assertEqual(self.session.query(database.Experiment).count(), 1)
        self.assertEqual(self.session.query(database.Dataset).count(), 1)
        self.assertEqual(self.session.query(database.Tags).count(), 0)
        self.assertEqual(self.session.query(database.Action).count(), 0)
        self.assertEqual(
                self.session.query(database.RunOfAnExperiment).count(), 0)

        # Assert if the dataset is the one expected
        dataset = self.session.query(database.Dataset).first()
        self.assertEqual(dataset.path, scenario["datasets"][0]["path"])
        self.assertEqual(dataset.name, scenario["datasets"][0]["name"])
        self.assertEqual(
            dataset.description, scenario["datasets"][0]["description"]
        )

        # Assert if the link betwen the dataset and the experiment in
        # the database is made
        experiment_id = database.find_experiment_id(
            self.session, scenario["experiments"][0]["name"]
        )
        dataset_id = database.find_dataset_id(
            self.session, scenario["datasets"][0]["name"]
        )
        self.assertEqual(
            self.session.query(database.DatasetExperiment).filter_by(
                experiment_id=experiment_id, dataset_id=dataset_id
            ).count(),  1
        )

    def test_scenario_3(self):
        """Testing with scenario number 3:
        1 experiment, 2 datasets, 4 tags and nothing else."""
        scenario = self.construct_scenario(3)

        # Assert one experience in database, two datasets, four tags,
        # no actions and no runs.
        self.assertEqual(self.session.query(database.Experiment).count(), 1)
        self.assertEqual(self.session.query(database.Dataset).count(), 2)
        self.assertEqual(self.session.query(database.Tags).count(), 4)
        self.assertEqual(self.session.query(database.Action).count(), 0)
        self.assertEqual(
                self.session.query(database.RunOfAnExperiment).count(), 0)

        # Assert if the datasets are the ones expected
        dataset_1 = self.session.query(database.Dataset).first()
        dataset_2 = self.session.query(database.Dataset).all()[1]
        self.assertEqual(dataset_1.path, scenario["datasets"][0]["path"])
        self.assertEqual(dataset_1.name, scenario["datasets"][0]["name"])
        self.assertEqual(
            dataset_1.description, scenario["datasets"][0]["description"]
        )
        self.assertEqual(dataset_2.path, scenario["datasets"][1]["path"])
        self.assertEqual(dataset_2.name, scenario["datasets"][1]["name"])
        self.assertEqual(
            dataset_2.description, scenario["datasets"][1]["description"]
        )

        # Assert if the link betwen the datasets and the experiment in
        # the database is made
        experiment_id = database.find_experiment_id(
            self.session, scenario["experiments"][0]["name"]
        )
        dataset_1_id = database.find_dataset_id(
            self.session, scenario["datasets"][0]["name"]
        )
        self.assertEqual(
            self.session.query(database.DatasetExperiment).filter_by(
                experiment_id=experiment_id, dataset_id=dataset_1_id
            ).count(),  1
        )

        # Assert if the tags are the ones expected
        tags_list = self.session.query(database.Tags).all()
        for tag_no in range(4):
            self.assertEqual(tags_list[tag_no].name,
                             scenario["tags"][tag_no]["name"])
            self.assertEqual(tags_list[tag_no].description,
                             scenario["tags"][tag_no]["description"])

        # Assert if the link betwen the tags and the experiment in
        # the database is made
        experiment_id = database.find_experiment_id(
            self.session, scenario["experiments"][0]["name"]
        )
        for tag_no in range(4):
            if "experiment_no" in scenario['tags'][tag_no].keys():
                if 1 in scenario['tags'][tag_no]['experiment_no']:
                    tag_id = database.find_tag_id(
                        self.session, scenario["tags"][tag_no]["name"]
                    )
                    self.assertEqual(
                        self.session.query(database.ExperimentsTags).filter_by(
                            experiment_id=experiment_id, tag_id=tag_id
                        ).count(),  1
                    )


class TestDataClassesDummy(unittest.TestCase):
    """Test data classes used for represening
    the database."""

    def test_Experimentclass(self):
        """Test the Experiment class with basic dummy
        values."""
        exp = database.Experiment(
            path="test path",
            name="test name",
            description="this is a test description",
            executable="test executable.sh",
            executable_command="/usr/bin/bash",
            created="2020-04-04 00:00:00",
            updated="2020-04-04 00:00:00",
        )
        self.assertEqual(exp.path, "test path")
        self.assertEqual(exp.name, "test name")
        self.assertEqual(exp.description, "this is a test description")
        self.assertEqual(exp.executable, "test executable.sh")
        self.assertEqual(exp.executable_command, "/usr/bin/bash")
        self.assertEqual(exp.created, "2020-04-04 00:00:00")
        self.assertEqual(exp.updated, "2020-04-04 00:00:00")

    def test_DatasetClass(self):
        """Test the Dataset class with basic dummy
        values."""
        dataset = database.Dataset(
            path="test path",
            name="test name",
            description="this is a test description",
            created="2020-04-04 00:00:00",
            updated="2020-04-04 00:00:00",
        )
        self.assertEqual(dataset.path, "test path")
        self.assertEqual(dataset.name, "test name")
        self.assertEqual(dataset.description, "this is a test description")
        self.assertEqual(dataset.created, "2020-04-04 00:00:00")
        self.assertEqual(dataset.updated, "2020-04-04 00:00:00")

    def test_TagsClass(self):
        """Test the Tags class with basic dummy
        values."""
        tag = database.Tags(name="test name",
                            description="this is a test description")
        self.assertEqual(tag.name, "test name")
        self.assertEqual(tag.description, "this is a test description")

    def test_ActionClass(self):
        """Test the Action class with basic dummy
        values."""
        action = database.Action(
            name="test name",
            description="this is a test description",
            experiment_id=1,
            executable="test executable.sh",
            executable_command="/usr/bin/bash",
            created="2020-04-04 00:00:00",
            updated="2020-04-04 00:00:00",
        )
        self.assertEqual(action.name, "test name")
        self.assertEqual(action.description, "this is a test description")
        self.assertEqual(action.experiment_id, 1)
        self.assertEqual(action.executable, "test executable.sh")
        self.assertEqual(action.executable_command, "/usr/bin/bash")
        self.assertEqual(action.created, "2020-04-04 00:00:00")
        self.assertEqual(action.updated, "2020-04-04 00:00:00")

    def test_RunOfAnExperimenClass(self):
        """Test the RunOfAnExperiment class with basic dummy
        values."""

        run = database.RunOfAnExperiment(
            experiment_id=1,
            launched="2020-04-04 00:00:00",
            finished="2020-04-04 00:00:00",
            status="finished",
            storage_path="test path",
            description="this is a test description",
            metric="test metric",
            parameters={"pos0": 0, "pos1": 1, "--opt": 2},
            commit_sha="test commit sha",
        )
        self.assertEqual(run.experiment_id, 1)
        self.assertEqual(run.launched, "2020-04-04 00:00:00")
        self.assertEqual(run.finished, "2020-04-04 00:00:00")
        self.assertEqual(run.status, "finished")
        self.assertEqual(run.storage_path, "test path")
        self.assertEqual(run.description, "this is a test description")
        self.assertEqual(run.metric, "test metric")
        self.assertEqual(run.parameters, {"pos0": 0, "pos1": 1, "--opt": 2})
        self.assertEqual(run.commit_sha, "test commit sha")

    def test_RunsTagsClass(self):
        """Test the RunsTags class with basic dummy
        values."""
        runtags = database.RunsTags(run_id=1, tag_id=1)
        self.assertEqual(runtags.run_id, 1)
        self.assertEqual(runtags.tag_id, 1)

    def test_GroupOfParametersOfARun(self):
        """Test the GroupOfParametersOfARun class with basic dummy
        values."""

        group = database.GroupOfParametersOfARun(
            run_id=1, values={"pos0": 0, "pos1": 1, "--opt": 2, "--opt2": 3}
        )
        self.assertEqual(group.run_id, 1)
        self.assertEqual(group.values,
                         {"pos0": 0, "pos1": 1, "--opt": 2, "--opt2": 3})

    def test_DatasetExperimentClass(self):
        """Test the DatasetExperiment class with basic dummy
        values."""

        datasetexp = database.DatasetExperiment(dataset_id=1, experiment_id=1)
        self.assertEqual(datasetexp.dataset_id, 1)
        self.assertEqual(datasetexp.experiment_id, 1)

    def test_ExperimentsTagsClass(self):
        """Test the ExperimentTags class with basic dummy
        values."""

        experimenttags = database.ExperimentsTags(experiment_id=1, tag_id=1)
        self.assertEqual(experimenttags.experiment_id, 1)
        self.assertEqual(experimenttags.tag_id, 1)

    def test_DatasetsTagsClass(self):
        """Test the DatasetTags class with basic dummy
        values."""

        datasettags = database.DatasetsTags(dataset_id=1, tag_id=1)
        self.assertEqual(datasettags.dataset_id, 1)
        self.assertEqual(datasettags.tag_id, 1)
