===============================================
Running with a file containing parameters
===============================================

.. warning::

   The keyword :code:`--parameters_file` is not to be confused with :code:`--param_file` which is used to specify command-line arguments that can possibily vary.
   Yes, I know it can be confusing and it may be changed later (due to lazyness from the author at this point in time).

Sometimes command-line arguments are not handy to set-up your simulation and you'd rather use a parameters file where you store all the relevant variables, definitions and so on. You still want to keep track of this file as for the command-line arguments case.
To handle this, Qanat has a special option: :code:`--parameters_file`. If you use this option when running and experiment, Qanat will copy this file into the :code:`storage_path` directory when running the experiment. For example:

.. code-block:: console

   qanat experiment run <experiment_name> --parameters_file <yourfile> [OPTIONS]

where **OPTIONS** are the usual options to describe the runs, runner, container, etc.

.. warning::

   The file could be anything (YAML, JSON or even another python file) but your executing script should parse it using exactly the option :code:`--parameters_file`.


When using the :code:`qanat experiment run_explore <experiment_name> <run_id>` command, an option is then added to visualize the parameters file's content.

.. warning::

   Obviously, do not modify this copied file in the results directory. You would discard any reproducibility.


