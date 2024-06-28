====================================
qanat init
====================================

Command information
----------------------

.. click:: qanat.cli:init
   :prog: qanat init
   :nested: full


Command description
----------------------

The **init** command takes a directory path as argument and creates a new Qanat project in that directory. This means that a `.qanat/` directory will be created with the files:
* `config.yaml`
* `database.db`

The `config.yaml` file contains the default configuration for the project. The `database.db` file is an empty SQLite database that will store the infromation on experiments, datasets, runs and other associated elements.

The **init** command can be used with the `--yes` option to skip the questions and use the default values for the configuration.

The **init** command can be used with the `--help` option to display the help message:

.. code-block:: console

    qanat init --help

    Usage: qanat init [OPTIONS] DIRECTORY

    Initialize experiment directory.

    Options
        DIRECTORY      PATH  (PATH) [required]
         --yes      -y        Answer yes to all questions.
         --help               Show this message and exit
