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
r"""A script that is called by other scripts used for generating the atomic
coordinates of a model of a :math:`\text{MoS}_2` thin film with a layer of
amorphous carbon (C). The atomic coordinates of this sample are determined in
part by those of two other models: a model of a :math:`\text{MoS}_2` thin film
without amorphous C; and a model of a amorphous C superblock.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --data_dir_1=<data_dir_1> \
         --data_dir_2=<data_dir_2> \
         --data_dir_3=<data_dir_3>

where ``<data_dir_1>`` is the absolute path to the output directory;
``<data_dir_2>`` is the absolute path to a directory directly containing the
file that stores the atomic coordinates of the model of the :math:`\text{MoS}_2`
thin film without amorphous C; and ``<data_dir_3>`` is the absolute path to a
directory directly containing the file that stores the atomic coordinates of the
model of the amorphous C superblock.

``<data_dir_2>`` must be the absolute path to an existing directory that
contains a file with the basename ``atomic_coords.xyz``, which stores the atomic
coordinates of the model of the :math:`\text{MoS}_2` thin film without amorphous
C. ``<data_dir_3>`` must be the absolute path to an existing directory that
contains a file with the basename ``atomic_coords.xyz``, which stores the atomic
coordinates of the model of the amorphous C superblock. Each file should be
formatted as an atomic coordinates file that is accepted by :mod:`prismatique`:
see the description of the parameter ``atomic_coords_filename`` of the class
:class:`prismatique.sample.ModelParams` for a discussion on the expected
formatting of such an atomic coordinates file.

We assume that the C atoms are subject to room temperature, and that their
root-mean-square :math:`x`-displacement is 0.141 Å. This value was taken from 
Ref. [Boothroyd1]_.

We assume that the Mo and S atoms are subject to room temperature. Furthermore,
we assume that the root-mean-square (RMS) :math:`x`-displacements of the Mo and
S atoms are 0.069 Å and 0.062 Å respectively. These values were taken from
Ref. [Schonfeld1]_.

Upon successful completion of the current script, the atomic coordinates of the
model of the :math:`\text{MoS}_2` thin film with a layer of amorphous C are
stored in the file at the file path ``<data_dir_1>/atomic_coords.xyz``, which
will have the same formatting as that expected of the two input atomic
coordinates files mentioned above.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse

# For making directories and creating path objects.
import pathlib



# For general array handling.
import numpy as np



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
argument_names = ("data_dir_1", "data_dir_2", "data_dir_3")
for argument_name in argument_names:
    parser.add_argument("--"+argument_name)
args = parser.parse_args()
path_to_data_dir_1 = args.data_dir_1
path_to_data_dir_2 = args.data_dir_2
path_to_data_dir_3 = args.data_dir_3



# Print the start message.
msg = ("Generating the atomic coordinates for the model of the MoS2 thin film "
       "with a layer of amorphous carbon...")
print(msg)
print()



# Read in the atomic coordinates of the MoS2 sub-sample.
filename = path_to_data_dir_2 + "/atomic_coords.xyz"
with open(filename, "r") as file_obj:
    throw_away_line = file_obj.readline()

    line = file_obj.readline()
    Delta_X = float(line.split()[0])
    Delta_Y = float(line.split()[1])
    Delta_Z_of_MoS2 = float(line.split()[2])

    last_line_has_not_been_read = True

    Mo_sample_unit_cell = []
    S_sample_unit_cell = []

    atomic_potential_extent = np.inf

    while last_line_has_not_been_read:
        line = file_obj.readline()
        numbers_from_lines = tuple(float(string) for string in line.split())
        if len(numbers_from_lines) == 1:
            last_line_has_not_been_read = False
        else:
            Z, x, y, z_prime, occ, u_x_rms = numbers_from_lines
            atomic_potential_extent = min(z_prime, atomic_potential_extent)
            if Z == 42:
                Mo_sample_unit_cell.append([x, y, z_prime])
            else:
                S_sample_unit_cell.append([x, y, z_prime])

Mo_sample_unit_cell = np.array(Mo_sample_unit_cell)
S_sample_unit_cell = np.array(S_sample_unit_cell)



# Read in the atomic coordinates of the amorphous C superblock and shift them
# such that the amorphous C superblock lies above the MoS2 sub-sample, i.e. the
# electron beam makes contact with the amorphous C superblock first.
filename = path_to_data_dir_3 + "/atomic_coords.xyz"
with open(filename, "r") as file_obj:
    throw_away_line = file_obj.readline()
    throw_away_line = file_obj.readline()

    last_line_has_not_been_read = True

    C_sample_unit_cell = []

    z_prime_shift = Delta_Z_of_MoS2 - (atomic_potential_extent/2)
    Delta_Z = 0

    while last_line_has_not_been_read:
        line = file_obj.readline()
        numbers_from_lines = tuple(float(string) for string in line.split())
        if len(numbers_from_lines) == 1:
            last_line_has_not_been_read = False
        else:
            Z, x, y, z_prime, occ, u_x_rms = numbers_from_lines
            Delta_Z = max(z_prime+z_prime_shift+atomic_potential_extent,
                          Delta_Z)
            C_sample_unit_cell.append([x, y, z_prime+z_prime_shift])

C_sample_unit_cell = np.array(C_sample_unit_cell)



# Set the sample unit cell dimensions.
sample_unit_cell_dims = (Delta_X, Delta_Y, Delta_Z)



# Write the atomic coordinates of the target sample to file.
output_dirname = str(path_to_data_dir_1)
pathlib.Path(output_dirname).mkdir(parents=True, exist_ok=True)

filename = output_dirname + "/atomic_coords.xyz"
with open(filename, "w") as file_obj:
    line = "MoS2 on Amorphous C Sample\n"
    file_obj.write(line)

    unformatted_line = "\t{:18.14f}\t{:18.14f}\t{:18.14f}\n"
    formatted_line = unformatted_line.format(*sample_unit_cell_dims)
    file_obj.write(formatted_line)

    occ = 1  # Number not used except to write file with expected format.

    Z_of_Mo = 42  # Atomic number of Mo.
    Z_of_S = 16  # Atomic number of S.
    Z_of_C = 6  # Atomic number of C.

    # The RMS x-displacement of the Mo atoms at room temperature, in units of
    # Å. The value was taken from experimental data for the RMS of the in-plane
    # displacement in Schönfeld et al., Acta Cryst. B39, 404-407 (1983).
    u_x_rms_of_Mo = 0.069

    # The RMS x-displacement of the S atoms at room temperature, in units of
    # Å. The value was taken from experimental data for the RMS of the in-plane
    # displacement in Schönfeld et al., Acta Cryst. B39, 404-407 (1983).
    u_x_rms_of_S = 0.062

    # The RMS x-displacement of the C atoms at room temperature, in units of
    # Å. The value was taken from C. B. Boothroyd, Ultramicroscopy **83**, 3-4
    # (2000).
    u_x_rms_of_C = 0.141

    single_species_sample_unit_cells = (Mo_sample_unit_cell,
                                        S_sample_unit_cell,
                                        C_sample_unit_cell)
    Z_set = (Z_of_Mo, Z_of_S, Z_of_C)
    u_x_rms_set = (u_x_rms_of_Mo, u_x_rms_of_S, u_x_rms_of_C)
    zip_obj = zip(single_species_sample_unit_cells, Z_set, u_x_rms_set)
        
    for triplet in zip_obj:
        single_species_sample_unit_cell, Z, u_x_rms = triplet
        for position_of_atom in single_species_sample_unit_cell:
            x, y, z_prime = position_of_atom
            unformatted_line = ("{}\t{:18.14f}\t{:18.14f}"
                                "\t{:18.14f}\t{:18.14f}\t{:18.14f}\n")
            args = (Z, x, y, z_prime, occ, u_x_rms)
            formatted_line = unformatted_line.format(*args)
            file_obj.write(formatted_line)

    file_obj.write("-1")



# Print the end message.
msg = ("Finished generating the atomic coordinates for the model of the MoS2 "
       "thin film with a layer of amorphous carbon: the atomic coordinates "
       "were written to the file {}.".format(filename))
print(msg)
print()
