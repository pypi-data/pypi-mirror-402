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
r"""A script that is called by various other scripts used for generating
individual machine learning (ML) datasets that can be used to train and/or
evaluate ML models for a specified task.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --ml_model_task=<ml_model_task> \
         --ml_dataset_idx=<ml_dataset_idx> \
         --data_dir_1=<data_dir_1>

where ``<ml_model_task>`` is one of a set of accepted strings that specifies the
ML model task; ``<ml_dataset_idx>`` is an integer that is used to label the
individual ML dataset to be generated; and ``<data_dir_1>`` is the absolute path
to an existing directory or one to be created, within which the output data is
to be saved.

At the moment, the only accepted value of ``<ml_model_task>`` is
``cbed/distortion/estimation``, which specifies that the ML model task is
distortion estimation in CBED.

``<ml_dataset_idx>`` can be any nonnegative integer, and ``<data_dir_1>`` can be
any valid absolute path to any valid existing directory or one to be created.

The only non-temporary output data generated from this script is a single HDF5
file, which stores the ML dataset. Upon successful execution of the script, the
HDF5 file is saved to
``<data_dir_1>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_<ml_dataset_idx>.h5``.

This script uses the module
:mod:`emicroml.modelling.cbed.distortion.estimation`. It is recommended that you
consult the documentation of said module as you explore the remainder of this
script.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse



# For generating images and targets in ML datasets.
import emicroml.modelling.cbed.distortion.estimation



##############################################
## Define classes, functions, and constants ##
##############################################

def parse_and_convert_cmd_line_args():
    accepted_ml_model_tasks = ("cbed/distortion/estimation",)

    current_func_name = "parse_and_convert_cmd_line_args"

    try:
        parser = argparse.ArgumentParser()
        argument_names = ("ml_model_task", "ml_dataset_idx", "data_dir_1")
        for argument_name in argument_names:
            parser.add_argument("--"+argument_name)
        args = parser.parse_args()
        ml_model_task = args.ml_model_task
        ml_dataset_idx = int(args.ml_dataset_idx)
        path_to_data_dir_1 = args.data_dir_1

        if ((ml_model_task not in accepted_ml_model_tasks)
            or (ml_dataset_idx < 0)):
            raise
    except:
        unformatted_err_msg = globals()["_"+current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(accepted_ml_model_tasks[0])
        raise SystemExit(err_msg)

    converted_cmd_line_args = {"ml_model_task": ml_model_task,
                               "ml_dataset_idx": ml_dataset_idx,
                               "path_to_data_dir_1": path_to_data_dir_1}
    
    return converted_cmd_line_args



###########################
## Define error messages ##
###########################

_parse_and_convert_cmd_line_args_err_msg_1 = \
    ("The correct form of the command is:\n"
     "\n"
     "    python execute_main_action_steps.py "
     "--ml_model_task=<ml_model_task> "
     "--ml_dataset_idx=<ml_dataset_idx> "
     "--data_dir_1=<data_dir_1>\n"
     "\n"
     "where ``<ml_model_task>`` must be set to {}; ``<ml_dataset_idx>`` must "
     "be a nonnegative integer; and ``<data_dir_1>`` must be a valid absolute "
     "path to a valid existing directory or one to be created.")



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
converted_cmd_line_args = parse_and_convert_cmd_line_args()
ml_model_task = converted_cmd_line_args["ml_model_task"]
ml_dataset_idx = converted_cmd_line_args["ml_dataset_idx"]
path_to_data_dir_1 = converted_cmd_line_args["path_to_data_dir_1"]



# Select the ``emicroml`` submodule required to generate a ML dataset that is
# appropriate to the specified ML model task. Also, select the RNG seed
# according to the specified ML dataset index and ML model task.
if ml_model_task == "cbed/distortion/estimation":
    ml_model_task_module = emicroml.modelling.cbed.distortion.estimation

    

# Construct the "fake" CBED pattern generator.
num_pixels_across_each_cbed_pattern = 512
max_num_disks_in_any_cbed_pattern = 90
sampling_grid_dims_in_pixels = 2*(num_pixels_across_each_cbed_pattern,)

kwargs = \
    {"num_pixels_across_each_cbed_pattern": num_pixels_across_each_cbed_pattern,
     "max_num_disks_in_any_cbed_pattern": max_num_disks_in_any_cbed_pattern,
     "rng_seed": ml_dataset_idx + 4000,
     "sampling_grid_dims_in_pixels": sampling_grid_dims_in_pixels,
     "least_squares_alg_params": None,
     "device_name": None}
cbed_pattern_generator = \
    ml_model_task_module.DefaultCBEDPatternGenerator(**kwargs)



# Generate and save the ML dataset.
unformatted_output_filename = (path_to_data_dir_1
                               + "/ml_datasets"
                               + "/ml_datasets_for_training_and_validation"
                               + "/ml_dataset_{}.h5")
output_filename = unformatted_output_filename.format(ml_dataset_idx)

kwargs = \
    {"num_cbed_patterns": 11520,
     "cbed_pattern_generator": cbed_pattern_generator,
     "output_filename": output_filename,
     "max_num_ml_data_instances_per_file_update": 576}
if ml_model_task == "cbed/distortion/estimation":
    kwargs["max_num_disks_in_any_cbed_pattern"] = \
        max_num_disks_in_any_cbed_pattern
    
ml_model_task_module.generate_and_save_ml_dataset(**kwargs)
