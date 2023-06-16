=====
Usage
=====

Qanat is meant to be used as a command-line tool. The main entry point is the qanat command which takes an argument specifying the action to be performed. The following actions are supported:

* **qanat init:** - creates a new qanat project in the specified directory
* **qanat dataset:** - dataset level operations
* **qanat experiment:** - experiment level operations
* **qanat status:** - prints the status of the current qanat project
* **qanat config:** - operations config of qanat project
* **qanat cache:** - operations on cache of qanat project

Assumptions
=================
Qanat assumes a few thing in the way you organise your workflow and your experiments:

* You want to work from the terminal mostly.
* You are comfortable with the command-line and shell scripting.
* You are able to split your experiment workflow into 3 steps:

    * **executable preparation:** A script responsible for the execution of the experiment (must handle pre-processing, execution and post-processing tasks)
    * **runner choice:** A way to run the executable on a machine (local, htcondor, slurm:todo)
    * **analysis:** One or several scripts that analyse the results of the experiment and produce a summary of the results.

* You give Qanat the reponsibility for launching the experiments and analysing the results according to your runner choice. The results are storted in a directory created by Qanat.
* You have access to your datasets via a shared filesystem that is accessible from all the machines you want to run your experiments on. (Later will be added option to mount on the fly).
* The experiments are specified by executables which accept command-line arguments and produce output files that will be later analysed thanks to other scripts.
* You are able to specify the parameters of your experiments in a configuration file or through command-line arguments.

Concepts and Vocabulary
=======================

Qanat is based on a few concepts that are important to understand in order to use it efficiently. See the glossar for a list of terms and their definitions:

.. toctree::
    :maxdepth: 2

    vocabulary


CLI reference
=============
.. toctree::
    :maxdepth: 2

    cli_reference/index
