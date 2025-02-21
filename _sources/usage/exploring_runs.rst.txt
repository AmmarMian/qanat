==================================================
Exploring runs of experiments
==================================================

The :code:`qanat experiment status` command
--------------------------------------------

This commands allows to have a list of the runs that have been done for an experiment. For example:

.. image:: ../_static/usage/experiment_status.png
    :align: center

A flag :code:`--live` can be appended to the command to see a refreshing status of the runs. This is useful when you are running a lot of experiments and want to see the status of the runs.

The :code:`run_explore` command
---------------------------------

.. warning::

   This functionality only work on linux and maxcosx machines since it use :code:`sime-term-menu` that is not available on windows. One workaround is to use WSL2 on windows.

After an experiment has ben executed, possibly many times with different parameters or by improving the code, it is time to explore the results. This is done with the `run_explore` command.  This will lanch a prompt:

.. code:: console

    qanat experiment run_explore <experiment_name>

    Experiment <experiment_name> has XX runs.
    How do you want to explore the runs?

    > Search
      Menu

where :code:`<experiment_name>` is the name of the experiment you want to explore and :code:`XX` should be the number of runs of this experiments. You can then choose to search for a specific run or to explore the runs with a menu by either selecting or searching.

Alternatively you can run the command:

.. code:: console

    qanat experiment run_explore <experiment_name> <run_id>

to directly jump to a run that you want to see.

Exploring runs from the menu
------------------------------

Two options:

* using the search function:

.. code:: console

   Experiment develop_autoencoder has 20 runs.
    Search runs prompt
    > [a] Tag
      [b] Description
      [c] Status
      [d] Runner
      [e] Commit
      [f] Parameters
      [g] Menu with remaining runs
      [h] Reset filters
      [q] Exit

that allows to search over the run information.

* using the menu function:

    .. image:: ../_static/usage/run_explore_menu.png
        :align: center


which allows to select a run and see the information about it.


Exploring a specific run
-------------------------

Once that you have selected a **run_id** for your experiment (either by the menu or by specifying in the command), you have access to the following menu:

.. image:: ../_static/usage/specific_run_menu.png
    :align: center

where you have access to the following options:

* **Show output(s)**: show the standard ouput(s) of the run with the :code:`less` command (see `mean page <https://man7.org/linux/man-pages/man1/less.1.html>`_). If several groups had been executed, you can iterate over all those outputs thanks to the :code:`:n` command in the less.
* **Show error(s)**: show the standard error(s) of the runs with less same as outputs.
* **Show parameters**: show the parameters of the run.
* **Show comment**: show the comment of the run. This is markdown file that is used to keep some information about the run (analysis, contecxt, etc). If it doesn't exist, you will be asked if you want to create it.
* **Explore run directory**: Will show a tree of the run directory. This is useful to see what has been saved during the run.
* **Show HTCondor log(s)**: show the HTCondor log(s) of the run. This is useful when the run has been executed on a cluster with HTCondor. The option is only availabl when the runner is :code:`htcondor`. For Slurm, there is unfortunately no way to see the logs.
* **Delete run**: delete the run from the database and from the disk. This is useful when you want to remove a run that you don't want to keep anymore. This allows delete all the files so be careful.
* **Action: <action_name>**: If some actions have been defined for the experiment, you can run the action from the menu. In the example, an action allowing to launch tensorboard for all the groups had been set up. You can also run the action from the command line with the :code:`qanat experiment action <experiment_name> <action_name> <run_id>` command.
