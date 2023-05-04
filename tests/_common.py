# ========================================
# FileName: _common.py
# Date: 04 mai 2023 - 13:55
# Author: Ammar Mian
# Email: ammar.mian@univ-smb.fr
# GitHub: https://github.com/ammarmian
# Brief: Common things used in several tests
# =========================================


def get_scenario(scenario_no: int) -> dict:
    """Return a scenario dictionary for 7 representative
    scenarios:
        * Scenario 1: experiment with no dataset
                        no tag and no action, no runs
        * Scenario 2: One experiment with one dataset, no tag
                        and no action, no runs
        * Scenario 3: experiment with several datasets, tags
                        and no actions, no runs
        * Scenario 4: experiment with several datasets and several
                        actions, tags, no runs
        * Scenario 5: Several experiments with several datasets and
                        several actions, tags, no runs
        * Scenario 6: Several experiments with several datasets and
                        several actions, tags, several runs
        * Scenario 7: Several experiments with several datasets and
                        several actions, tags, several runs, several

    :param scenario_no: The scenario number
    :type scenario_no: int

    :return: The scenario dictionary
    :rtype: dict
    """
    scenarios = []

    # Scenario 1: experiment with no dataset
    #             no tag and no action, no runs
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/bash",
            }
        ],
        "datasets": [],
        "tags": [],
        "actions": [],
        "runs": [],
    }
    scenarios.append(tocreate)

    # Scenario 2: One experiment with one dataset, no tag
    #             and no action, no runs
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "executable": "exp1 executable",
                "executable_command": "/usr/bin/bash",
                "path": "exp1 path/",
            },
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [1],
            }
        ],
        "tags": [],
        "actions": [],
        "runs": [],
    }
    scenarios.append(tocreate)

    # Scenario 3: experiment with several datasets, tags
    #             and no actions, no runs
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/python",
            }
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [1],
            },
            {
                "name": "dataset2",
                "description": "dataset2 description",
                "path": "dataset2 path/",
            },
        ],
        "tags": [
            {
                "dataset_no": [1],
                "name": "tag1",
                "description": "tag1 description",
            },
            {
                "dataset_no": [1, 2],
                "name": "tag2",
                "description": "tag2 description",
            },
            {
                "experiment_no": [1],
                "name": "tag3",
                "description": "tag3 description",
            },
            {
                "experiment_no": [1],
                "dataset_no": [1, 2],
                "name": "tag4",
                "description": "tag4 description",
            },
        ],
        "actions": [],
        "runs": [],
    }
    scenarios.append(tocreate)

    # Scenario 4: experiment with several datasets and several
    #             actions, tags, no runs
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/python",
            }
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [1],
            },
            {
                "name": "dataset2",
                "description": "dataset2 description",
                "path": "dataset2 path/",
            },
        ],
        "tags": [
            {
                "dataset_no": [1],
                "name": "tag1",
                "description": "tag1 description",
            },
            {
                "dataset_no": [1, 2],
                "name": "tag2",
                "description": "tag2 description",
            },
            {
                "experiment_no": [1],
                "name": "tag3",
                "description": "tag3 description",
            },
            {
                "experiment_no": [1],
                "dataset_no": [1, 2],
                "name": "tag4",
                "description": "tag4 description",
            },
        ],
        "actions": [
            {
                "name": "action1",
                "description": "action1 description",
                "executable": "action1 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 1,
            },
            {
                "name": "action2",
                "description": "action2 description",
                "executable": "action2 executable",
                "executable_command": "/usr/bin/julia",
                "experiment_no": 1,
            },
        ],
        "runs": [],
    }
    scenarios.append(tocreate)

    # Scenario 5: Several experiments with several datasets and
    #             several actions, tags, no runs
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp2",
                "description": "exp2 description",
                "path": "exp2 path/",
                "executable": "exp2 path/exp2 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp3",
                "description": "exp3 description",
                "path": "exp3 path/",
                "executable": "exp3 path/exp3 executable.sh",
                "executable_command": "/usr/bin/julia",
            },
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [2, 3],
            },
            {
                "name": "dataset2",
                "description": "dataset2 description",
                "path": "dataset2 path/",
                "experiment_no": [1],
            },
        ],
        "tags": [
            {
                "dataset_no": [1, 2],
                "name": "tag1",
                "description": "tag1 description",
            },
            {
                "dataset_no": [2],
                "name": "tag2",
                "description": "tag2 description",
            },
            {
                "type": ["experiment"],
                "experiment_no": [3],
                "name": "tag3",
                "description": "tag3 description",
            },
            {
                "type": ["experiment", "dataset"],
                "experiment_no": [1, 2],
                "dataset_no": [1, 2],
                "name": "tag4",
                "description": "tag4 description",
            },
        ],
        "actions": [
            {
                "name": "action1",
                "description": "action1 description",
                "executable": "action1 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 1,
            },
            {
                "name": "action2",
                "description": "action2 description",
                "executable": "action2 executable",
                "executable_command": "/usr/bin/julia",
                "experiment_no": 1,
            },
            {
                "name": "action3",
                "description": "action3 description",
                "executable": "action3 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 2,
            },
        ],
        "runs": [],
    }
    scenarios.append(tocreate)

    # Scenario 6: Several experiments with several datasets and
    #             several actions, tags, runs, no parameters
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp2",
                "description": "exp2 description",
                "path": "exp2 path/",
                "executable": "exp2 path/exp2 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp3",
                "description": "exp3 description",
                "path": "exp3 path/",
                "executable": "exp3 path/exp3 executable.sh",
                "executable_command": "/usr/bin/julia",
            },
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [2],
            },
            {
                "name": "dataset2",
                "description": "dataset2 description",
                "path": "dataset2 path/",
                "experiment_no": [2, 3],
            },
        ],
        "tags": [
            {
                "dataset_no": [1, 2],
                "name": "tag1",
                "description": "tag1 description",
            },
            {
                "dataset_no": [2],
                "name": "tag2",
                "description": "tag2 description",
            },
            {
                "experiment_no": [3],
                "name": "tag3",
                "description": "tag3 description",
            },
            {
                "experiment_no": [1, 2],
                "dataset_no": [1, 2],
                "name": "tag4",
                "description": "tag4 description",
            },
            {
                "run_no": [1, 2, 3],
                "name": "tag5",
                "description": "tag5 description",
            }
        ],
        "actions": [
            {
                "name": "action1",
                "description": "action1 description",
                "executable": "action1 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 1,
            },
            {
                "name": "action2",
                "description": "action2 description",
                "executable": "action2 executable",
                "executable_command": "/usr/bin/julia",
                "experiment_no": 1,
            },
            {
                "name": "action3",
                "description": "action3 description",
                "executable": "action3 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 2,
            },
        ],
        "runs": [
            {
                "experiment_no": 1,
                "launched": "2018-01-01 00:00:00",
                "finished": "2018-01-01 00:00:00",
                "status": "finished",
                "parameters": [],
                "description": "run1 description",
                "metric": "run1 metric",
                "storage_path": "run1 storage_path/",
                "commit_sha": "run1 commit_sha",
            },
            {
                "experiment_no": 1,
                "launched": "2018-02-01 00:00:00",
                "finished": "2018-03-01 00:00:00",
                "status": "running",
                "parameters": [],
                "description": "run2 description",
                "metric": "run2 metric",
                "storage_path": "run2 storage_path/",
                "commit_sha": "run2 commit_sha",
            },
            {
                "experiment_no": 3,
                "launched": "2018-01-01 00:00:00",
                "finished": "2018-07-01 00:00:00",
                "status": "not started",
                "parameters": [],
                "description": "run3 description",
                "metric": "run3 metric",
                "storage_path": "run3 storage_path/",
                "commit_sha": "run3 commit_sha",
            },
        ],
    }
    scenarios.append(tocreate)

    # Scenario 7: Several experiments with several datasets and
    #             several actions, tags, runs, parameters
    tocreate = {
        "experiments": [
            {
                "name": "exp1",
                "description": "exp1 description",
                "path": "exp1 path/",
                "executable": "exp1 path/exp1 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp2",
                "description": "exp2 description",
                "path": "exp2 path/",
                "executable": "exp2 path/exp2 executable.sh",
                "executable_command": "/usr/bin/python",
            },
            {
                "name": "exp3",
                "description": "exp3 description",
                "path": "exp3 path/",
                "executable": "exp3 path/exp3 executable.sh",
                "executable_command": "/usr/bin/julia",
            },
        ],
        "datasets": [
            {
                "name": "dataset1",
                "description": "dataset1 description",
                "path": "dataset1 path/",
                "experiment_no": [2],
            },
            {
                "name": "dataset2",
                "description": "dataset2 description",
                "path": "dataset2 path/",
                "experiment_no": [1, 2, 3],
            },
        ],
        "tags": [
            {
                "dataset_no": [1, 2],
                "name": "tag1",
                "description": "tag1 description",
            },
            {
                "dataset_no": [2],
                "name": "tag2",
                "description": "tag2 description",
            },
            {
                "type": ["experiment"],
                "experiment_no": [3],
                "name": "tag3",
                "description": "tag3 description",
            },
            {
                "experiment_no": [1, 2],
                "dataset_no": [1, 2],
                "name": "tag4",
                "description": "tag4 description",
            },
            {
                "run_no": [1, 2],
                "name": "tag5",
                "description": "tag5 description",
            },
            {
                "run_no": [1, 2, 3],
                "experiment_no": [1, 2],
                "dataset_no": [1, 2],
                "name": "tag6",
                "description": "tag6 description",
            },
        ],
        "actions": [
            {
                "name": "action1",
                "description": "action1 description",
                "executable": "action1 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 1,
            },
            {
                "name": "action2",
                "description": "action2 description",
                "executable": "action2 executable",
                "executable_command": "/usr/bin/julia",
                "experiment_no": 1,
            },
            {
                "name": "action3",
                "description": "action3 description",
                "executable": "action3 executable",
                "executable_command": "/usr/bin/bash",
                "experiment_no": 2,
            },
        ],
        "runs": [
            {
                "experiment_no": 1,
                "launched": "2018-01-01 00:00:00",
                "finished": "2018-01-01 00:00:00",
                "status": "finished",
                "parameters": [
                    {
                        "pos0": "value0",
                        "pos1": "value1",
                        "--opt0": "value0",
                    },
                ],
                "description": "run1 description",
                "metric": "run1 metric",
                "storage_path": "run1 storage_path/",
                "commit_sha": "run1 commit_sha",
            },
            {
                "experiment_no": 1,
                "launched": "2018-02-01 00:00:00",
                "finished": "2018-03-01 00:00:00",
                "status": "running",
                "parameters": [
                    {
                        "pos0": "value0",
                        "pos1": "value1",
                        "--opt0": "value0",
                    },
                    {
                        "pos0": "value0",
                        "pos1": "value1",
                        "--opt0": "value0",
                        "--opt1": "value1",
                    },
                ],
                "description": "run2 description",
                "metric": "run2 metric",
                "storage_path": "run2 storage_path/",
                "commit_sha": "run2 commit_sha",
            },
            {
                "experiment_no": 3,
                "launched": "2018-01-01 00:00:00",
                "finished": "2018-07-01 00:00:00",
                "status": "not started",
                "parameters": [],
                "description": "run3 description",
                "metric": "run3 metric",
                "storage_path": "run3 storage_path/",
                "commit_sha": "run3 commit_sha",
            },
        ],
    }
    scenarios.append(tocreate)

    return scenarios[scenario_no-1]
