===================================================
Running inside a container
===================================================

It is useful to be able to run an experiment inside a containerized environement. This allows to have a separate environment from the Qanat one and possibly have different experiments depending on different environments.

.. note::
   For now, Qanat only takes charge of Singularity/Apptainer conainers. Support for docker will be added later.

To run inside a container, use the :code:`--container` option when running:

.. code::

   qanat experiment run <experiment_name> [POSITIONAL ARGUMENTS] [OPTIONS] --container <container_path.sif> [--gpu True|False]

This will automatically add a prefix to the command(s) executed that will do the following:

* precise that the command(s) should be executed inside the container precised by the path
* bind the current working directory in the container and execute from there seamlessly
* bind all the paths to the datasets that this experiment depends upon to the container


Qanat will also keep a record of the path to the container used.

.. warning::
   The path is purely informational. It is your responsibility to:

    * make sure that the container is accessible on the machine you are running the experiment (local if runner is local, the remote machines in the case of a job system).
    * not move the container or change its path after the experiment has been run. Or at least keep a track of this move by adding a comment to the run for example.

.. note::

   The option :code:`--gpu` is specifically for NVIDIA GPUs usage inside the containers that needs an option when running inside the container.

