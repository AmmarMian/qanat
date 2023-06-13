========================
Concepts and vocabulary
========================

This page contains the definitions of all the necessary concepts to understand Qanat and its documentation.


Dataset
-------

.. note::

    The term *dataset* is used in Qanat to refer to a collection of data that are used in your experimentations. It is assuemd to be stored on a shared filesystem already mounted and accessible on all executable machines. We define datasets thanks to their name, tags and mostly the path to access the dataset.

    This is used for two reasons:
    * To track datasets used for an experiment and their relative versions
    * To mount those datasets in the containers (see :ref:`container`) used for the experiment


Experiment
----------

.. note::

   The term **experiment** refers to a specific workflow that you want to be tracked in terms of:
   * The datasets used
   * parameters and hyperparameters used
   * The launch time, duration and status of the experiment
   * The logs of the experiment
   * The results of the experiment
   * The version of the code used for the experiment

   An experiment is specified thanks to the `qanat experiment new` command.


Container
---------

.. note::

    The term *container* is used in Qanat to refer to a Singularity (Apptainer)/Docker container that is used to run an experiment. It is assumed that the container is already built and available on the machine where the experiment is run. We define containers thanks to the path to the image.


