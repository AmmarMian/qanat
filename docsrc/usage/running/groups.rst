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

TODO

and the corresponding info.yaml:

TODO


From a param_file precising the arguments and their variation
--------------------------------------------------------------

You can use the option :code:`--param_file`:

.. code:: console

   qanat experiment run <experiment_name> --param_file yourfile.yaml [--n_threads NTHREADS] [runner, container, etc options]

.. warning::

   To not confuse with :code:`--parameters_file` which correspond to a single set of parameters that is parsed by your executable.

For more information about this approach see `the page about it <../description_files/run.html>`_.
