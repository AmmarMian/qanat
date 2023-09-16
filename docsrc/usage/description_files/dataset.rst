====================================
Dataset description file
====================================

In order to add datasets to the database, you can use the command 'qanat dataset new'. If no arguments is provided, a prompt will be shown asking the informations about your dataset.
Alternatively, you can provide a YAML file containing the description of your dataset: 

.. code-block:: console

    qanat dataset new -f <yaml_file>


The YAML file must contain the following fields:

* **name**: *string*
    The name of the dataset. This name will be used to identify the dataset in the database.

* **description**: *string*
    A short description of the dataset.

* **path**: *string*
    The path to the dataset (from the Qanat projet root). This path must be accessible from the machine running the a Qanat experiment.

* **tags**: *list of strings*
    A list of tags associated to the dataset. Tags are used to filter the datasets in the database.

Example
-------
.. code-block:: yaml

    name: mnist
    description: MNIST dataset
    path: data/mnist
    tags: [mnist, classification, images]