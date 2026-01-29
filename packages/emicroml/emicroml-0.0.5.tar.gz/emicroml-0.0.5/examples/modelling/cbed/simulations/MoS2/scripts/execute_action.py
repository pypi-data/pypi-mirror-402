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
r"""A script for generating the atomic coordinates of a model of a 5-layer
:math:`\text{MoS}_2` thin film.

To execute this action, first we need to change into the directory
``<root>/examples/modelling/cbed/simulations/MoS2/scripts``, where ``<root>`` is
the root of the ``emicroml`` repository. Then, we need to run the Python script
``./execute_action.py`` via the terminal command::

  python execute_action.py --action=<action> --use_slurm=<use_slurm>

where ``<action>`` must be equal to ``generate_atomic_coords``, and
``<use_slurm>`` is either ``yes`` or ``no``. If ``<use_slurm>`` equals ``yes``
and a SLURM workload manager is available on the server from which you intend to
run the script, then the action will be performed as a SLURM job. If
``<use_slurm>`` is equal to ``no``, then the action will be performed locally
without using a SLURM workload manager.

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

We assume that the atoms are subject to room temperature. Furthermore, we assume
that the root-mean-square (RMS) :math:`x`-displacements of the Mo and S atoms
are 0.069 Å and 0.062 Å respectively. These values were taken from
Ref. [Schonfeld1]_.

Upon successful completion of the current script, the atomic coordinates of the
model of :math:`\text{MoS}_2` are stored in the file at the file path
``../data/atomic_coords.xyz``. Moreover, a subset of the sample model parameters
used to construct the model of :math:`\text{MoS}_2` are stored in the JSON file
at the file path ``../data/sample_model_params_subset.json``. The atomic
coordinates file will be formatted as an atomic coordinates file that is
accepted by :mod:`prismatique`: see the description of the parameter
``atomic_coords_filename`` of the class :class:`prismatique.sample.ModelParams`
for a discussion on the correct formatting of such an atomic coordinates file.

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
    accepted_actions = ("generate_atomic_coords",)

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
        unformatted_err_msg = globals()["_"+current_func_name+"_err_msg_1"]
        args = accepted_actions
        err_msg = unformatted_err_msg.format(*args)
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
     "where ``<action>`` can be ``{}``; and ``<use_slurm>`` can be either "
     "``yes`` or ``no``.")



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
converted_cmd_line_args = parse_and_convert_cmd_line_args()
action = converted_cmd_line_args["action"]
use_slurm = converted_cmd_line_args["use_slurm"]



# Get the path to the script that executes the remainder of the action. This
# path is equal to
# ``<path_to_directory_containing_current_script>/<action>/execute_all_action_steps.py``,
# where ``<path_to_directory_containing_current_script>`` is the path to the
# directory containing directly the current script, and ``<action>`` is the
# string specifying the action to be performed, equal in value to the variable
# ``action``.
path_to_current_script = pathlib.Path(os.path.realpath(__file__))
path_to_data_dir_1 = str(path_to_current_script.parents[1]) + "/data"
path_to_repo_root = str(path_to_current_script.parents[6])
path_to_script_to_execute = (str(path_to_current_script.parent)
                             + "/" + action + "/execute_all_action_steps.py")



# Execute the script at ``path_to_script_to_execute``.
unformatted_cmd_str = ("python {} "
                       "--data_dir_1={} "
                       "--repo_root={} "
                       "--use_slurm={}")

cmd_str = unformatted_cmd_str.format(path_to_script_to_execute,
                                     path_to_data_dir_1,
                                     path_to_repo_root,
                                     use_slurm)
os.system(cmd_str)
