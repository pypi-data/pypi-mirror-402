# -*- coding: utf-8 -*-
# Copyright 2025 Matthew Fitzpatrick.
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program. If not, see <https://www.gnu.org/licenses/gpl-3.0.html>.
r"""A script for training and testing machine learning (ML) models for distortion
estimation in convergent beam electron diffraction (CBED). The ML models that
can be used for distortion estimation are described in the documentation for the
class :class:`emicroml.modelling.cbed.distortion.estimation.MLModel`.

This script can be used to perform a variety of actions. To execute an action,
first we need to change into the directory
``<root>/examples/modelling/cbed/distortion/estimation/scripts``, where
``<root>`` is the root of the ``emicroml`` repository. Then, we need to run the
Python script ``./execute_action.py`` via the terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` is one of a set of accepted strings that specifies the action
to be performed, and ``<use_slurm>`` is either ``yes`` or ``no``. If
``<use_slurm>`` equals ``yes`` and a SLURM workload manager is available on the
server from which you intend to run the script, then the action will be
performed as a SLURM job. If ``<use_slurm>`` is equal to ``no``, then the action
will be performed locally without using a SLURM workload manager. ``<action>``
can be equal to ``generate_ml_datasets_for_training_and_validation``,
``combine_ml_datasets_for_training_and_validation_then_split``,
``train_ml_model_set``, ``generate_ml_datasets_for_ml_model_test_set_1``,
``combine_ml_datasets_for_ml_model_test_set_1``, ``run_ml_model_test_set_1``, or
``run_rgm_test_set_1``.  We describe below in more detail each action that can
be performed.

If the action is to be performed locally without using a SLURM workload manager,
then prior to executing the above Python script, a set of Python libraries need
to be installed in the Python environment within which said Python script is to
be executed. See :ref:`this page
<examples_prerequisites_for_execution_without_slurm_sec>` for instructions on
how to do so. If the action is being performed as a SLURM job, then prior to
executing any Python commands that do not belong to Python's standard library, a
customizable sequence of commands are executed that are expected to try to
either activate an existing Python virtual environment, or create then activate
one, in which the Python libraries needed to complete the action successfully
are installed. See :ref:`this page
<examples_prerequisites_for_execution_with_slurm_sec>` for instructions how to
customize the sequence of commands.

If ``<action>`` equals ``generate_ml_datasets_for_training_and_validation``,
then the script will generate 55 ML datasets that can be used to train and/or
evaluate ML models for distortion estimation in CBED patterns. Let
``<top_level_data_dir>`` be
``<root>/examples/modelling/cbed/distortion/estimation/data``, where ``<root>``
be the path to the root of the git repository. For every nonnegative integer
``<k>`` less than 55, the ``<k>`` th ML dataset is stored in the HDF5 file at
the file path
``<top_level_data_dir>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_<k>.h5``.
The file structure of each HDF5 file storing an ML dataset is described in the
documentation for the function
:func:`emicroml.modelling.cbed.distortion.estimation.generate_and_save_ml_dataset`.
Each ML dataset contains 11520 ML data instances, where each ML data instance
stores a :math:`512 \times 512` "fake" CBED pattern containing at most 90 CBED
disks.

If ``<action>`` equals
``combine_ml_datasets_for_training_and_validation_then_split``, then the script
will take as input the 55 ML datasets generated from the previous action,
assuming the previous action had already been executed successfully, combine
said input ML datasets, and then subsequently split the resulting ML dataset
into two output ML datasets: one intended for training ML models, the other for
validating ML models. Upon successful completion of the script, approximately 80
percent of the input ML data instances are stored in the output ML dataset
intended for training ML models, and the remaining input ML data instances are
stored in the output ML dataset intented for validating ML models. Moreover,
upon successful completion, the files storing the input ML datasets are
deleted. The output ML datasets intended for training and validating the ML
models are stored in the HDF5 files at the file paths
``<top_level_data_dir>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_for_training.h5``
and
``<top_level_data_dir>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_for_validation.h5``
respectively.

If ``<action>`` equals ``train_ml_model_set``, then the script will train 10 ML
models using the training and validation ML datasets generated from the previous
action, assuming the previous action had already been executed
successfully. Upon successful completion of the script, for every nonnegative
integer ``<k>`` less than 10, a dictionary representation of ``<k>`` th ML model
after training is saved to a file at the file path
``<top_level_data_dir>/ml_models/ml_model_<k>/ml_model_at_lr_step_<last_lr_step>.pth``,
where ``<last_lr_step>`` is an integer indicating the last learning rate step in
the ML model training procedure. Additionally, for every nonnegative integer
``<k>`` less than 10, the ML model training summary output data file of the
``<k>`` th trained ML model is saved to
``<top_level_data_dir>/ml_models/ml_model_<k>/ml_model_training_summary_output_data.h5"``.

If ``<action>`` equals ``generate_ml_datasets_for_ml_model_test_set_1``, then
the script will generate a set of 3 ML datasets that can be used to test ML
models for distortion estimation in CBED patterns. This action depends on the
output data generated by running the script
``<root>/examples/modelling/cbed/simulation/MoS2_on_amorphous_C/scripts/execute_action.py``
with the command line argument ``--action`` of said script set to
``generate_cbed_pattern_sets``. Hence, one must execute the action
``generate_cbed_pattern_sets`` of the other script before executing the action
``generate_ml_datasets_for_ml_model_test_set_1`` of the current script. Note
that the action ``generate_cbed_pattern_sets`` depends on other actions as
well. See the summary documentation for the script
``<root>/examples/modelling/cbed/simulation/MoS2_on_amorphous_C/scripts/execute_action.py``
for more details on that matter. Upon successful completion of the action
``generate_ml_datasets_for_ml_model_test_set_1`` of the current script, for
every string ``<disk_size>`` in the sequence ``(small, medium, large)``, an ML
dataset is stored in the HDF5 file at the file path
``<top_level_data_dir>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_datasets_with_<disk_size>_sized_disks/ml_dataset_0.h5``,
where the ML dataset contains 2880 ML data instances, with each ML data instance
storing a :math:`512 \times 512` "fake" CBED pattern obtained by randomly
distorting the same undistorted CBED pattern with ``<disk_size>``-sized CBED
disks. For every string ``<disk_size>`` in the sequence ``(small, medium,
large)``, the undistorted CBED pattern with ``<disk_size>``-sized CBED disks is
the final CBED pattern of a CBED experiment simulated via the multislice
technique, where the sample is a 5-layer :math:`\text{MoS}_2` thin film with a
:math:`0.5 \ \text{nm}` thick layer of amorphous carbon (C). By small-, medium-,
and large-sized CBED disks, we mean CBED disks with radii equal roughly to 1/35,
(1/35+1/10)/2, and 1/10 in units of the image width, respectively.

If ``<action>`` equals ``combine_ml_datasets_for_ml_model_test_set_1``, then the
script essentially moves/renames the HDF5 files generated from the previous
action, assuming the previous action had already been executed
successfully. Upon successful completion of the action
``combine_ml_datasets_for_ml_model_test_set_1`` of the current script, for every
string ``<disk_size>`` in the sequence ``(small, medium, large)``, the HDF5 file
at the file path
``<top_level_data_dir>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_datasets_with_<disk_size>_sized_disks/ml_dataset_0.h5``
is moved to
``<top_level_data_dir>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_dataset_with_<disk_size>_sized_disks.h5``.

If ``<action>`` equals ``run_ml_model_test_set_1``, then the script runs the
"first" set of ML model tests of the ML models trained in the action
``train_ml_model_set``, assuming the latter action had already been executed
successfully. The current action also depends on the output data generated by
the action ``combine_ml_datasets_for_ml_model_test_set_1``. Upon successful
completion of the current script, for every string ``<disk_size>`` in the
sequence ``(small, medium, large)``, for every nonnegative integer ``<k>`` less
than 10, the ``<k>`` th trained ML model will have been tested against the ML
testing dataset stored in the HDF5 file at the file path
``<top_level_data_dir>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_dataset_with_<disk_size>_sized_disks.h5``,
with the ML model testing having been performed using the class
:class:`emicroml.modelling.cbed.distortion.estimation.MLModelTester`, with the
output data files having been saved in the directory
``<top_level_data_dir>/ml_models/ml_model_<k>/ml_model_test_set_1_results/results_for_cbed_patterns_of_MoS2_on_amorphous_C_with_<disk_size>_sized_disks``.

If ``<action>`` equals ``run_rgm_test_set_1``, then the script runs the "first"
set of tests of radial gradient maximization (RGM) approach to the distortion
estimation of CBED patterns. The current action depends on the output data
generated by the action ``combine_ml_datasets_for_ml_model_test_set_1``. At this
point, it is worth noting that every ML data instance stored in every valid ML
dataset encodes data about a "fake" CBED pattern. See the documentation for the
class :class:`fakecbed.discretized.CBEDPattern` for a full discussion on fake
CBED patterns and the context relevant to the discussion below. In constructing
a fake CBED pattern, one needs to specify a set of circular, undistorted CBED
disk supports, defined in :math:`\left(u_{x},u_{y}\right)`-space, sharing a
common disk radius, with their centers being specified in
:math:`\left(u_{x},u_{y}\right)` coordinates. One also needs to specify a
distortion field to construct a fake CBED pattern. The supports of the distorted
CBED disks that appear in the fake CBED pattern are obtained by distorting the
aforementioned set of undistorted disk supports according to the aforementioned
distortion field. Let :math:`\left\{
\left(u_{x;c;\text{C};i},u_{y;c;\text{C};i}\right)\right\}_{i}` be the
:math:`\left(u_{x},u_{y}\right)` coordinates of the undistorted disk support
centers, and :math:`\left\{
\left(q_{x;c;\text{C};i},q_{y;c;\text{C};i}\right)\right\}_{i}` be the
corresponding coordinates in :math:`\left(q_{x},q_{y}\right)`-space according to
the distortion field. The RGM approach to estimating the distortion of the fake
CBED pattern can be described as follows:

1. Use the RGM technique, described in Ref. [Mahr1]_ to estimate the subset of
:math:`\left\{ \left(q_{x;c;\text{C};i},q_{y;c;\text{C};i}\right)\right\}_{i}`
corresponding to the distorted CBED disks in the fake CBED pattern that are not
clipped.

2. Determine iteratively via non-linear least squares the distortion field that
minimizes the mean-square error of the estimated coordinates in step 1.

Upon successful completion of the current script, for every string
``<disk_size>`` in the sequence ``(small, medium, large)``, the RGM approach
will have been tested against the ML testing dataset stored in the HDF5 file at
the file path
``<top_level_data_dir>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_dataset_with_<disk_size>_sized_disks.h5``,
with the output having being saved in an HDF5 file generated at the file path
``<top_level_data_dir>/rgm_test_set_1_results/results_for_cbed_patterns_of_MoS2_on_amorphous_C_with_<disk_size>_sized_disks/rgm_testing_summary_output_data.h5``.
Each HDF5 file is guaranteed to contain the following HDF5 objects:

* path_to_ml_testing_dataset: <HDF5 1D dataset>

* total_num_ml_testing_data_instances: <HDF5 0D dataset>

- ml_data_instance_metrics: <HDF5 group>

  - testing: <HDF5 group>

    * epes_of_distortion_fields <HDF5 1D dataset>

      + dim_0: "ml testing data instance idx"

Note that the sub-bullet points listed immediately below a given HDF5 dataset
display the HDF5 attributes associated with said HDF5 dataset. Some HDF5
datasets have attributes with names of the form ``"dim_{}".format(i)`` with
``i`` being an integer. Attribute ``"dim_{}".format(i)`` of a given HDF5 dataset
labels the ``i`` th dimension of the underlying array of the dataset.

The HDF5 dataset at the HDF5 path ``"/path_to_ml_testing_dataset"`` stores the
path, as a string, to the ML testing dataset used for the test.

The HDF5 dataset at the HDF5 path
``"/ml_data_instance_metrics/testing/epes_of_distortion_fields"`` stores the
end-point errors (EPEs) of the "adjusted" standard distortion fields specified
by the predicted standard coordinate transformation parameter sets, during
testing. For every nonnegative integer ``m`` less than the the total number of
ML testing data instances, the ``m`` th element of the aforementioned HDF5
dataset is the EPE of the adjusted standard distortion field specified by the
``m`` th predicted standard standard coordinate transformation set, during
testing. See the summary documentation of the class
:class:`emicroml.modelling.cbed.distortion.estimation.MLModelTrainer` for a
definition of an adjusted standard distortion field, and how the EPE is
calculated exactly.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse

# For creating path objects.
import pathlib

# For getting the path to current script and for executing other scripts.
import os



##############################################
## Define classes, functions, and constants ##
##############################################

def parse_and_convert_cmd_line_args():
    accepted_actions = \
        ("generate_ml_datasets_for_training_and_validation",
         "combine_ml_datasets_for_training_and_validation_then_split",
         "train_ml_model_set",
         "generate_ml_datasets_for_ml_model_test_set_1",
         "combine_ml_datasets_for_ml_model_test_set_1",
         "run_ml_model_test_set_1",
         "run_rgm_test_set_1")

    current_func_name = "parse_and_convert_cmd_line_args"

    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--action", default=accepted_actions[0])
        parser.add_argument("--use_slurm", default="no")
        args = parser.parse_args()
        action = args.action
        use_slurm = args.use_slurm
        
        if (action not in accepted_actions) or (use_slurm not in ("yes", "no")):
            raise
    except:
        num_placeholders = len(accepted_actions)
        unformatted_partial_err_msg = (("``{}``, "*(num_placeholders-1))
                                       + "or ``{}``")
        args = accepted_actions
        partial_err_msg = unformatted_partial_err_msg.format(*args)
        
        unformatted_err_msg = globals()["_"+current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(partial_err_msg)
        raise SystemExit(err_msg)

    converted_cmd_line_args = {"action": action, "use_slurm": use_slurm}
    
    return converted_cmd_line_args



###########################
## Define error messages ##
###########################

_parse_and_convert_cmd_line_args_err_msg_1 = \
    ("The correct form of the command is:\n"
     "\n"
     "    python execute_action.py "
     "--action=<action> --use_slurm=<use_slurm>\n"
     "\n"
     "where ``<action>`` can be {}; and ``<use_slurm>`` can be either ``yes`` "
     "or ``no``.")



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
converted_cmd_line_args = parse_and_convert_cmd_line_args()
action = converted_cmd_line_args["action"]
use_slurm = converted_cmd_line_args["use_slurm"]



# Get the path to the current script.
path_to_current_script = pathlib.Path(os.path.realpath(__file__))
path_to_calling_script_of_script_to_execute = str(path_to_current_script)



if action == "run_rgm_test_set_1":
    # Get the path to the script that executes the remainder of the action. This
    # path is equal to
    # ``<path_to_directory_containing_current_script>/run_rgm_test_set_1/execute_all_action_steps.py``,
    # where ``<path_to_directory_containing_current_script>`` is the path to the
    # directory containing directly the current script.
    path_to_script_to_execute = (str(path_to_current_script.parents[0])
                                 + "/run_rgm_test_set_1"
                                 + "/execute_all_action_steps.py")
else:
    # Get the path to the script that executes the remainder of the action. This
    # path is equal to
    # ``<path_to_directory_containing_current_script>/../../../common/scripts/execute_action.py``,
    # where ``<path_to_directory_containing_current_script>`` is the path to the
    # directory containing directly the current script.
    path_to_script_to_execute = (str(path_to_current_script.parents[3])
                                 + "/common/scripts/execute_action.py")


# Execute the script at ``path_to_script_to_execute``.
unformatted_cmd_str = ("python {} "
                       "--calling_script={} "
                       "--action={} "
                       "--use_slurm={}")
args = (path_to_script_to_execute,
        path_to_calling_script_of_script_to_execute,
        action,
        use_slurm)
cmd_str = unformatted_cmd_str.format(*args)
os.system(cmd_str)
