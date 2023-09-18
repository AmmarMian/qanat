================================================================
Running through a job system
================================================================

One of Qanat's strength relies on the fact that an experiment can be run locally or through a job system without too much hassle to change between the two options. To do that, Qanat has a concept of a `runner` that is a value equals to either `local`, `htcondor` or `slurm`.
When running an experiment you can use the special option :code:`--runner` to specify hwo to run the experiment. For example:

.. code:: console

    qanat experiment run <experiment_name> --runner local|htcondor|slurm [POSITIONAL ARGUMENTS] [OPTIONS] [--submit_template yourtemplate]

When using either `htcondor` or `slurm`, a job is submitted rather than executing on the local machine.

How to precise the ressources needed by the job ?
-------------------------------------------------

Excellent question! This is done thanks to a submit template that is precised when running the command.

Two options:

* The **submit_template** is a name of a template precised in the `.qanat/config.yaml` file
* The **submit_template** is the path to a YAML file precising the ressources and needed variables.

If none is provided, a default (`default` name in the config file)

To have an idea how to write a template, you can take inspiration from the templates in the `.qanat/config.yaml` file:

.. code:: yaml

   htcondor:
      default:
        +WishedAcctGroup: group_usmb.listic
        getenv: 'true'
        request_cpus: 1
        request_disk: 1GB
        request_gpus: 0
        request_memory: 1GB
        universe: vanilla

    slurm:
      default:
        --cpus-per-task: 1
        --ntasks: 1
        --time: 1-00:00:00

The variaables are the usual that are expected for each job system.

How does it work behind the scene ?
------------------------------------

An **execute.sh** file is produced in the results direcotry. It is an executable where soem commands are written to get back to the working directory, add containers, data binding, etc

Then depending on the job system:

* `htcondor`: a job is submitted thanks to the htcondor python bindings (need to be installed)
* `slurm`: a job is submitted thanks to the `sbatch` command and the ressources are written in the header of the executable in the slurm style.

When fetching the status of a run thanks to :code:`qanat experiment status <experiment_name>`, Qanat takes charge to read the log files and give to the best of its capabilities the status of the run.
A limitation is that you need to run the status command from the machine that launched the job since it is the only one capable of tracking the job. Regardless of the status, you can execute actions from any machine that is mounted on the Qanat project directory.

