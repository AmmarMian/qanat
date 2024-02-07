===========================================================================
Running a run at a previous commit of the repository
===========================================================================

Sometimes, it is necessary to run a run at a previous commit of the repository. This can be done by using the `--commit_sha` option. For example, to run the run at commit `a1b2c3d4` of the repository, run the following command:

.. code:: console

   qanat experiment run <experiment_name> --commit_sha a1b2c3d4

The mechanism behind this approach is to clone the repo at the commit `a1b2c3d4` in the `.qanat/cache/a1b2c3d4` folder and run the experiment from there rather than the project root. If the size of git files in the project are large, this can lead to a large cache that you can clean thanks to the command:

.. code:: console

   qanat cache clean
