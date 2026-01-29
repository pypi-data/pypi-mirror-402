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
coordinates of a model of a :math:`25 \times 25 \times 1 \ \text{nm}^3` large
superblock of amorphous carbon (C), that is subsequently truncated to the same
lateral dimensions of a model of :math:`\text{MoS}_2`, and to :math:`0.5 \
\text{nm}` along the :math:`z`-axis. The superblock, prior to truncation, is
generating by tiling various transformations of a model of a :math:`5 \times 5
\times 1 \ \text{nm}^3` large block of amorphous C.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --data_dir_1=<data_dir_1> \
         --data_dir_2=<data_dir_2> \
         --data_dir_3=<data_dir_3>

where ``<data_dir_1>`` is the absolute path to the output directory;
``<data_dir_2>`` is the absolute path to a directory directly containing the
file that stores the atomic coordinates of the model of the :math:`5 \times 5
\times 1 \ \text{nm}^3` large block of amorphous C; and ``<data_dir_3>`` is the
absolute path to a directory directly containing the file that stores the atomic
coordinates of the model of :math:`\text{MoS}_2`.

``<data_dir_2>`` must be the absolute path to an existing directory that
contains a file with the basename ``atomic_coords.xyz``, which stores the atomic
coordinates of the model of the :math:`5 \times 5 \times 1 \ \text{nm}^3` large
block of amorphous C. ``<data_dir_3>`` must be the absolute path to an existing
directory that contains a file with the basename ``atomic_coords.xyz``, which
stores the atomic coordinates of the model of :math:`\text{MoS}_2`. Each file
should be formatted as an atomic coordinates file that is accepted by
:mod:`prismatique`: see the description of the parameter
``atomic_coords_filename`` of the class :class:`prismatique.sample.ModelParams`
for a discussion on the expected formatting of such an atomic coordinates file.

We assume that the C atoms are subject to room temperature, and that their
root-mean-square :math:`x`-displacement is 0.141 Å. This value was taken from 
Ref. [Boothroyd1]_.

Upon successful completion of the current script, the atomic coordinates of the
model of the truncated superblock of amorphous C are stored in the file at the
file path ``<data_dir_1>/atomic_coords.xyz``, which will have the same
formatting as that expected of the two input atomic coordinates files mentioned
above. 

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse

# For making directories and creating path objects.
import pathlib

# For generating permutations of a sequence.
import itertools



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
msg = ("Generating the atomic coordinates for the model of the superblock of "
       "amorphous carbon...")
print(msg)
print()



# The idea is to read-in the atomic coordinates of a 5x5x1 nm^3 large block of
# amorphous carbon (C), and store this block for later use in some
# container. Next, we take the block in this container, transform the block in a
# variety of ways using reflections and axes permutations, to generate 25 5x5x1
# nm^3 blocks, which we can then tile to construct our 25x25x1 nm^3 sized
# superblock, which we then truncate to the same lateral dimensions as the MoS2
# sub-sample, and to 0.5 nm along the z-axis.



# Read in the atomic coordinates of the 5x5x1 nm^3 large amorphous C block.
filename = path_to_data_dir_2 + "/atomic_coords.xyz"
with open(filename, "r") as file_obj:
    throw_away_line = file_obj.readline()
        
    line = file_obj.readline()
    amorphous_C_block_tile_dims = tuple(float(s) for s in line.split())

    last_line_has_not_been_read = True

    amorphous_C_block_tile = []

    while last_line_has_not_been_read:
        line = file_obj.readline()
        numbers_from_lines = tuple(float(string) for string in line.split())
        if len(numbers_from_lines) == 1:
            last_line_has_not_been_read = False
        else:
            Z, x, y, z_prime, occ, u_x_rms = numbers_from_lines
            position_of_atom = (x, y, z_prime)
            amorphous_C_block_tile.append(position_of_atom)



# Generate the set of transformations to apply to the block.
reflection_seq_set = []
for reflect_across_yz_plane in (False, True):
    for reflect_across_xz_plane in (False, True):
        for reflect_across_xy_plane in (False, True):
            reflection_seq = ((-1)**reflect_across_yz_plane,
                              (-1)**reflect_across_xz_plane,
                              (-1)**reflect_across_xy_plane)
            reflection_seq_set.append(reflection_seq)
                
