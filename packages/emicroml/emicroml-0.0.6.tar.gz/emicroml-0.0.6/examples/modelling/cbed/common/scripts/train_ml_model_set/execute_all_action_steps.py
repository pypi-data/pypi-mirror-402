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
r"""A script that is called by various other scripts used for training sets of
machine learning (ML) models for a specified task.

The action of training a set of ML models is broken down effectively into
multiple steps, where each step trains a single ML model. These steps are
executed in parallel if a SLURM workload manager is used. Moreover, each step
can be thought of as an "action" as well, which itself is broken down into
multiple steps.

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



###########################
## Define error messages ##
###########################



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
parser = argparse.ArgumentParser()
argument_names = ("ml_model_task", "data_dir_1", "repo_root", "use_slurm")
for argument_name in argument_names:
    parser.add_argument("--"+argument_name)
args = parser.parse_args()
ml_model_task = args.ml_model_task
path_to_data_dir_1 = args.data_dir_1
path_to_repo_root = args.repo_root
use_slurm = args.use_slurm



# Get the path to the script that trains a single ML model.
path_to_current_script = pathlib.Path(os.path.realpath(__file__))
path_to_script_to_execute = (str(path_to_current_script.parents[1])
                             + "/train_ml_model/execute_all_action_steps.py")



# Execute the script at ``path_to_script_to_execute`` multiple times to train
# multiple ML models.
num_ml_models_to_train = 10
for ml_model_idx in range(num_ml_models_to_train):
    unformatted_cmd_str = ("python {} "
                           "--ml_model_task={} "
                           "--ml_model_idx={} "
                           "--data_dir_1={} "
                           "--repo_root={} "
                           "--use_slurm={}")
    cmd_str = unformatted_cmd_str.format(path_to_script_to_execute,
                                         ml_model_task,
                                         ml_model_idx,
                                         path_to_data_dir_1,
                                         path_to_repo_root,
                                         use_slurm)
    os.system(cmd_str)
    print("\n\n\n")
