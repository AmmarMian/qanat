=============================================================================
Re-run a previous run of an experiment
=============================================================================

If a run has been cancelled or you want to check if you obtain the same results, Qanat provides an option to run an experiment in the **exact** same condition (runner also) as a previosu one thanks to the comment:

.. code::

   qanat experiment rerun <experiment_name> <run_id>

The run will be executed in the exact same conditions and a tag will show from which previous run it has been reproducted.
