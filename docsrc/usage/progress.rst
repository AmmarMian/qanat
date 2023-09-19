=============================================================================
Showing progress of a run in :code:`qanat experiment status`
=============================================================================

You may hae noticed in the output of the :code:`qanat experiment status` command that a column `progress` is present. This is a nice option that allows to know where your experiment is at.

Obviouly, the notion of progress differs from experiments to experiments. For example, in a machine learning experiment, it can be the training progress. In an optimisation problem, it can be the number of iterations.

To be abler to have generalisation, Qanat parse a file **progress.txt** in the :code:`storage_path` results directory that you have to create in your experiment executable.

Two options:

* **TQDM** progressbar: `Tqdm <https://github.com/tqdm/tqdm>`_ is a nice python progress bar library. It gives the option to redirects its output to a file that can be parsed by Qanat. To tell Qanat that this is a TQDM format, you need to write at the first line of the **progress.txt** file: :code:`tqdm` and then redirects the output to the file. For example, by writing:

.. code:: python

    f_tqdm = open(os.path.join(args.storage_path, 'progress.txt'), 'w')
    f_tqdm.write('tqdm\n')
    for epoch in tqdm(range(args.epochs), file=f_tqdm):
        ...

* **count_total** progressbar. This is a more general approach where you write at the top of the file a string of the format: :code:`count_total=NUMBER` where **NUMBER** is the total number of operations to do. Then at each subsequent line, you can write the number of operations done (`1` or more). This is is useful for process that are in parallel and append at the end of the file. Finally, if you write :code:`finished` at the last line, Qanat will skip the computation of the percentage and yield `100%`.

**What happens when there are several groups?**

Qanat will do an average of all the percentages over all the groups.


