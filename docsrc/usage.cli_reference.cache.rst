====================================
qanat cache
====================================

Command information
----------------------

.. click:: qanat.cli:cache_main
   :prog: qanat
   :nested: full


Command description
----------------------

This command is used to manage the cache of the application. It can be used to clear the cache, or to display the content of the cache.

.. note::

   The cache corresponds to the versions of the code at previous commits that are created when executing an experiment with a specific commit sha. It is then sometimes necessary to clean the cache if its size is too voluminous.

.. code-block:: console

    qanat cache --help

    Usage: qanat cache [OPTIONS] COMMAND [ARGS]...

      Manage the cache of the application.

    Commands:
      clear   Clear the cache.
      show    Display the content of the cache.

    Options:

        --help  Show this message and exit.


