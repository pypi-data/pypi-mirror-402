.. _examples_modelling_cbed_distortion_estimation_analyzing_ml_model_testing_results_sec:

Analyzing machine learning model testing results
================================================

This page summarizes briefly the contents of the Jupyter notebook at the file
path
``<root>/examples/modelling/cbed/distortion/estimation/notebooks/analyzing_ml_model_testing_results.ipynb``,
where ``<root>`` is the root of the ``emicroml`` repository.

In this notebook, we analyze the output that results from performing the
"actions" described in the following pages:

1. :ref:`examples_modelling_cbed_simulations_MoS2_on_amorphous_C_generate_cbed_pattern_sets_sec`
2. :ref:`examples_modelling_cbed_distortion_estimation_generate_ml_datasets_for_ml_model_test_set_1_sec`
3. :ref:`examples_modelling_cbed_distortion_estimation_combine_ml_datasets_for_ml_model_test_set_1_sec`
4. :ref:`examples_modelling_cbed_distortion_estimation_run_ml_model_test_set_1_sec`
5. :ref:`examples_modelling_cbed_distortion_estimation_run_rgm_test_set_1_sec`

In short, in this notebook we analyze the performance results of the "first" set
of machine learning (ML) model tests for the ML task of estimating distortion in
convergent beam electron diffraction (CBED). These performance results are
benchmarked against those obtained by the radial gradient maximization (RGM)
approach to estimating distortion.

In order to execute the cells in this notebook as intended, a set of Python
libraries need to be installed in the Python environment within which the cells
of the notebook are to be executed. For this particular notebook, users need to
install::

  torch
  pyprismatic>=2.0
  jupyter
  ipympl
  prismatique
  emicroml

Before installing ``emicroml``, it is recommended that users install ``torch``
(i.e. ``PyTorch``) in the same environment that they intend to install
``emicroml`` according to the instructions given `here
<https://pytorch.org/get-started/locally/>`_ for their preferred ``PyTorch``
installation option. The Python library ``pyprismatic>=2.0`` must also be
installed prior to ``emicroml``. The easiest way to install this additional
dependency is within a ``conda`` virtual environment, using the following
command::

  conda install -y pyprismatic=*=gpu* -c conda-forge

if CUDA version >= 11 is available on our machine, otherwise users should run
instead the following command::

  conda install -y pyprismatic=*=cpu* -c conda-forge

After installing ``torch`` and ``pyprismatic``, users can install the remaining
libraries by running the following command in a terminal::

  pip install emicroml prismatique jupyter ipympl

The ``emicroml`` repository contains a script located at
``<root>/default_env_setup_for_slurm_jobs.sh`` that will attempt to create a
virtual environment, then activate it, and then install all the libraries
required to run all of the examples in said repository, when executed with
appropriately chosen command line arguments. As an alternative to the manual
installation procedure above, users can try the automated approach that involves
executing the aforementioned script. See :ref:`this page
<examples_prerequisites_for_execution_without_slurm_sec>` for instructions on
how to do so.

A subset of the output that results from performing the "actions" mentioned at
the beginning of this section is required to execute the cells in this notebook
as intended. One can obtain this subset of output by executing said actions,
however this requires significant computational resources, including significant
walltime. Alternatively, one can copy this subset of output from a Federated
Research Data Repository (FRDR) dataset by following the instructions given on
:ref:`this page
<examples_modelling_cbed_distortion_estimation_copying_subset_of_output_from_frdr_dataset_sec>`.
For this particular notebook, the only directories that one would need to copy
from the FRDR dataset are::

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/distortion/estimation/data/ml_datasets/ml_datasets_for_ml_model_test_set_1

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/distortion/estimation/data/ml_models/ml_model_1/ml_model_test_set_1_results

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/distortion/estimation/data/rgm_test_set_1_results

where ``<frdr_dataset_root>`` is the root of the FRDR dataset, and the only
files that one would need to copy from the FRDR dataset are::

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/simulations/MoS2_on_amorphous_C/data/cbed_pattern_generator_output/patterns_with_small_sized_disks/stem_sim_intensity_output.h5

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/simulations/MoS2_on_amorphous_C/data/cbed_pattern_generator_output/patterns_with_medium_sized_disks/stem_sim_intensity_output.h5

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/simulations/MoS2_on_amorphous_C/data/cbed_pattern_generator_output/patterns_with_large_sized_disks/stem_sim_intensity_output.h5

It is recommended that you consult the documentation of the :mod:`emicroml`
library as you explore the notebook. Moreover, users should execute the cells in
the order that they appear, i.e. from top to bottom, as some cells reference
variables that are set in other cells above them.
