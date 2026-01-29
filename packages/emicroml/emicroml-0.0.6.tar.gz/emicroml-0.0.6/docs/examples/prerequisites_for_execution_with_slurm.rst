.. _examples_prerequisites_for_execution_with_slurm_sec:

Prerequisites for running example scripts or Jupyter notebooks using a SLURM workload manager
=============================================================================================

There are numerous Python scripts sharing the basename ``execute_action.py``,
located in different subdirectories of ``<root>/examples``, where ``<root>`` is
the root of the ``emicroml`` repository. Each one of these Python scripts can be
executed to perform one or more "actions". To execute a particular action of a
particular script, one must first change into the directory containing said
script. Then, we need to run the Python script ``./execute_action.py`` via the
terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` is the string associated with the action of interest, and
``<use_slurm>`` is either ``yes`` or ``no``. If ``<use_slurm>`` equals ``yes``
and a SLURM workload manager is available on the server from which you intend to
run the script, then the action will be performed as one or more SLURM jobs. If
``<use_slurm>`` is equal to ``no``, then the action will be performed locally
without using a SLURM workload manager.

For instance, let us assume that we can perform actions as SLURM jobs. If we
were to change into the directory
``<root>/examples/modelling/cbed/simulations/MoS2/scripts``, and then execute
the following terminal command::

  python execute_action.py --action=generate_atomic_coords --use_slurm=yes

then the action of generating the atomic coordinates of a model of a 5-layer
:math:`\text{MoS}_2` thin film will be performed as a SLURM job.

In general, if an action is being performed as one or more SLURM jobs, then
prior to executing any Python commands that do not belong to Python's standard
library, a customizable sequence of commands are executed that are expected to
try to either activate an existing Python virtual environment, or create then
activate one, in which the Python libraries needed to complete the action
successfully are installed. Let us refer to this customizable sequence of
commands as the environment setup procedure. The Python libraries that need to
be installed in said Python virtual environment are::

  torch
  pyprismatic>=2.0
  jupyter
  ipypml
  pyopencl
  pocl-binary-distribution>=1.2
  prismatique
  emicroml

The environment setup procedure starts by looking for a file located at the file
path ``<root>/custom_env_setup_for_slurm_jobs.sh``. If a file exists at that
location, then the environment setup procedure will attempt to execute the file
via the following terminal command::

  source <root>/custom_env_setup_for_slurm_jobs.sh ${SLURM_TMPDIR}/tempenv true

If a file does not exist at that location, then the environment setup procedure
will execute the following terminal command instead::

  source <root>/default_env_setup_for_slurm_jobs.sh ${SLURM_TMPDIR}/tempenv true

The script :download:`<root>/default_env_setup_for_slurm_jobs.sh
<../../default_env_setup_for_slurm_jobs.sh>` will attempt to create a virtual
environment, then activate it, and then install the above Python libraries. If
the script is executed on a Digital Alliance of Canada (DRAC) high-performance
computing (HPC) server, then the virtual environment is created via
``virtualenv``. Otherwise, the virtual environment is created via ``conda``. For
the latter scenario, an ``anaconda`` or ``miniconda`` distribution must be
installed prior to running the script. The correct generic form of the previous
terminal command is::

  source <root>/default_env_setup_for_slurm_jobs.sh <env_name> <install_extras>

where ``<env_name>`` is the path to the virtual environment, if the script is
being executed on a DRAC HPC server, else it is the name of the ``conda``
virtual environment; and ``<install_extras>`` is a boolean, i.e. it should
either be ``true`` or ``false``. If ``<install_extras>`` is set to ``true``,
then the script will attempt to install within the environment the dependencies
required to run all of the examples in the repository, in addition to installing
``emicroml``. Otherwise, the script will attempt to install only ``emicroml``
and its dependencies, i.e. not the additional libraries required to run the
examples.

If, via the script at the file path
``<root>/default_env_setup_for_slurm_jobs.sh``, the virtual environment is to be
created on a HPC server belonging to DRAC, and the script at the file path
``<root>/download_wheels_for_offline_env_setup_on_drac_server.sh`` has never
been executed, then one must first change into the root of the repository, and
subsequently execute that script via the following command::

  bash download_wheels_for_offline_env_setup_on_drac_server.sh

Upon completion of that script, a set of Python wheels will be downloaded to the
directory ``<root>/_wheels_for_offline_env_setup_on_drac_server``, where
``<root>`` is the root of the repository. Note that that script only needs to be
executed once, assuming one does not modify or delete the directory
``<root>/_wheels_for_offline_env_setup_on_drac_server``.

If for whatever reason the script
:download:`<root>/default_env_setup_for_slurm_jobs.sh
<../../default_env_setup_for_slurm_jobs.sh>` fails, then you will need to write
your own shell script according to the constraints imposed by the machine or
server on which you intend to run examples, and then save this script to the
file path ``<root>/custom_env_setup_for_slurm_jobs.sh``. 
