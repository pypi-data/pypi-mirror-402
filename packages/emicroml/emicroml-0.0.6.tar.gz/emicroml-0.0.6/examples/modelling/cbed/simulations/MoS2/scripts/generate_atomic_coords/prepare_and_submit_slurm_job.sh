#!/bin/bash
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



# The current script is expected to be called only by the parent script with the
# basename ``execute_all_action_steps.py``, located in the same directory as the
# current script. The parent script performs the "action" of generating the
# atomic coordinates of a model of a 5-layer :math:`\text{MoS}_2` thin film.
#
# The current script prepares and submits a SLURM job which:
#
#   1. Sets the remaining parameters required to execute the "main" steps of the
#   action that were not set by the parent script.
#
#   2. Prepares the input data required to execute the main steps.
#
#   3. Executes the main steps.
#
#   4. Moves non-temporary output data that is generated from the main steps to
#   their expected final destinations.
#
#   5. Deletes/removes any remaining temporary files or directories.
#
# The main steps are executed by running the script with the basename
# ``execute_main_action_steps.py``, located in the same directory as the current
# script.



#SBATCH --job-name=generate_atomic_coords
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1  # CPU cores/threads
#SBATCH --mem=4G           # CPU memory per node
#SBATCH --time=00-02:59    # time (DD-HH:MM)
#SBATCH --mail-type=ALL

# Parse the command line arguments.
path_to_dir_containing_current_script=${1}
path_to_repo_root=${2}
path_to_data_dir_1=${3}
overwrite_slurm_tmpdir=${4}



# Overwrite ``SLURM_TMPDIR`` if specified to do so.
if [ "${overwrite_slurm_tmpdir}" = true ]
then
    SLURM_TMPDIR=${path_to_data_dir_1}/tmp_dir
fi



# Setup the Python virtual environment used to execute the main action steps.
basename=custom_env_setup_for_slurm_jobs.sh
if [ ! -f ${path_to_repo_root}/${basename} ]
then
    basename=default_env_setup_for_slurm_jobs.sh
fi
source ${path_to_repo_root}/${basename} ${SLURM_TMPDIR}/tempenv false



# Execute the script which executes the main action steps.
basename=execute_main_action_steps.py
path_to_script_to_execute=${path_to_dir_containing_current_script}/${basename}

python ${path_to_script_to_execute} \
       --data_dir_1=${SLURM_TMPDIR}
python_script_exit_code=$?

if [ "${python_script_exit_code}" != 0 ];
then
    msg="\n\n\nThe slurm job terminated early with at least one error. "
    msg=${msg}"See traceback for details.\n\n\n"
    echo -e ${msg}
    exit 1
fi



# Move the non-temporary output data that is generated from the main steps to
# their expected final destinations. Also delete/remove any remaining temporary
# files or directories.
cd ${SLURM_TMPDIR}

basenames=(atomic_coords.xyz sample_model_params_subset.json)

for basename_1 in "${basenames[@]}"
do
    dirname_1=${SLURM_TMPDIR}
    dirname_2=${path_to_data_dir_1}
    basename_2=${basename_1}
    filename_1=${dirname_1}/${basename_1}
    filename_2=${dirname_2}/${basename_2}

    mkdir -p ${dirname_2}
    if [ "${filename_1}" != "${filename_2}" ]
    then
	echo ""
	echo ""
	mv ${filename_1} ${filename_2}
	msg="Moved file at ``'"${filename_1}"'`` to ``'"${filename_2}"'``."
	echo ${msg}
    fi
done

if [ "${overwrite_slurm_tmpdir}" = true ]
then
    cd ${path_to_repo_root}
    rm -rf ${SLURM_TMPDIR}
fi
