====================================
Experiment description file
====================================

In order to add experiments to the database, you can use the command 'qanat experiment new'. If no arguments is provided, a prompt will be shown asking the informations about your experiment.
Alternatively, you can provide a YAML file containing the description of your experiment. The experiment description file is a YAML file containing the description of an experiment. This file is used to add an experiment to the database. The file must contain the following fields:

.. code-block:: console

    qanat experiment new -f <yaml_file>


The YAML file must contain the following fields:

* **name**: *string*
    The name of the dataset. This name will be used to identify the dataset in the database.

* **description**: *string*
    A short description of the dataset.

* **path**: *string*
    The path to the folder cotnaining the executable (from the Qanat projet root). This path must be accessible from the machine running the a Qanat experiment.

* **executable**: *string*
    The path to the executable file (from the Qanat projet root). This path must be accessible from the machine running the a Qanat experiment.

* **executabe_command**: *string*
    The command to run the executable. This command will be executed from the root of the Qanat project. The command must be a valid command line command.

* **tags**: *list of strings*
    A list of tags associated to the dataset. Tags are used to filter the experiments in the database.

* **datasets**: *list of strings*
    A list of datasets used by the experiment. The datasets must be already present in the database.

* **actions**: *list*
    A list of actions used by the experiment. The actions are provident as follows:

    * **name**: *string*
        The name of the action. This name will be used to identify the action in the database.
    
    * **description**: *string*
        A short description of the action.

    * **executable**: *string*
        The path to the executable file (from the Qanat projet root). This path must be accessible from the machine running the a Qanat experiment.

    * **executabe_command**: *string*
        The command to run the executable. This command will be executed from the root of the Qanat project. The command must be a valid command line command.

Example
-------

From the tutorials:


.. code:: yaml

    name: summary_mnist
    description: Summary statistics on MNIST dataset
    path: experiments/summary_statistics
    executable: experiments/summary_statistics/mnist.py
    executable_command: python
    datasets:
      - mnist
    tags:
      - First-order
      - Histograms
      - Correlation
      - Statistics
    actions:
      - plot:
          name: plot
          executable: experiments/summary_statistics/plot_mnist.py
          executable_command: python
          description: Plot summary statistics about the dataset