.. _examples_modelling_cbed_distortion_estimation_copying_subset_of_output_from_frdr_dataset_sec:

Copying data from online repository dataset related to distortion estimation of CBED patterns
=============================================================================================

In order to execute the cells in the Jupyter notebooks in the directory at the
path ``<emicroml_root>/examples/modelling/cbed/distortion/estimation/notebooks``
--- where ``<emicroml_root>`` is the root of the ``emicroml`` repository --- a
subset of the output that results from performing a set of "actions" are
required. Descriptions of these actions can be found through :ref:`this page
<examples_modelling_cbed_distortion_estimation_sec>`. One can obtain this subset
of output by executing said actions, however this requires significant
computational resources, including significant walltime. Alternatively, one can
copy this subset of output from the Federated Research Data Repository (FRDR)
dataset found `here <https://doi.org/10.20383/103.01569>`_. Below we describe
how one should copy the data from this FRDR dataset.

First, download a copy of the FRDR dataset to the machine on which you intend to
launch the Jupyter notebooks; Secondly, for every file in every subdirectory of
the directory at the path ``<frdr_dataset_root>/emicroml`` --- where
``<frdr_dataset_root>`` is the root of the local copy of the FRDR dataset ---
copy said file to ``<emicroml_root>/<relative_path_to_file_in_frdr_dataset>``
--- where ``<relative_path_to_file_in_frdr_dataset>`` is the path to said file
relative to ``<frdr_dataset_root>/emicroml`` --- and create any new directories
as required. For example, the file at the path
``<frdr_dataset_root>/emicroml/examples/modelling/cbed/simulations/MoS2/data/atomic_coords.xyz``
should be copied to
``<emicroml_root>/examples/modelling/cbed/simulations/MoS2/data/atomic_coords.xyz``.
