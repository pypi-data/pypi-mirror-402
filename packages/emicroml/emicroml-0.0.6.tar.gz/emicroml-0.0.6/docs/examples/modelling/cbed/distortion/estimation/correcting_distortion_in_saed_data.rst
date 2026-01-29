.. _examples_modelling_cbed_distortion_estimation_correcting_distortion_in_saed_data_sec:

Correcting distortion in SAED data
==================================

This page summarizes briefly the contents of the Jupyter notebook at the file
path
``<root>/examples/modelling/cbed/distortion/estimation/notebooks/correcting_distortion_in_saed.ipynb``,
where ``<root>`` is the root of the ``emicroml`` repository.

In this notebook, we show how one can use the machine learning (ML) model that
is trained as a result of executing the "action" described in the page
:ref:`examples_modelling_cbed_distortion_estimation_train_ml_model_set_sec` to
correct distortion in selected area electron diffraction (SAED) data. Strictly
speaking, this ML model is trained to estimate distortion in convergent beam
electron diffraction (CBED) patterns. However, by exploiting the fact that
distortions predominantly come from post-specimen lenses [Hawkes1]_,
e.g. projection lenses, we can estimate and correct distortion in SAED data as
follows:

1. Collect the target experimental SAED data;
2. Modify only pre-specimen lenses to produce CBED data;
3. Use ML model to estimate distortion field in CBED data;
4. Correct distortion in SAED data using distortion field from step 3.

We demonstrate steps 3 and 4 using pre-collected experimental SAED and CBED data
of a calibration sample of single-crystal Au oriented in the [100]
direction. This experimental data was collected on a modified Hitachi SU9000
scanning electron microscope operated at 20 keV.

In order to execute the cells in this notebook as intended, a set of Python
libraries need to be installed in the Python environment within which the cells
of the notebook are to be executed. For this particular notebook, users need to
install::

  torch
  jupyter
  emicroml

Before installing ``emicroml``, it is recommended that users install ``torch``
(i.e. ``PyTorch``) in the same environment that they intend to install
``emicroml`` according to the instructions given `here
<https://pytorch.org/get-started/locally/>`_ for their preferred ``PyTorch``
installation option. After installing ``torch``, users can install the remaining
libraries by running the following command in a terminal::

  pip install emicroml jupyter

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
For this particular notebook, the only file that one would need to copy from the
FRDR dataset is::

  <frdr_dataset_root>/emicroml/examples/modelling/cbed/distortion/estimation/data/ml_models/ml_model_1/ml_model_at_lr_step_<step_count>.pth

where ``<step_count>`` is an integer. 

It is recommended that you consult the documentation of the :mod:`emicroml`
library as you explore the notebook. Moreover, users should execute the cells in
the order that they appear, i.e. from top to bottom, as some cells reference
variables that are set in other cells above them.
