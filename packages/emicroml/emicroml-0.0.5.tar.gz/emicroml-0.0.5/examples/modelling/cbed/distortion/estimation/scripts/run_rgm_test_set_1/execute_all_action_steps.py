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
"first" set of tests of the radial gradient maximization (RGM) approach to the
distortion estimation of convergent beam electron diffraction (CBED) patterns.

The action of running a set of tests is broken down effectively into multiple
steps, where each step runs a single test. These steps are executed in parallel
if a SLURM workload manager is used. Moreover, each step can be thought of as an
"action" as well, which itself is broken down into multiple steps.

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
argument_names = ("calling_script", "action", "use_slurm")
for argument_name in argument_names:
    parser.add_argument("--"+argument_name)
args = parser.parse_args()
path_to_calling_of_script_of_current_script = args.calling_script
action = args.action
use_slurm = args.use_slurm



# Get the path to the directory in which all input and output data related to
# the specified ML model task is stored or is to be stored.
up_2_levels_from_path_to_calling_script_of_current_script = \
    pathlib.Path(path_to_calling_of_script_of_current_script).parents[1]
path_to_data_dir_1 = \
    (str(up_2_levels_from_path_to_calling_script_of_current_script) + "/data")



# Get the path to the script that runs a single test from the "first" set of
# tests of the RGM approach to distortion estimation. This path is equal to
# ``<path_to_directory_containing_current_script>/../run_rgm_test_from_set_1/execute_all_action_steps.py``,
# where ``<path_to_directory_containing_current_script>`` is the path to the
# directory containing directly the current script.
path_to_current_script = \
    pathlib.Path(os.path.realpath(__file__))
path_to_script_to_execute = \
    (str(path_to_current_script.parents[1])
     + "/run_rgm_test_from_set_1"
     + "/execute_all_action_steps.py")



# Get the path to the root of the repository.
path_to_repo_root = str(path_to_current_script.parents[7])



# Execute the script at ``path_to_script_to_execute`` multiple times to simulate
# multiple CBED experiments.
disk_sizes = ("small", "medium", "large")
for disk_size in disk_sizes:
    unformatted_cmd_str = ("python {} "
                           "--disk_size={} "
                           "--data_dir_1={} "
                           "--repo_root={} "
                           "--use_slurm={}")
    cmd_str = unformatted_cmd_str.format(path_to_script_to_execute,
                                         disk_size,
                                         path_to_data_dir_1,
                                         path_to_repo_root,
                                         use_slurm)
    os.system(cmd_str)
    print("\n\n\n")
