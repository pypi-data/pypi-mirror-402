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



# The current script will attempt to create a virtual environment, then activate
# it within the current shell, and then install the ``emicroml`` library within
# said environment, along with some optional libraries. If the script is
# executed on a Digital Alliance of Canada (DRAC) high-performance computing
# (HPC) server, then the virtual environment is created via
# ``virtualenv``. Otherwise, the virtual environment is created via
# ``conda``. For the latter scenario, an ``anaconda`` or ``miniconda``
# distribution must be installed prior to running the script.
#
# The correct form of the command to run the script is::
#
#  source <path_to_current_script> <env_name> <install_extras>
#
# where ``<path_to_current_script>`` is the absolute or relative path to the
# current script; ``<env_name>`` is the path to the virtual environment, if the
# script is being executed on a DRAC HPC server, else it is the name of the
# ``conda`` virtual environment; and ``<install_extras>`` is a boolean, i.e. it
# should either be ``true`` or ``false``. If ``<install_extras>`` is set to
# ``true``, then the script will attempt to install within the environment the
# dependencies required to run all of the examples in the repository, in
# addition to installing ``emicroml``. Otherwise, the script will attempt to
# install only ``emicroml`` and its dependencies, i.e. not the additional
# libraries required to run the examples.
#
# If the virtual environment is to be created on a HPC server belonging to DRAC,
# and the script with the basename
# ``download_wheels_for_offline_env_setup_on_drac_server.sh`` at the root of the
# repository has never been executed, then one must first change into the root
# of the repository, and subsequently execute that script via the following
# command::
#
#  bash download_wheels_for_offline_env_setup_on_drac_server.sh
#
# Upon completion of that script, a set of Python wheels will be downloaded to
# the directory ``<root>/_wheels_for_offline_env_setup_on_drac_server``, where
# ``<root>`` is the root of the repository. Note that that script only needs to
# be executed once, assuming one does not modify or delete the directory
# ``<root>/_wheels_for_offline_env_setup_on_drac_server``.



# Begin timer, and print starting message.
start_time=$(date +%s.%N)

msg="Beginning virtual environment creation and setup..."
echo ""
echo ${msg}
echo ""
echo ""
echo ""



# Get the path to the root of the repository.
cmd="realpath "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)""
path_to_repo_root=$(${cmd})



# Automatically determine whether the script is being executed on a DRAC HPC
# server.
current_machine_is_on_a_drac_server=false

path_to_python_wheels=/cvmfs/soft.computecanada.ca/custom/python/wheelhouse

if [ -d "${path_to_python_wheels}" ]
then
    current_machine_is_on_a_drac_server=true
fi



