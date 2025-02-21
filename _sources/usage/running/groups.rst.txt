===============================================================
Running several groups of parameters in a single run
===============================================================

An experiment run can be the result of the execution of the executable with different groups of arguments. This is useful for cases such as:

* Extensive testing of hyperparameters over a grid: testing several values to find the best one regarding to a criterion
* Aggregating statistics over all the paramters tested : for example, accucaries means/variance over K-folds/different seeds in machine learning experiments

In both case, we want to store the results of the different parameters in a single run to then perform some action on the sub-runs.

To achieve this Qanat propose the notion of **group** which is an execution of the executable with a set of parameters. A run can then be composed of several groups. In practice, this means that the :code:`storage_path` directory corresponding to the run will be composed of sub-folders named :code:`group_0, group_1, etc` and the **info.yaml** will need to be parsed by your action to find the correspondance between a group and its set of parameters.

To do this two options:

From the command-line
----------------------

You can precise groups thanks to the following syntax:

.. code:: console

   qanat experiment run <experiment_name> [some fixed args] -g "1 --opt1 value1" -g "2 --opt1 value2" -r "--opt2 start end step" [--n_threads NTHREADS] [runner, container, etc options]

Several things to be said about this:

* You can always provide fixed arguments liek usual. They will be applied to all executions.
* The option :code:`-g` allows to define a group meaning that what is written after between quotes will correspond to a group. Then any subsequent option :code:`-g` will be considered as an alternate group (at set of parameters that will be run separately).
* The option :code:`--n_threads` allows when running on a :code:`local` runner to run the different commands in parallel with the number of threads specified. When on a job system, the commands are executed as different jobs anyway.
* You don't have to use the same positional arguments or options between groups.
* Finally there is an option to do a range over options values with the :code:`-r` option by precising the name of the option, the start, end and step. When mixing groups and range, a Cartesian products will be done between different groups and range values.


To make it more clear, let's take an example:

.. code:: console

   qanat experiment run AFEW_generalisation --n_samples 1000 -g "--hd '[100, 50]'" -g "--hd '[100, 50, 20]'" -r "--seed 0 10 1" --dry_run

which is a run of an machine learning experiment where the model size can change (option :code:`--hd`) for which we run the training at different seeds. The option :code:`--dry_run` allows to output the parased parameters rather than running the experiment:

.. code:: console

   [08:41:34] INFO     Dry run: Showing parsed parameters without running the experiment.                                            run.py:1051
           INFO     Parsed parameters:                                                                                               run.py:1058
                     - Group 0:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 0.0
                     - Group 1:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 0.0
                     - Group 2:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 1.0
                     - Group 3:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 1.0
                     - Group 4:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 2.0
                     - Group 5:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 2.0
                     - Group 6:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 3.0
                     - Group 7:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 3.0
                     - Group 8:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 4.0
                     - Group 9:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 4.0
                     - Group 10:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 5.0
                     - Group 11:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 5.0
                     - Group 12:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 6.0
                     - Group 13:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 6.0
                     - Group 14:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 7.0
                     - Group 15:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 7.0
                     - Group 16:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 8.0
                     - Group 17:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 8.0
                     - Group 18:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50]'
                        ◼ --seed: 9.0
                     - Group 19:
                        ◼ --n_samples: 1000
                        ◼ --hd: '[100, 50, 20]'
                        ◼ --seed: 9.0

As you can see:

* We iterate over the option :code:`--seed` by steps of one from 0 to 9 included. Remark that the value is a float so it needs casting to **int** in the executable.
* For each of those seeds, we have a group with a smaller and one a bigger model size.
* Since the :code:`n_samples` is not included in the range or groups, it is common to all executions.

The results repertory has the following structure:

.. code:: console

    tree results/AFEW_generalisation/run_38/

    results/AFEW_generalisation/run_38/
    ├── group_0
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_1
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_10
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_11
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_12
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_13
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_14
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_15
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_16
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_17
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_18
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_19
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_2
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_3
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_4
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_5
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_6
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_7
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_8
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    ├── group_9
    │   ├── group_info.yaml
    │   ├── stderr.txt
    │   └── stdout.txt
    └── info.yaml


To know which group correspond to which parameters, in an action over this run, there are files **group_info.yaml** in each directory. For example, for group 0:

.. code::

    command: python experiments/generalisation_stacking/main_AFEW.py --n_samples 1000 --hd '[100, 50]' --seed 0.0 --storage_path /home/ammarmian/Desktop/MUST/research_projects/spd_autoencoder/results/AFEW_generalisation/run_38/group_0 --dataset_path /home/ammarmian/Desktop/MUST/research_projects/spd_autoencoder/data/AFEW_spdnet
    parameters:
      --hd: '''[100, 50]'''
      --n_samples: '1000'
      --seed: '0.0'

Alternatively, the **info.yaml** has those informations for all the groups.

From a param_file precising the arguments and their variation
--------------------------------------------------------------

You can use the option :code:`--param_file`:

.. code:: console

   qanat experiment run <experiment_name> --param_file yourfile.yaml [--n_threads NTHREADS] [runner, container, etc options]

.. warning::

   To not confuse with :code:`--parameters_file` which correspond to a single set of parameters that is parsed by your executable.

For more information about this approach see `the page about it <../description_files/run.html>`_.
