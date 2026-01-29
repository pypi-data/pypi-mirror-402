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
r"""A script that is called by various other scripts used for running the 
"first" set of machine learning (ML) model tests for a specified task.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --ml_model_task=<ml_model_task> \
         --data_dir_1=<data_dir_1>

where ``<ml_model_task>`` is one of a set of accepted strings that specifies the
ML model task; and ``<data_dir_1>`` is the absolute path to the top-level data
directory containing the input data for this script.

At the moment, the only accepted value of ``<ml_model_task>`` is
``cbed/distortion/estimation``, which specifies that the ML model task is
distortion estimation in CBED.

``<data_dir_1>`` must be the absolute path to an existing directory that
contains the subdirectories located at the paths
``<data_dir_1>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C``
and ``<data_dir_1>/ml_models``. Let ``<path_to_ml_testing_datasets>`` be the
former subdirectory path. The directory at ``<path_to_ml_testing_datasets>``
must contain at least one HDF5 file that stores a ML testing dataset with the
basename of the form ``ml_dataset_with_<disk_size>_sized_disks.h5``, where
``<disk_size>`` is any string of letters in the alphabet. Note that
``<disk_size>`` serves as a unique identifier of the ML testing datasets that
are considered for the current action.

The directory at ``<data_dir_1>/ml_models`` must contain at least one
subdirectory with the basename of the form ``ml_model_<k>``, where ``<k>`` is
any nonnegative integer. For each one of these directories in
``<data_dir_1>/ml_models``, there must be a dictionary representation of a ML
model that can be used for the ML model task specified by ``<ml_model_task>``,
that has a basename of the form ``ml_model_at_lr_step_<n>.pth``, where ``<n>``
is any nonnegative integer. If more than one dictionary representation exists in
the same directory, then only the dictionary representation with the largest
nonnegative integer ``<n>`` is considered, denoted here by ``<m>``, the rest are
ignored. Much like ``<disk_size>`` serves as a unique identifier of ML testing
datasets, the pair ``(<k>, <m>)`` serves as a unique identifier of the ML models
to be tested for the current action.

Upon successful completion of the current script, for each ML model and ML
testing dataset considered for testing, said ML model will have been tested
against said ML testing dataset using the class
:class:`emicroml.modelling.cbed.distortion.estimation.MLModelTester`, with the
output data files having been saved in the directory
``<data_dir_1>/ml_models/ml_model_<k>/ml_model_test_set_1_results/results_for_cbed_patterns_of_MoS2_on_amorphous_C_with_<disk_size>_sized_disks``.
See the summary documentation for the method
:meth:`emicroml.modelling.cbed.distortion.estimation.MLModelTester.test_ml_model`
for a discussion on the output files resulting from ML model testing.

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

# For setting Python's seed.
import random



# For avoiding errors related to the ``mkl-service`` package. Note that
# ``numpy`` needs to be imported before ``torch``.
import numpy as np

# For setting the seed to the random-number-generator used in ``pytorch``.
import torch



# For testing ML models.
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



# Set a RNG seed for reproducibility.
rng_seed = 555444

torch.manual_seed(seed=rng_seed)
torch.cuda.manual_seed_all(seed=rng_seed)
random.seed(a=rng_seed)
np.random.seed(seed=rng_seed)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False



# Specify by name the device to use for PyTorch operations.
device_name = None



# Search for ML models.
path_to_ml_models = path_to_data_dir_1 + "/ml_models"
pattern = "ml_model_[0-9]*"
ml_model_idx_set = tuple(int(name.split("_")[-1])
                         for name in os.listdir(path_to_ml_models)
                         if re.fullmatch(pattern, name))



# Search for ML datasets for testing.
sample_name = "MoS2_on_amorphous_C"

unformatted_path = (path_to_data_dir_1
                    + "/ml_datasets"
                    + "/ml_datasets_for_ml_model_test_set_1"
                    + "/ml_datasets_with_cbed_patterns_of_{}")
path_to_ml_datasets = unformatted_path.format(sample_name)

pattern = "ml_dataset_with_[a-z]*_sized_disks\.h5"
disk_sizes = tuple(name.split("_")[-3]
                   for name in os.listdir(path_to_ml_datasets)
                   if re.fullmatch(pattern, name))



for disk_size in disk_sizes:
    # Load ML dataset.
    unformatted_path = (path_to_data_dir_1
                        + "/ml_datasets"
                        + "/ml_datasets_for_ml_model_test_set_1"
                        + "/ml_datasets_with_cbed_patterns_of_{}"
                        + "/ml_dataset_with_{}_sized_disks.h5")
    path_to_ml_dataset = unformatted_path.format(sample_name, disk_size)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": True,
              "max_num_ml_data_instances_per_chunk": 32}
    ml_testing_dataset = ml_model_task_module.MLDataset(**kwargs)

    kwargs = {"ml_training_dataset": None,
              "ml_validation_dataset": None,
              "ml_testing_dataset": ml_testing_dataset,
              "mini_batch_size": 64,
              "rng_seed": rng_seed}
    ml_dataset_manager = ml_model_task_module.MLDatasetManager(**kwargs)


    
    for ml_model_idx in ml_model_idx_set:
        # Load ML model to test.
        architecture = "distoptica_net"

        unformatted_path = \
            (path_to_data_dir_1
             + "/ml_models/ml_model_{}")
        path_to_ml_model_state_dicts = \
            unformatted_path.format(ml_model_idx)
        pattern = \
            "ml_model_at_lr_step_[0-9]*\.pth"
        largest_lr_step_idx = \
            max([name.split("_")[-1].split(".")[0]
                 for name in os.listdir(path_to_ml_model_state_dicts)
                 if re.fullmatch(pattern, name)])

        unformatted_filename = \
            (path_to_ml_model_state_dicts + "/ml_model_at_lr_step_{}.pth")
        ml_model_state_dict_filename = \
            unformatted_filename.format(largest_lr_step_idx)

        kwargs = {"ml_model_state_dict_filename": ml_model_state_dict_filename,
                  "device_name": device_name}
        ml_model = ml_model_task_module.load_ml_model_from_file(**kwargs)

        

        # Run ML model test.
        unformatted_path = (path_to_ml_model_state_dicts
                            + "/ml_model_test_set_1_results"
                            + "/results_for_cbed_patterns_of_{}"
                            + "_with_{}_sized_disks")
        output_dirname = unformatted_path.format(sample_name, disk_size)
        
        misc_model_testing_metadata = {"ml_model_architecture": architecture}

        kwargs = {"ml_dataset_manager": ml_dataset_manager,
                  "device_name": device_name,
                  "output_dirname": output_dirname,
                  "misc_model_testing_metadata": misc_model_testing_metadata}
        ml_model_tester = ml_model_task_module.MLModelTester(**kwargs)

        ml_model_tester.test_ml_model(ml_model)