if [ "${current_machine_is_on_a_drac_server}" = true ]
then
    # Parse the command line arguments.
    if [ $# -eq 0 ]
    then
	path_to_virtual_env=~/emicroml
	install_libs_required_to_run_all_examples=false
    else
	path_to_virtual_env=$1
	install_libs_required_to_run_all_examples=$2
    fi



    # Load some DRAC software modules.
    module load StdEnv/2023
    module load python/3.11 hdf5 cuda



    # Create the virtual environment, activate it, and then upgrade ``pip``.
    cmd="realpath "$(dirname "${path_to_virtual_env}")""
    path_to_parent_dir_of_virtual_env=$(${cmd})
    
    mkdir -p ${path_to_parent_dir_of_virtual_env}
    
    virtualenv --no-download ${path_to_virtual_env}
    source ${path_to_virtual_env}/bin/activate
    pip install --no-index --upgrade pip

    

    # Install the remaining libraries in the virtual environment. Where
    # applicable, GPU-supported versions of libraries are installed.
    pkgs="numpy<2.0.0 numba hyperspy h5py pytest ipympl jupyter torch kornia"
    pkgs=${pkgs}" blosc2 msgpack"
    if [ "${install_libs_required_to_run_all_examples}" = true ]
    then
	pkgs=${pkgs}" pyopencl pyFAI pytools<=2025.1.6 pyprismatic-gpu"
    fi
    pip install --no-index ${pkgs}

    cd ${path_to_repo_root}/_wheels_for_offline_env_setup_on_drac_server

    pkgs="czekitout*.whl fancytypes*.whl h5pywrappers*.whl"
    pkgs=${pkgs}" distoptica*.whl fakecbed*.whl"
    if [ "${install_libs_required_to_run_all_examples}" = true ]
    then
	pkgs=${pkgs}" empix*.whl embeam*.whl prismatique*.whl"
    fi
    pkgs=${pkgs}" emicroml*.whl"
    pip install ${pkgs}

    cd ${path_to_repo_root}
else
    # Parse the command line arguments.
    if [ $# -eq 0 ]
    then
	virtual_env_name=emicroml
	install_libs_required_to_run_all_examples=false
    else
	virtual_env_name=$1
	install_libs_required_to_run_all_examples=$2
    fi



    # Determine automatically whether NVIDIA drivers have been installed. If
    # they have been installed, then the script will install GPU-supported
    # versions of certain libraries.
    nvidia_smi_cmd_1="nvidia-smi"

    nvidia_smi_cmd_2="/c/Program\ Files/NVIDIA\ Corporation/NVSMI"
    nvidia_smi_cmd_2=${nvidia_smi_cmd_2}"/nvidia-smi.exe"

    nvidia_smi_cmd_3="/c/Windows/System32/DriverStore/FileRepository/nvdm*"
    nvidia_smi_cmd_3=${nvidia_smi_cmd_3}"/nvidia-smi.exe"

    declare -a nvidia_smi_cmds=("${nvidia_smi_cmd_1}"
				"${nvidia_smi_cmd_2}"
				"${nvidia_smi_cmd_3}")

    for nvidia_smi_cmd in "${nvidia_smi_cmds[@]}"
    do
	${nvidia_smi_cmd} 2>/dev/null
	if [ "$?" -ne 0 ]
	then
	    major_cuda_version="0"
	    continue
	fi

	cmd_seq=${nvidia_smi_cmd}
	cmd_seq=${cmd_seq}" | grep -oP '(?<=CUDA Version: )'.*"
	cmd_seq=${cmd_seq}"| grep -oP '([1-9]+)' | head -1"
	major_cuda_version="$(eval "${cmd_seq}")"

	if [ "$?" -eq 0 ]
	then
	    break
	fi
    done



    # Determine which versions of ``pytorch`` and ``pyprismatic`` to install
    # according to what NVIDIA drivers are installed, if any.
    if [ "${major_cuda_version}" = 11 ]
    then
	url="https://download.pytorch.org/whl/cu118"
	pyprismatic_pkg="pyprismatic=*=gpu*"
    elif [ "${major_cuda_version}" -gt 11 ]
    then
	url="https://download.pytorch.org/whl/cu121"
	pyprismatic_pkg="pyprismatic=*=gpu*"
    else
	url="https://download.pytorch.org/whl/cpu"
	pyprismatic_pkg="pyprismatic=*=cpu*"
    fi
    extra_torch_install_args="--index-url "${url}



    # Create the ``conda`` virtual environment and install a subset of
    # libraries, then activate the virtual environment.
    pkgs="python=3.11"
    conda create -n ${virtual_env_name} ${pkgs} -y
    conda activate ${virtual_env_name}

    pkgs="numpy numba hyperspy h5py pytest ipympl jupyter h5pywrappers"
    conda install -y ${pkgs} -c conda-forge



    # Install the remaining libraries in the virtual environment.
    pip install torch ${extra_torch_install_args}
    pip install kornia

    if [ "${install_libs_required_to_run_all_examples}" = true ]
    then
    	pkgs="pyopencl[pocl] pyFAI"
    	pip install ${pkgs}
	
    	conda install -y ${pyprismatic_pkg} -c conda-forge

    	pkgs="prismatique"
    fi
    pkgs=${pkgs}" emicroml"
    pip install ${pkgs}
fi



# End timer and print completion message.
end_time=$(date +%s.%N)
elapsed_time=$(echo "${end_time} - ${start_time}" | bc -l)

echo ""
echo ""
echo ""
msg="Finished virtual environment creation and setup. Time taken: "
msg=${msg}"${elapsed_time} s."
echo ${msg}
echo ""
