.. _examples_modelling_cbed_distortion_estimation_generate_ml_datasets_for_training_and_validation_sec:

Generating machine learning datasets for training and validation
================================================================

In this example, we perform the "action" of generating 55 machine learning (ML)
datasets that can be used to train and/or evaluate ML models for distortion
estimation in convergent beam electron diffraction (CBED) patterns.

NOTE: Users are advised to read the remainder of the current page in its
entirety before trying to execute this action.

To execute the action, first we need to change into the directory
``<root>/examples/modelling/cbed/distortion/estimation/scripts``, where
``<root>`` is the root of the ``emicroml`` repository. Then, we need to run the
Python script ``./execute_action.py`` via the terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` must be equal to
``generate_ml_datasets_for_training_and_validation``, and ``<use_slurm>`` is
either ``yes`` or ``no``. If ``<use_slurm>`` equals ``yes`` and a SLURM workload
manager is available on the server from which you intend to run the script, then
the action will be performed as multiple SLURM jobs. If ``<use_slurm>`` is equal
to ``no``, then the action will be performed locally without using a SLURM
workload manager.

If the action is to be performed locally without using a SLURM workload manager,
then prior to executing the above Python script, a set of Python libraries need
to be installed in the Python environment within which said Python script is to
be executed. See :ref:`this page
<examples_prerequisites_for_execution_without_slurm_sec>` for instructions on
how to do so. If the action is being performed as multiple SLURM jobs, then
prior to executing any Python commands that do not belong to Python's standard
library, a customizable sequence of commands are executed that are expected to
try to either activate an existing Python virtual environment, or create then
activate one, in which the Python libraries needed to complete the action
successfully are installed. See :ref:`this page
<examples_prerequisites_for_execution_with_slurm_sec>` for instructions how to
customize the sequence of commands.

Upon successful completion of the action, for every nonnegative integer ``<k>``
less than 55, the ``<k>`` th ML dataset is stored in the HDF5 file at the file
path
``<root>/examples/modelling/cbed/distortion/estimation/data/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_<k>.h5``.
The file structure of each HDF5 file storing an ML dataset is described in the
documentation for the function
:func:`emicroml.modelling.cbed.distortion.estimation.generate_and_save_ml_dataset`.
Each ML dataset contains 11520 ML data instances, where each ML data instance
stores a :math:`512 \times 512` "fake" CBED pattern containing at most 90 CBED
disks. **Be advised that each file storing an ML dataset is approximately 13.55
GB in size. Hence, in total, the output resulting from the action is
approximately 745 GB of data**.

In executing the action described at the beginning of the current page, multiple
scripts are executed. The particular scripts that are executed depend on the
command line arguments of the parent Python script introduced at the beginning
of this page. If ``<use_slurm>`` equals ``yes``, then the following scripts are
executed in the order that they appear directly below:

:download:`<root>/examples/modelling/cbed/distortion/estimation/scripts/execute_action.py <../../../../../../examples/modelling/cbed/distortion/estimation/scripts/execute_action.py>`
:download:`<root>/examples/modelling/cbed/common/scripts/generate_ml_datasets_for_training_and_validation/execute_all_action_steps.py <../../../../../../examples/modelling/cbed/common/scripts/generate_ml_datasets_for_training_and_validation/execute_all_action_steps.py>`
:download:`<root>/examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/execute_all_action_steps.py <../../../../../../examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/execute_all_action_steps.py>`
:download:`<root>/examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/prepare_and_submit_slurm_job.sh <../../../../../../examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/prepare_and_submit_slurm_job.sh>`
:download:`<root>/examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/execute_main_action_steps.py <../../../../../../examples/modelling/cbed/common/scripts/generate_ml_dataset_for_training_and_validation/execute_main_action_steps.py>`

Otherwise, if ``<use_slurm>`` equals ``no``, then the fourth script, i.e. the
one with the basename ``prepare_and_submit_slurm_job.sh`` is not executed. See
the contents of the scripts listed above for implementation details. The last
script uses the module :mod:`emicroml.modelling.cbed.distortion.estimation`. It
is recommended that you consult the documentation of said module as you explore
said script. Lastly, if the action is being performed as multiple SLURM jobs,
then the default ``sbatch`` options, which are specified in the file with the
basename ``prepare_and_submit_slurm_job.sh``, can be overridden by following the
instructions in :ref:`this page <examples_overriding_sbatch_options_sec>`.
