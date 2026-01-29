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
r"""A script that is called by various other scripts used for combining a given
set of input machine learning (ML) datasets, then splitting the resulting ML
dataset into two output ML datasets: one intended for training ML models for a
specified task, the other for validating such ML models.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --ml_model_task=<ml_model_task> \
         --data_dir_1=<data_dir_1>

where ``<ml_model_task>`` is one of a set of accepted strings that specifies the
ML model task; ``<ml_dataset_idx>`` and ``<data_dir_1>`` is the absolute path to
the top-level data directory containing the input data for this script.

At the moment, the only accepted value of ``<ml_model_task>`` is
``cbed/distortion/estimation``, which specifies that the ML model task is
distortion estimation in CBED.

``<data_dir_1>`` must be the absolute path to an existing directory that
contains the subdirectories ``ml_datasets`` and
``ml_datasets/ml_datasets_for_training_and_validation``, the latter of which
must contain directly the HDF5 files storing the input ML datasets. The basename
of each HDF5 file storing an input ML dataset must be of the form
``ml_dataset_<k>.h5`` where ``<k>`` is any nonnegative integer.

Upon successful completion of the current script, approximately 80 percent of
the input ML data instances are stored in the output ML dataset intended for
training ML models, and the remaining input ML data instances are stored in the
output ML dataset intented for validating ML models. Moreover, upon successful
completion, the files storing the input ML datasets are deleted. The output ML
datasets intended for training and validating the ML models are stored in the
HDF5 files at the file paths
``<data_dir_1>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_for_training.h5``
and
``<data_dir_1>/ml_datasets/ml_datasets_for_training_and_validation/ml_dataset_for_validation.h5``
respectively.

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

# For listing files and subdirectories in a given directory.
import os

# For pattern matching.
import re

# For removing directories.
import shutil



# For combining ML datasets.
import emicroml.modelling.cbed.distortion.estimation



##############################################
## Define classes, functions, and constants ##
##############################################

def parse_and_convert_cmd_line_args():
    accepted_ml_model_tasks = ("cbed/distortion/estimation",)

    current_func_name = "parse_and_convert_cmd_line_args"

    try:
        parser = argparse.ArgumentParser()
        argument_names = ("ml_model_task", "data_dir_1")
        for argument_name in argument_names:
            parser.add_argument("--"+argument_name)
        args = parser.parse_args()
        ml_model_task = args.ml_model_task
        path_to_data_dir_1 = args.data_dir_1

        if ml_model_task not in accepted_ml_model_tasks:
            raise
    except:
        unformatted_err_msg = globals()["_"+current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(accepted_ml_model_tasks[0])
        raise SystemExit(err_msg)

    converted_cmd_line_args = {"ml_model_task": ml_model_task,
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
     "--data_dir_1=<data_dir_1>\n"
     "\n"
     "where ``<ml_model_task>`` must be set to {}; and ``<data_dir_1>`` must "
     "be the absolute path to a valid directory.")



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
converted_cmd_line_args = parse_and_convert_cmd_line_args()
ml_model_task = converted_cmd_line_args["ml_model_task"]
path_to_data_dir_1 = converted_cmd_line_args["path_to_data_dir_1"]



# Select the ``emicroml`` submodule required to generate a ML dataset that is
# appropriate to the specified ML model task.
if ml_model_task == "cbed/distortion/estimation":
    ml_model_task_module = emicroml.modelling.cbed.distortion.estimation



# Get the paths to ML datasets that are to be combined.
pattern = r"ml_dataset_[0-9]*\.h5"
path_to_input_ml_datasets = (path_to_data_dir_1
                             + "/ml_datasets"
                             + "/ml_datasets_for_training_and_validation")
input_ml_dataset_filenames = [path_to_input_ml_datasets + "/" + name
                              for name in os.listdir(path_to_input_ml_datasets)
                              if re.fullmatch(pattern, name)]
input_ml_dataset_filenames.sort()



# Specify the filename of the ML dataset that will result from the combination
# of ML datasets.
output_ml_dataset_filename = (path_to_data_dir_1
                              + "/ml_datasets"
                              + "/ml_dataset_for_training_and_validation.h5")



# Combine the input ML dataset files and then remove the directory containing
# said input ML dataset files.
max_num_ml_data_instances_per_file_update = 23040

kwargs = {"input_ml_dataset_filenames": \
          input_ml_dataset_filenames,
          "output_ml_dataset_filename": \
          output_ml_dataset_filename,
          "rm_input_ml_dataset_files": \
          True,
          "max_num_ml_data_instances_per_file_update": \
          max_num_ml_data_instances_per_file_update}
ml_model_task_module.combine_ml_dataset_files(**kwargs)

shutil.rmtree(path_to_input_ml_datasets)



# Specify the filename of the ML dataset to split.
input_ml_dataset_filename = output_ml_dataset_filename



# Specify the filenames of the ML datasets that will result from the split.
output_ml_dataset_filename_1 = (path_to_data_dir_1
                                + "/ml_datasets/ml_dataset_for_training.h5")
output_ml_dataset_filename_2 = (path_to_data_dir_1
                                + "/ml_datasets/ml_dataset_for_validation.h5")
output_ml_dataset_filename_3 = (path_to_data_dir_1
                                + "/ml_datasets/ml_dataset_for_testing.h5")



# Perform the ML dataset split.
kwargs = {"input_ml_dataset_filename": \
          input_ml_dataset_filename,
          "output_ml_dataset_filename_1": \
          output_ml_dataset_filename_1,
          "output_ml_dataset_filename_2": \
          output_ml_dataset_filename_2,
          "output_ml_dataset_filename_3": \
          output_ml_dataset_filename_3,
          "split_ratio": \
          (80, 20, 0),
          "enable_shuffling": \
          False,
          "rng_seed": \
          1100,
          "rm_input_ml_dataset_file": \
          True,
          "max_num_ml_data_instances_per_file_update": \
          max_num_ml_data_instances_per_file_update}
ml_model_task_module.split_ml_dataset_file(**kwargs)
