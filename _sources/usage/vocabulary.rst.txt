========================
Concepts and vocabulary
========================

This page contains the definitions of all the necessary concepts to understand Qanat and its documentation.


.. _dataset:

Dataset
-------

The term **dataset** is used in Qanat to refer to a collection of data that are used in your experimentations. It is assuemd to be stored on a shared filesystem already mounted and accessible on all executable machines. We define datasets thanks to their name, tags and mostly the path to access the dataset.

This is used for two reasons:

* To track datasets used for an experiment and their relative versions
* To mount those datasets in the containers (see :ref:`container`) used for the experiment


.. _experiment:

Experiment
----------

The term **experiment** refers to a specific workflow that you want to be tracked in terms of:

* The datasets used
* The parameters and hyperparameters used
* The launch time, duration and status of the experiment
* The logs of the experiment
* The results of the experiment
* The version of the code used for the experiment

An experiment is specified thanks to the `qanat experiment new` command.


.. _run:

Run
----

The term **run** refers to a specific execution of an experiment. It is used to track the different executions of an experiment with different parameters and hyperparameters. It is also linked to the specific commit of the repo at which the experiment was executed so it makes it able to track evolution of the code relative to an experiment (i.e keeps failed attempts as illustration).

.. _action:

Action
------

The term **action** corresponds to an action that can be performed to a run of an experiment. More specifically, it is a script that takes the directory of the stored results and perform a specific action such as plotting, exporting data, following progress of the experiment or even a full dashboard relative to the experiment.


.. _comment:

Comment
-------

The term **comment** refers to a comment that can be added to a run of an experiment. It is used to add a comment to a specific run of an experiment. It can be used to add a comment to a run that failed to explain why it failed or to add a comment to a run that succeeded to explain why it succeeded. It is always a markdown file.

.. _document:

Document
---------

The term **document** refers to a document that is relevant to the project such as a paper, report, website. It can be linked to experiments, dependency style, with a specific set run options that are expected to produce some output. If any expected output from a dependency is not existing, the experiment will be run with the saved options and then the document will be compiled.


.. _runner:

Runner
-------

The ter **runner** refers to a specific way to execute your experiment run script. Either on the machine launching the execution (runner = 'local') or through a job scheduling system (runner = 'htcondor' or runner = 'slurm'). It is associated with parameters. See (todo) for more details on parameters for specific runners.

.. _container:

Container
---------

The term *container* is used in Qanat to refer to a Singularity (Apptainer)/Docker container that is used to run an experiment. For singularity (apptainer), it is assumed that the container is already built and available on the machine where the experiment is run. For docker, we construct the container from a Dockerfile. We define containers thanks to the path to the image.

.. warning::
    Docker is not implemented yet.
