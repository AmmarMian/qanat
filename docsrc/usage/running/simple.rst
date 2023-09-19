======================================================================
Running a simple experiment with command-line arguments
======================================================================

Supposing that your experiment **experiment_name** is set and accepts commmand-line arguments. Running the experiment while keeping track of the parameters and redirecting output/errors to an automatically created directory can be done by running:

.. code-block::

   qanat experiment run <experiment_name> <experiment_args> [--description "Some description"] [--tag tag1 --tag tag2 ..] [--storage_path somepath]


where:

* **--description** is an optional description of the experiment
* **--tag** is an optional tag for the experiment. Several tags can be specified.
* **--storage_path** is an optional path to the directory where the experiment data will be stored. If not specified, the experiment data will be stored in the default results directory of the Qanat project.

This will create **info.yaml**, **stdout.txt**, **stderr.txt** files in the dedicated directory for this experiment run.

* **info.yaml** contains the parameters of the experiment, the description and the tags.
* **stdout.txt** contains the standard output of the experiment.
* **stderr.txt** contains the standard error of the experiment.

Additionally, depending on your configuration, experiment result files should be stored there.

.. note::

    Reminder: It is your responsibily when creating the executable for the experiment to parse the option :code:`--storage_path` and store the files there.


The run will block the terminal until the executable is done so do not quit if you want the experiment to run until its end.
