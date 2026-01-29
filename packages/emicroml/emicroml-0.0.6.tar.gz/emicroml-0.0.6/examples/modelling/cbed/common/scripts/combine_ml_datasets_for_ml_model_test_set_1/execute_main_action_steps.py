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
r"""A script that is called by various other scripts used for combining multiple
given sets of input machine learning (ML) datasets into multiple larger ML
datasets, intended for testing ML models for a specified task.

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
contains at least one subdirectory located at a path satisfying the pattern
``<data_dir_1>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_datasets_with_<disk_size>_sized_disks``,
where ``<disk_size>`` is any string of letters in the alphabet. For each
subdirectory located at a path satisfying the aforementioned pattern, there must
be at least one HDF5 file storing an input ML dataset, each with a basename of
the form ``ml_dataset_<k>.h5``, where ``<k>`` is any nonnegative integer.

Upon successful completion of the current script, for each subdirectory of
``<data_dir_1>`` satisfying the conditions described in the previous paragraph,
the ML datasets stored therein are combined into a single large ML dataset,
stored in the HDF5 file at the file path
``<data_dir_1>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_dataset_with_<disk_size>_sized_disks.h5``.

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

# For listing files and subdirectories in a given directory, and for renaming
# directories.
import os

# For pattern matching.
import re

# For creating path objects.
import pathlib

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



# Get the paths to ML datasets that are to be combined, specify the filenames of
# the ML datasets that will result from the combinations of ML datasets, and
# combine the ML datasets. After successfully combining the ML datasets, remove
# the directories containing the input ML dataset files.
sample_name = "MoS2_on_amorphous_C"

unformatted_path = (path_to_data_dir_1
                    + "/ml_datasets"
                    + "/ml_datasets_for_ml_model_test_set_1"
                    + "/ml_datasets_with_cbed_patterns_of_{}")
path_to_input_ml_datasets = unformatted_path.format(sample_name)

pattern = "ml_datasets_with_[a-z]*_sized_disks"
partial_path_set_1 = [path_to_input_ml_datasets + "/" + name
                      for name in os.listdir(path_to_input_ml_datasets)
                      if re.fullmatch(pattern, name)]
for partial_path_1 in partial_path_set_1:
    pattern = "ml_dataset_[0-9]*\.h5"
    input_ml_dataset_filenames = [partial_path_1 + "/" + name
                                  for name in os.listdir(partial_path_1)
                                  if re.fullmatch(pattern, name)]

    output_ml_dataset_basename = \
        pathlib.Path(partial_path_1).name.replace("datasets", "dataset")
    output_ml_dataset_filename = \
        path_to_input_ml_datasets + "/" + output_ml_dataset_basename + ".h5"

    kwargs = {"input_ml_dataset_filenames": input_ml_dataset_filenames,
              "output_ml_dataset_filename": output_ml_dataset_filename,
              "rm_input_ml_dataset_files": True,
              "max_num_ml_data_instances_per_file_update": 240}
    ml_model_task_module.combine_ml_dataset_files(**kwargs)

    shutil.rmtree(partial_path_1)