axes_permutations = tuple(itertools.permutations([0, 1, 2]))



# Transform the block to yield 25 blocks; and tile the 25 blocks to generate a
# 25x25x1 nm^3 superblock, which we will subsequently truncate.
block_tile_idx = 0
target_num_blocks = 25
amorphous_C_superblock_dims_in_blocks = (5, 5, 1)
amorphous_C_block_side_length = amorphous_C_block_tile_dims[0]
amorphous_C_superblock_sample_unit_cell = []

for reflection_seq in reflection_seq_set:
    for axes_permutation in axes_permutations:
        shift = np.unravel_index(block_tile_idx,
                                 amorphous_C_superblock_dims_in_blocks)
        shift = amorphous_C_block_side_length * np.array(shift)
        transformation_matrix = reflection_seq * np.eye(3)[axes_permutation, :]
        for position_of_seed_atom in amorphous_C_block_tile:
            position_of_atom = position_of_seed_atom @ transformation_matrix
            position_of_atom %= amorphous_C_block_tile_dims
            position_of_atom += shift
            amorphous_C_superblock_sample_unit_cell.append(position_of_atom)
        block_tile_idx += 1
        if block_tile_idx == target_num_blocks:
            break
    if block_tile_idx == target_num_blocks:
        break



# Read in the dimensions of the MoS2 sub-sample.
filename = path_to_data_dir_3 + "/atomic_coords.xyz"
with open(filename, "r") as file_obj:
    throw_away_line = file_obj.readline()
        
    line = file_obj.readline()
MoS2_subsample_dims = tuple(float(s) for s in line.split())
Delta_X, Delta_Y, _ = MoS2_subsample_dims  # In Å.



# Set the amorphous C superblock unit cell dimensions.
Delta_Z = 5  # In Å.
sample_unit_cell_dims = (Delta_X, Delta_Y, Delta_Z)



# Truncate the amorphous C superblock.
num_atoms_in_amorphous_C_superblock_pre_truncation = \
    len(amorphous_C_superblock_sample_unit_cell)

indices = range(num_atoms_in_amorphous_C_superblock_pre_truncation-1, -1, -1)
for idx in indices:
    position_of_atom = amorphous_C_superblock_sample_unit_cell[idx]
    x, y, z_prime = position_of_atom
    if (((x < 0) or (Delta_X <= x))
        or ((y < 0) or (Delta_Y <= y))
        or ((z_prime < 0) or (Delta_Z <= z_prime))):
        del amorphous_C_superblock_sample_unit_cell[idx]



# Write the atomic coordinates of the target sample to file.
output_dirname = str(path_to_data_dir_1)
pathlib.Path(output_dirname).mkdir(parents=True, exist_ok=True)

filename = output_dirname + "/atomic_coords.xyz"
with open(filename, "w") as file_obj:
    line = "Amorphous C Superblock\n"
    file_obj.write(line)

    unformatted_line = "\t{:18.14f}\t{:18.14f}\t{:18.14f}\n"
    formatted_line = unformatted_line.format(*sample_unit_cell_dims)
    file_obj.write(formatted_line)

    occ = 1  # Number not used except to write file with expected format.

    Z_of_C = 6  # Atomic number of C.

    # The RMS x-displacement of the C atoms at room temperature, in units of
    # Å. The value was taken from C. B. Boothroyd, Ultramicroscopy **83**, 3-4
    # (2000).
    u_x_rms_of_C = 0.141

    C_sample_unit_cell = amorphous_C_superblock_sample_unit_cell
    single_species_sample_unit_cells = (C_sample_unit_cell,)
    Z_set = (Z_of_C,)
    u_x_rms_set = (u_x_rms_of_C,)
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
msg = ("Finished generating the atomic coordinates for the model of the "
       "superblock of amorphous carbon: the atomic coordinates were written to "
       "the file {}.".format(filename))
print(msg)
print()
