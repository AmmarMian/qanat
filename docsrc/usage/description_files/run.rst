====================================
Run launching description file
====================================

.. error::
    There is a bug in the parsing of the varying groups that makes the parsing of the positional arguments independent of the options so you end up with a cartesian product of the positional arguments and the options.
    This is not the intended behaviour and will be fixed.

When launching an experiment, it is often necessary to specify a number of parameters. Moreover, when launching an experiment with varying parameters, descibing the different groups or range in a single line can lead to errors.
To solve this, Qanat accept a YAML file that describes the different parameters to use. This file is then used to generate the different commands to launch the experiments thanks to the command:

.. code-block:: console

    qanat experiment run (runner) --param_file <file> (runner, contianer, description, tags)

.. warning::
    The parameters in the file are not checked against the parameters of the experiment. It is the user's responsibility to ensure that the parameters are correct.

.. warning::
    The parameters' file only precise the parameters fed into the experiment executable. All other parameters must be specified in the command line.

The file is a YAML file with the following structure:

.. code-block:: yaml

    fixed_args:
        positional:
            <weight1>: <value>
            <weight2>: <value>
            ...
        options:
            <option1>: <value>
            <option2>: <value>
            ...
    varying_args:
        range:
            options:
                <option1>: <range>
                <option2>: <range>
                ...

        groups:
            - options: # Group 1
                <option1>: <value>
                <option2>: <value>
                ...
              positional:
                <weight1>: <value>
                <weight2>: <value>
                ...
            - options: # Group 2
                <option1>: <value>
                <option2>: <value>
                ...
              positional:
                <weight1>: <value>
                <weight2>: <value>
                ...
            ...

where there are two parts:

* **fixed_args**: the parameters that are always the same for all executions.

    * **positional**: the positional arguments of the experiment. The keys are the weights (relative position in the construction of the final command) of the arguments and the values are the values of the arguments.
    
    * **options**: the options of the experiment. The keys are the names of the options and the values are the values of the options.     

* **varying_args**: the parameters that vary over the executions.

    * **range**: the parameters that vary over a range of values **(only works for options)**. The keys are the names of the options and the values are the ranges of the options. The ranges are defined as a list of values or a dictionary with the keys ``start``, ``stop`` and ``step``.
    
    .. warning::

        The type of the yielded values are float, so you will have to cast them if you want to use them as integers.

    * **groups**: the parameters that vary over a set of values. A list is constructed with two keywords for each element:

        * **options**: the options of the experiment. The keys are the names of the options and the values are the values of the options.

        * **positional**: the positional arguments of the experiment. The keys are the weights (relative position in the construction of the final command) of the arguments and the values are the values of the arguments.


    The constructed commands are the cartesian product of the different groups and the range of the options.

In order to have an idea of the structure of the file, here is an example:

.. code-block:: yaml

    fixed_args:
        options:
            '--mean': '10, -50'
            

    varying_args:
        range:
            options:
            '--n_samples': [5, 201, 100]

        groups:
            - options:
                '--cov': '1, 0.8, 0.8, 1'
              positional:
                0: 10

            - options:
                '--cov': '1, 0.4, 0.4, 1'
              positional:
                0: 10
                1: 500
      
      
To see the parameters that have been parsed, you can use the flag ``--dry_run`` which will print the different commands that will be executed without actually executing them.

.. code-block:: console

    qanat experiment run --param_file <file> --dry_run

For the previous example, the output would be:

.. error::
    Reminder: There is a bug in the parsing of the varying groups that makes the parsing of the positional arguments independent of the options so you end up with a cartesian product of the positional arguments and the options.
    This is not the intended behaviour and will be fixed.

.. code-block:: console

    INFO     Dry run: Showing parsed parameters without running the experiment.                                            run.py:1051
    INFO     Parsed parameters:                                                                                            run.py:1058
             - Group 0:
                ◼ pos_0: 10
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.8, 0.8, 1
                ◼ --n_samples: 5.0
            - Group 1:
                ◼ pos_0: 10
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.4, 0.4, 1
                ◼ --n_samples: 5.0
            - Group 2:
                ◼ pos_0: 10
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.8, 0.8, 1
                ◼ --n_samples: 105.0
            - Group 3:
                ◼ pos_0: 10
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.4, 0.4, 1
                ◼ --n_samples: 105.0
            - Group 4:
                ◼ pos_0: 10
                ◼ pos_1: 500
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.8, 0.8, 1
                ◼ --n_samples: 5.0
            - Group 5:
                ◼ pos_0: 10
                ◼ pos_1: 500
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.4, 0.4, 1
                ◼ --n_samples: 5.0
            - Group 6:
                ◼ pos_0: 10
                ◼ pos_1: 500
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.8, 0.8, 1
                ◼ --n_samples: 105.0
            - Group 7:
                ◼ pos_0: 10
                ◼ pos_1: 500
                ◼ --mean: 10, -50
                ◼ --cov: 1, 0.4, 0.4, 1
                ◼ --n_samples: 105.0