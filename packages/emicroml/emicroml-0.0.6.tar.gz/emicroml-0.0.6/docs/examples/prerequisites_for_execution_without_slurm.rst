.. _examples_prerequisites_for_execution_without_slurm_sec:

Prerequisites for running example scripts or Jupyter notebooks without using a SLURM workload manager
=====================================================================================================

Prior to running any scripts or Jupyter notebooks in the directory
``<root>/examples`` without using a SLURM workload manager, where ``<root>`` is
the root of the ``emicroml`` repository, a set of Python libraries need to be
installed in the Python environment within which any such scripts or Jupyter
notebooks are to be executed.

The Python libraries that need to be installed in said Python environment are::

  torch
  pyprismatic>=2.0
  jupyter
  ipypml
  pyopencl
  pocl-binary-distribution>=1.2
  prismatique
  emicroml

Installing the above set of Python libraries will enable you to run any script
or Jupyter notebook in the directory ``<root>/example``, though a given script
or Jupyter notebook will not necessarily require all of the Python libraries
listed above. Note that the last 6 Python libraries listed above can be
installed via ``pip`` by running the following command::

  pip install emicroml[examples]

however one should installed ``torch``, then ``pyprismatic``,
beforehand. Continue reading the remainder of this page for details.

With appropriately chosen command line arguments, the script
:download:`<root>/default_env_setup_for_slurm_jobs.sh
<../../default_env_setup_for_slurm_jobs.sh>` will attempt to create a virtual
environment, then activate it, and then install the first list of Python
libraries above. If the script is executed on a Digital Alliance of Canada
(DRAC) high-performance computing (HPC) server, then the virtual environment is
created via ``virtualenv``. Otherwise, the virtual environment is created via
``conda``. For the latter scenario, an ``anaconda`` or ``miniconda``
distribution must be installed prior to running the script.

The correct form of the command to run the script is::

  source <path_to_current_script> <env_name> <install_extras>

where ``<path_to_current_script>`` is the absolute or relative path to the
script :download:`<root>/default_env_setup_for_slurm_jobs.sh
<../../default_env_setup_for_slurm_jobs.sh>`; ``<env_name>`` is the path to the
virtual environment, if the script is being executed on a DRAC HPC server, else
it is the name of the ``conda`` virtual environment; and ``<install_extras>`` is
a boolean, i.e. it should either be ``true`` or ``false``. If
``<install_extras>`` is set to ``true``, then the script will attempt to install
within the environment the dependencies required to run all of the examples in
the repository, in addition to installing ``emicroml``. Otherwise, the script
will attempt to install only ``emicroml`` and its dependencies, i.e. not the
additional libraries required to run the examples.

If for whatever reason the script
:download:`<root>/default_env_setup_for_slurm_jobs.sh
<../../default_env_setup_for_slurm_jobs.sh>` fails to create and the activate
successfully a virtual environment equipped with the Python libraries listed
above, then one will need to do so manually according to the constraints imposed
by the machine or server on which you intend to run examples. Before installing
``emicroml[examples]``, it is recommended that users install ``torch`` in the
same environment that they intend to install ``emicroml[examples]`` according to
the instructions given `here <https://pytorch.org/get-started/locally/>`_ for
their preferred PyTorch installation option. The Python library
``pyprismatic>=2.0`` must also be installed prior to ``emicroml[examples]``. The
easiest way to install this additional dependency is within a ``conda`` virtual
environment, using the following command::

  conda install -y pyprismatic=*=gpu* -c conda-forge

if CUDA version >= 11 is available on your machine, otherwise users should run
instead the following command::

  conda install -y pyprismatic=*=cpu* -c conda-forge

The most straightforward way to install the remaining libraries is via ``pip``::

  pip install emicroml[examples]
