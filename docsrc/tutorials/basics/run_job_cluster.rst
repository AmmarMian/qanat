Running experiments through a job system
============================================
.. sectnum::
  :start: 3

.. note::
   In this tutorial, we will see how to run experiments through a job allocation system. It is comprised of two parts depending on the cluster configuration:
    * The case of HTCondor (https://htcondor.readthedocs.io/en/latest/) system
    * The case of SLURM (https://slurm.schedmd.com/documentation.html) system

.. note::
   The code of this tutorial is available at: TODO


Objectives
----------

In this tutorial we will try to run the previous tutorial (:doc:`experiment_dataset_yaml`) through a job allocation system. We will see how to take the existing Qanat project structure and run the experiments on the cluster.


Setting up the project and environment
--------------------------------------


We assume that you already have done the previous tutorial (:doc:`experiment_dataset_yaml`) or downloaded its code and setup the Qanat project. If you did it on your local machine that do not have a job system, you need to copy the project over to the job submission server or redo those steps on the machine.

The problem that needs adressing is to have installation of python working on both the job submission server and the job execution server. This is because the job submission server will be responsible for submitting the jobs to the job execution server and will need to have Qanat installed. The job execution server will be responsible for running the experiments and should be able to execute the scripts of the experiments.

One workaround that is useful is to recast the experiment executable as a bash script that will do the following:
    * Make it so that the python environment is setup. This can be done depending on your setup:
        * If you are using conda, you can use the conda activate command to activate the environment that will be stored in a shared filesystem between the job submission server and the job execution server.
        * If you have a working python executable somewhere in the shared filesystem, you can use it to run the experiment by specifying the full path to the python executable.
    * Run the python script of the experiment by also forwarding the arguments to the script. This can be done by using the $@ variable in bash and it is very important since the python script need to access the `--storage_path` and `--dataset_path` options.

In this case, you need to update the experiment executable and executable command with `qanat experiment update summary_iris`.

Another approach is to use a containerized environment. This is a more robust approach but requires more setup. We will not cover it in this tutorial. See (TODO-ADD-LINK) for more information.

.. warning::
   We assume in Qanat that the current working directory is available on the job execution server. This is because the experiment executable is a python script that is run from the current working directory. This a limitation of the package.

HTCondor
--------

Usually when submitting a job through HTCondor, you need to specify a submit description file (`jobname.submit`) that will contain the description of the job. This file will contain the following information:
    * The executable that will be run
    * The arguments that will be passed to the executable
    * The environment variables that will be set
    * The input and output files that will be used
    * The resources that will be used
    * The queue that will be used

See (https://htcondor.readthedocs.io/en/latest/users-manual/submitting-a-job.html) for more information.

Qanat takes a similar approach but ditch the need of a submit description file for each executable. Instead, we use YAML description file as a template that will contain the keywords (ressources, groups, etc). When running Qanat will parse those descriptors and submit a job with the right executable and arguments for you thanks to the python bindings of HTCondor.

For example, the default template (when no template is specified for a job) is the following:

.. code-block:: yaml

    +WishedAcctGroup: group_usmb.listic
    getenv: 'true'
    request_cpus: 1
    request_disk: 1GB
    request_gpus: 0
    request_memory: 1GB
    universe: vanilla

.. note::
   The `+WishedAcctGroup` is a custom keyword that is used to specify the group that will be used for the job. It is used by the job allocation system to determine the group that will be used for the job. The default group is the one I have in the MUST datacenter of Université Savoie Mont-Blanc. You will need to change it in the `.qanat/config.yaml` according to your needs.

In order to run the experiment through HTCondor, we need two things:
    * to specify the runner as `htcondor` when running the experiment with `qanat run` command
    * to specify the template that will be used for the job. This can be done by specifying the `--submit_template` option to put at the end of the `qanat run` command. If no template is specified, the previous default one is used.

A command to run the experiment through HTCondor would be:

.. code-block:: bash

    qanat run --runner htcondor summary_iris --submit_template htcondor_template.yaml

Another approach to have several templates without having different templates files is to put them in the qanat configuration file `.qanat/config.yaml` which looks like:

.. code-block:: yaml

    default_editor: vim
    htcondor:
      default:
        +WishedAcctGroup: group_usmb.listic
        getenv: 'true'
        request_cpus: 1
        request_disk: 1GB
        request_gpus: 0
        request_memory: 1GB
        universe: vanilla
    logging: INFO
    result_dir: results
    slurm:
      default:
        --cpus-per-task: 1
        --ntasks: 1
        --time: 1-00:00:00

You can edit the file to add your own templates. For example, if you want to add a template for a job that will use 2 cpus and 2GB of memory, you can add the following lines:

.. code-block:: yaml

    htcondor:
      default:
        +WishedAcctGroup: group_usmb.listic
        getenv: 'true'
        request_cpus: 1
        request_disk: 1GB
        request_gpus: 0
        request_memory: 1GB
        universe: vanilla
      two_cpus:
        +WishedAcctGroup: group_usmb.listic
        getenv: 'true'
        request_cpus: 2
        request_disk: 1GB
        request_gpus: 0
        request_memory: 2GB
        universe: vanilla

.. note::
   The `getenv` option is used to make sure that the environment variables are forwarded to the job execution server. This allows to use the python environment that is setup on the job submission server on the job execution server.

Then you can run the experiment with the following command:

.. code-block:: console

    qanat run --runner htcondor summary_iris --submit_template two_cpus

If you manage to configure this, you will be able to launch the experiment and have the following output:

.. code-block:: console

   [13:17:55] INFO     Run 4 created.                                                                                                                                                      run.py:1078
              INFO     Setting up the run...                                                                                                                                               run.py:1179
              INFO     Single group of parameters detected                                                                                                                                 runs.py:209
              INFO     Creating /mustfs/MUST-DATA/listic/amian/iris_mnist/results/summary_iris/run_4                                                                                       runs.py:210
              INFO     Running the experiment...                                                                                                                                           run.py:1188
              INFO     Submitting job for command python experiments/summary_statistics/iris.py --storage_path /mustfs/MUST-DATA/listic/amian/iris_mnist/results/summary_iris/run_4        runs.py:806
                        --dataset_path /mustfs/MUST-DATA/listic/amian/iris_mnist/data/iris
              INFO     Jobs submitted to clusters                                                                                                                                          runs.py:829
              INFO       - 4651

You can check that the job has been submitted by running the following command:

.. code-block:: console

    condor_q


    -- Schedd: lappusmb7a.in2p3.fr : <134.158.84.226:9618?... @ 06/29/23 13:18:02
    OWNER     BATCH_NAME        SUBMITTED   DONE   RUN    IDLE  TOTAL JOB_IDS
    ammarmian summary_iris_4   6/29 13:17      _      1      _      1 4651.0

    Total for query: 1 jobs; 0 completed, 0 removed, 0 idle, 1 running, 0 held, 0 suspended
    Total for ammarmian: 1 jobs; 0 completed, 0 removed, 0 idle, 1 running, 0 held, 0 suspended
    Total for all users: 3 jobs; 0 completed, 0 removed, 0 idle, 3 running, 0 held, 0 suspended

You can also check the status of the run with the following command:

.. code-block:: console

    > qanat experiment status summary_iris
    🔖 Name: summary_iris
    💬 Description: Summary statistics on IRIS dataset
    📁 Path: experiments/summary_statistics
    💾 Datasets:['iris']
    ⚙ Executable: experiments/summary_statistics/iris.py
    ⚙ Execute command: python
    ⏳ Number of runs: 3
    🏷  Tags: ['First-order', 'Histograms', 'Correlation', 'Statistics']
    🛠 Actions:
      - plot: Plot summary statistics about the dataset

    ⏳ Runs:
    🆔 ID    💬 Description    📁 Path                       🖥 Runner    📆 Launch date                ⏱ Duration        🔍 Status    🏷  Tags    ⏳ Progress
    4                          results/summary_iris/run_4    htcondor    2023-06-29 13:17:58           0:00:11.333462        ▶
    1                          results/summary_iris/run_1     local      2023-06-29 10:51:06.260540    0:00:00.319506       🏁
    3                          results/summary_iris/run_3    htcondor    2023-06-29 11:35:04           0:00:14              🏁

Once the job is finished, you can check the results in the `results/summary_iris/run_4` directory. You can also check the status explore the run through a prompt with:

.. code-block::

    > qanat experiment run_explore summary_iris 4                                                                                                                                                   ─╯
    Run 4 of experiment summary_iris informations:
      - 🆔 Id: 4
      - 💬 description:
      - 🏷  Tags
      - 🖥 Runner: htcondor
      - 📓 Runner parameters:
            ◾ --submit_template: default
      - 📁 Path: results/summary_iris/run_4
      - 🔍 Status: 🏁
      - 📆 Start time: 2023-06-29 13:17:58
      - 📆 End time: 2023-06-29 13:18:15
      - 📑 Commit: eac4a826bbbfc2700f4dd2f860acd802f62bd5b6


    Run 4 of experiment summary_iris - Explore menu
    > [a] Show output(s)
      [b] Show error(s)
      [c] Show parameters
      [d] Show comment
      [e] Explore run directory
      [f] Show HTCondor log(s)
      [g] Delete run
      [h] Action: plot
    ┌── preview ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
    │ Show output(s) of the run with less                                                                                                                                                             │
    └─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘


.. note::

   You can see that an option has been added to the menu: `Show HTCondor log(s)` which will allow you to see the logs of the job. When more than one job is submitted, you can see the logs of all the jobs for each separate command used.

.. note::

   In this tutorial we simplified with a script that use no parameters but you can specify them after the experiment_name in the `qanat experiment run` command like usual. You can also do groups of parameters and range on options. This is of course the point: being able to run the same experiments over a grid of parameters that are executed over several machines. For more information: See (TODO).


SLURM
-----

SLURM is a job scheduler that is used on many clusters. It is very similar to HTCondor and the configuration is very similar.

TODO
