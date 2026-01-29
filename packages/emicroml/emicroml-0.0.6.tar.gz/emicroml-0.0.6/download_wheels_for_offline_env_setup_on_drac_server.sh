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



# The current script downloads the Python wheels required to install
# ``emicroml`` and to run all of the examples in this repository, on any
# high-performance computing server belonging to Digital Alliance of Canada,
# without internet access subsequent to downloading said wheels. The correct
# form of the command to run the script is::
#
#  bash download_wheels_for_offline_env_setup_on_drac_server.sh
#
# Upon completion of the script, the wheels will be downloaded to the directory
# ``<root>/_wheels_for_offline_env_setup_on_drac_server``, where ``<root>`` is
# the root of the repository. Note that this script only needs to be executed
# once, assuming one does not modify or delete the directory
# ``<root>/_wheels_for_offline_env_setup_on_drac_server``.



# Get the path to the root of the repository.
cmd="realpath "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)""
path_to_repo_root=$(${cmd})

# Create directory in which to download wheels.
mkdir -p ${path_to_repo_root}/_wheels_for_offline_env_setup_on_drac_server

# Change into the aforementioned directory.
cd ${path_to_repo_root}/_wheels_for_offline_env_setup_on_drac_server

# Load some DRAC software modules.
module load StdEnv/2023
module load python/3.11

# Download the wheels.
pip download --no-deps czekitout
pip download --no-deps fancytypes
pip download --no-deps h5pywrappers
pip download --no-deps distoptica
pip download --no-deps fakecbed
pip download --no-deps empix
pip download --no-deps embeam
pip download --no-deps hyperspy_gui_ipywidgets
pip download --no-deps link_traits
pip download --no-deps prismatique
pip download --no-deps emicroml

# Change into the root of the repository.
cd ${path_to_repo_root}
