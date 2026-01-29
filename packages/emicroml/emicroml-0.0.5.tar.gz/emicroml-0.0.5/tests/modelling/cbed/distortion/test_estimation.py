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
r"""Contains tests for the module
:mod:`emicrocml.modelling.cbed.distortion.estimation`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For operations related to unit tests.
import pytest

# For creating distortion models.
import distoptica

# For generating fake CBED disks.
import fakecbed

# For removing directories.
import shutil

# For setting file permissions.
import os

# For making directories.
import pathlib

# For creating instances of the class ``collections.OrderedDict``.
import collections



# For general array handling.
import numpy as np
import torch

# For creating HDF5 files.
import h5py



# For creating wrappers to PyTorch optimizer classes.
import emicroml.modelling.optimizers

# For creating learning rate scheduler managers.
import emicroml.modelling.lr

# For training models for distortion estimation in CBED.
import emicroml.modelling.cbed.distortion.estimation



##################################
## Define classes and functions ##
##################################



def generate_default_distortion_model_generator_1_ctor_params():
    default_distortion_model_generator_1_ctor_params = \
        {"reference_pt": (0.53, 0.48),
         "rng_seed": 7,
         "sampling_grid_dims_in_pixels": (64, 64),
         "least_squares_alg_params": distoptica.LeastSquaresAlgParams(),
         "device_name": "cpu",
         "skip_validation_and_conversion": False}

    return default_distortion_model_generator_1_ctor_params



def generate_default_distortion_model_generator_2_ctor_params():
    default_distortion_model_generator_2_ctor_params = \
        {"reference_pt": (100.5, 10.5),
         "rng_seed": 0,
         "sampling_grid_dims_in_pixels": (32, 32),
         "least_squares_alg_params": None,
         "device_name": None,
         "skip_validation_and_conversion": False}

    return default_distortion_model_generator_2_ctor_params



def generate_default_cbed_pattern_generator_1_ctor_params():
    default_cbed_pattern_generator_1_ctor_params = \
        {"num_pixels_across_each_cbed_pattern": 64,
         "max_num_disks_in_any_cbed_pattern": 90,
         "rng_seed": 0,
         "sampling_grid_dims_in_pixels": (64, 64),
         "least_squares_alg_params": None,
         "device_name": None,
         "skip_validation_and_conversion": False}

    return default_cbed_pattern_generator_1_ctor_params



def generate_default_cbed_pattern_generator_2_ctor_params():
    default_cbed_pattern_generator_2_ctor_params = \
        {"num_pixels_across_each_cbed_pattern": 32,
         "max_num_disks_in_any_cbed_pattern": 90,
         "rng_seed": 0,
         "sampling_grid_dims_in_pixels": (32, 32),
         "least_squares_alg_params": None,
         "device_name": None,
         "skip_validation_and_conversion": False}

    return default_cbed_pattern_generator_2_ctor_params



class InvalidCBEDPatternGenerator1():
    def __init__(self):
        return None



    def generate(self):
        return None



_module_alias = emicroml.modelling.cbed.distortion.estimation
_cls_alias = _module_alias.DefaultCBEDPatternGenerator
class InvalidCBEDPatternGenerator2(_cls_alias):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 max_num_disks_in_any_cbed_pattern,
                 rng_seed,
                 sampling_grid_dims_in_pixels,
                 least_squares_alg_params,
                 device_name,
                 skip_validation_and_conversion):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        module_alias = emicroml.modelling.cbed.distortion.estimation
        cls_alias = module_alias.DefaultCBEDPatternGenerator
        cls_alias.__init__(self, **kwargs)

        return None



    def generate(self):
        cbed_pattern = super().generate()

        kwargs = {"center": (0.5, 0.5),
                  "radius": 2,
                  "intra_shape_val": 1}
        undistorted_disk_support = fakecbed.shapes.Circle(**kwargs)

        kwargs = {"support": undistorted_disk_support,
                  "intra_support_shapes": tuple()}
        undistorted_disk = fakecbed.shapes.NonuniformBoundedShape(**kwargs)

        undistorted_disks = (cbed_pattern.core_attrs["undistorted_disks"]
                             + (undistorted_disk,))

        new_core_attr_subset_candidate = {"undistorted_disks": \
                                          undistorted_disks}
        cbed_pattern.update(new_core_attr_subset_candidate)

        return cbed_pattern



_module_alias = emicroml.modelling.cbed.distortion.estimation
_cls_alias = _module_alias.DefaultCBEDPatternGenerator
class InvalidCBEDPatternGenerator3(_cls_alias):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 max_num_disks_in_any_cbed_pattern,
                 rng_seed,
                 sampling_grid_dims_in_pixels,
                 least_squares_alg_params,
                 device_name,
                 skip_validation_and_conversion):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        module_alias = emicroml.modelling.cbed.distortion.estimation
        cls_alias = module_alias.DefaultCBEDPatternGenerator
        cls_alias.__init__(self, **kwargs)

        return None



    def generate(self):
        cbed_pattern = super().generate()

        distortion_model = cbed_pattern.core_attrs["distortion_model"]

        kwargs = {"radial_cosine_coefficient_matrix": ((0.001,),)}
        coord_transform_params = distoptica.CoordTransformParams(**kwargs)

        new_core_attr_subset_candidate = {"coord_transform_params": \
                                          coord_transform_params}
        distortion_model.update(new_core_attr_subset_candidate)

        new_core_attr_subset_candidate = {"distortion_model": distortion_model}
        cbed_pattern.update(new_core_attr_subset_candidate)

        return cbed_pattern



_module_alias = emicroml.modelling.cbed.distortion.estimation
_cls_alias = _module_alias.DefaultCBEDPatternGenerator
class InvalidCBEDPatternGenerator4(_cls_alias):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 max_num_disks_in_any_cbed_pattern,
                 rng_seed,
                 sampling_grid_dims_in_pixels,
                 least_squares_alg_params,
                 device_name,
                 skip_validation_and_conversion):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        module_alias = emicroml.modelling.cbed.distortion.estimation
        cls_alias = module_alias.DefaultCBEDPatternGenerator
        cls_alias.__init__(self, **kwargs)

        self._generation_count = 0

        return None



    def generate(self):
        cbed_pattern = super().generate()
        
        if self._generation_count > 0:
            new_core_attr_subset_candidate = \
                {"num_pixels_across_pattern": \
                 self._num_pixels_across_each_cbed_pattern//2}
            _ = \
                cbed_pattern.update(new_core_attr_subset_candidate)

        self._generation_count += 1

        return cbed_pattern



_module_alias = emicroml.modelling.cbed.distortion.estimation
_cls_alias = _module_alias.DefaultCBEDPatternGenerator
class InvalidCBEDPatternGenerator5(_cls_alias):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 max_num_disks_in_any_cbed_pattern,
                 rng_seed,
                 sampling_grid_dims_in_pixels,
                 least_squares_alg_params,
                 device_name,
                 skip_validation_and_conversion):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        module_alias = emicroml.modelling.cbed.distortion.estimation
        cls_alias = module_alias.DefaultCBEDPatternGenerator
        cls_alias.__init__(self, **kwargs)

        self._generation_count = 0

        return None



    def generate(self):
        cbed_pattern = super().generate()
        
        if self._generation_count > 1:
            raise

        self._generation_count += 1

        return cbed_pattern



def generate_path_to_test_data():
    path_to_test_data = "./test_data"

    return path_to_test_data



def generate_ml_data_dict_0():
    N_x = 16
    N_y = N_x
    mini_batch_size = 1
    max_num_disks_in_any_cbed_pattern = 6

    N_B = mini_batch_size
    N_D = max_num_disks_in_any_cbed_pattern
    
    cbed_pattern_images = np.zeros((N_B, N_y, N_x), dtype=np.float32)
    cbed_pattern_images[0, 0, 0] = 1

    disk_overlap_maps = np.zeros_like(cbed_pattern_images, dtype=np.uint8)

    disk_clipping_registries = np.zeros((N_B, N_D), dtype=bool)
    disk_objectness_sets = np.zeros((N_B, N_D), dtype=np.float32)
    common_undistorted_disk_radii = np.ones((N_B,), dtype=np.float32)
    undistorted_disk_center_sets = 0.5*np.ones((N_B, N_D, 2), dtype=np.float32)

    distortion_centers = 0.5*np.ones((N_B, 2), dtype=np.float32)
    quadratic_radial_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    elliptical_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)
    spiral_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    parabolic_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)

    ml_data_dict_0 = {"cbed_pattern_images": \
                      cbed_pattern_images,
                      "disk_overlap_maps": \
                      disk_overlap_maps,
                      "disk_clipping_registries": \
                      disk_clipping_registries,
                      "disk_objectness_sets": \
                      disk_objectness_sets,
                      "common_undistorted_disk_radii": \
                      common_undistorted_disk_radii,
                      "undistorted_disk_center_sets": \
                      undistorted_disk_center_sets,
                      "distortion_centers": \
                      distortion_centers,
                      "quadratic_radial_distortion_amplitudes": \
                      quadratic_radial_distortion_amplitudes,
                      "elliptical_distortion_vectors": \
                      elliptical_distortion_vectors,
                      "spiral_distortion_amplitudes": \
                      spiral_distortion_amplitudes,
                      "parabolic_distortion_vectors": \
                      parabolic_distortion_vectors}

    return ml_data_dict_0



def generate_ml_data_dict_1():
    N_x = 8
    N_y = N_x
    mini_batch_size = 1
    max_num_disks_in_any_cbed_pattern = 6

    N_B = mini_batch_size
    N_D = max_num_disks_in_any_cbed_pattern
    
    cbed_pattern_images = np.zeros((N_B, N_y, N_x), dtype=np.float32)
    cbed_pattern_images[0, 0, 0] = 1

    disk_overlap_maps = np.zeros_like(cbed_pattern_images, dtype=np.uint8)

    disk_clipping_registries = np.zeros((N_B, N_D), dtype=bool)
    disk_objectness_sets = np.zeros((N_B, N_D), dtype=np.float32)
    common_undistorted_disk_radii = np.ones((N_B,), dtype=np.float32)
    undistorted_disk_center_sets = 0.5*np.ones((N_B, N_D, 2), dtype=np.float32)

    distortion_centers = 0.5*np.ones((N_B, 2), dtype=np.float32)
    quadratic_radial_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    elliptical_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)
    spiral_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    parabolic_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)

    ml_data_dict_1 = {"cbed_pattern_images": \
                      cbed_pattern_images,
                      "disk_overlap_maps": \
                      disk_overlap_maps,
                      "disk_clipping_registries": \
                      disk_clipping_registries,
                      "disk_objectness_sets": \
                      disk_objectness_sets,
                      "common_undistorted_disk_radii": \
                      common_undistorted_disk_radii,
                      "undistorted_disk_center_sets": \
                      undistorted_disk_center_sets,
                      "distortion_centers": \
                      distortion_centers,
                      "quadratic_radial_distortion_amplitudes": \
                      quadratic_radial_distortion_amplitudes,
                      "elliptical_distortion_vectors": \
                      elliptical_distortion_vectors,
                      "spiral_distortion_amplitudes": \
                      spiral_distortion_amplitudes,
                      "parabolic_distortion_vectors": \
                      parabolic_distortion_vectors}

    return ml_data_dict_1



def generate_ml_data_dict_2():
    N_x = 32
    N_y = N_x
    mini_batch_size = 2
    max_num_disks_in_any_cbed_pattern = 6

    N_B = mini_batch_size
    N_D = max_num_disks_in_any_cbed_pattern
    
    cbed_pattern_images = np.zeros((N_B, N_y, N_x), dtype=np.float32)
    cbed_pattern_images[0, 0, 0] = 1
    cbed_pattern_images[1, 1, 0] = 1

    disk_overlap_maps = np.zeros_like(cbed_pattern_images, dtype=np.uint8)

    disk_clipping_registries = np.zeros((N_B, N_D), dtype=bool)
    disk_objectness_sets = np.zeros((N_B, N_D), dtype=np.float32)
    common_undistorted_disk_radii = np.ones((N_B,), dtype=np.float32)
    undistorted_disk_center_sets = 0.5*np.ones((N_B, N_D, 2), dtype=np.float32)

    distortion_centers = 0.5*np.ones((N_B, 2), dtype=np.float32)
    quadratic_radial_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    elliptical_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)
    spiral_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    parabolic_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)

    ml_data_dict_2 = {"cbed_pattern_images": \
                      cbed_pattern_images,
                      "disk_overlap_maps": \
                      disk_overlap_maps,
                      "disk_clipping_registries": \
                      disk_clipping_registries,
                      "disk_objectness_sets": \
                      disk_objectness_sets,
                      "common_undistorted_disk_radii": \
                      common_undistorted_disk_radii,
                      "undistorted_disk_center_sets": \
                      undistorted_disk_center_sets,
                      "distortion_centers": \
                      distortion_centers,
                      "quadratic_radial_distortion_amplitudes": \
                      quadratic_radial_distortion_amplitudes,
                      "elliptical_distortion_vectors": \
                      elliptical_distortion_vectors,
                      "spiral_distortion_amplitudes": \
                      spiral_distortion_amplitudes,
                      "parabolic_distortion_vectors": \
                      parabolic_distortion_vectors}

    return ml_data_dict_2



def generate_ml_data_dict_3():
    N_x = 32
    N_y = N_x
    mini_batch_size = 4
    max_num_disks_in_any_cbed_pattern = 6

    N_B = mini_batch_size
    N_D = max_num_disks_in_any_cbed_pattern
    
    cbed_pattern_images = np.zeros((N_B, N_y, N_x), dtype=np.float32)
    cbed_pattern_images[0, 0, 0] = 1
    cbed_pattern_images[1, 1, 0] = 1

    disk_overlap_maps = np.zeros_like(cbed_pattern_images, dtype=np.uint8)

    disk_clipping_registries = np.zeros((N_B, N_D), dtype=bool)
    disk_objectness_sets = np.zeros((N_B, N_D), dtype=np.float32)
    common_undistorted_disk_radii = np.ones((N_B,), dtype=np.float32)
    undistorted_disk_center_sets = 0.5*np.ones((N_B, N_D, 2), dtype=np.float32)

    distortion_centers = 0.5*np.ones((N_B, 2), dtype=np.float32)
    quadratic_radial_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    elliptical_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)
    spiral_distortion_amplitudes = np.ones((N_B,), dtype=np.float32)
    parabolic_distortion_vectors = 0.5*np.ones((N_B, 2), dtype=np.float32)

    ml_data_dict_3 = {"cbed_pattern_images": \
                      cbed_pattern_images,
                      "disk_overlap_maps": \
                      disk_overlap_maps,
                      "disk_clipping_registries": \
                      disk_clipping_registries,
                      "disk_objectness_sets": \
                      disk_objectness_sets,
                      "common_undistorted_disk_radii": \
                      common_undistorted_disk_radii,
                      "undistorted_disk_center_sets": \
                      undistorted_disk_center_sets,
                      "distortion_centers": \
                      distortion_centers,
                      "quadratic_radial_distortion_amplitudes": \
                      quadratic_radial_distortion_amplitudes,
                      "elliptical_distortion_vectors": \
                      elliptical_distortion_vectors,
                      "spiral_distortion_amplitudes": \
                      spiral_distortion_amplitudes,
                      "parabolic_distortion_vectors": \
                      parabolic_distortion_vectors}

    return ml_data_dict_3



def generate_normalization_weights_of_ml_data_dict_0():
    key_subset = ("common_undistorted_disk_radii",
                  "undistorted_disk_center_sets",
                  "distortion_centers",
                  "quadratic_radial_distortion_amplitudes",
                  "elliptical_distortion_vectors",
                  "spiral_distortion_amplitudes",
                  "parabolic_distortion_vectors")
    normalization_weights = {key: 1.0 for key in key_subset}

    return normalization_weights



def generate_normalization_weights_of_ml_data_dict_1():
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()

    return normalization_weights



def generate_normalization_weights_of_ml_data_dict_2():
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()

    return normalization_weights



def generate_normalization_weights_of_ml_data_dict_3():
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_weights["distortion_centers"] = 0.5

    return normalization_weights



def generate_normalization_biases_of_ml_data_dict_0():
    normalization_biases = generate_normalization_weights_of_ml_data_dict_0()
    for key in normalization_biases:
        normalization_biases[key] = 0.0

    return normalization_biases



def generate_normalization_biases_of_ml_data_dict_1():
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    return normalization_biases



def generate_normalization_biases_of_ml_data_dict_2():
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    return normalization_biases



def generate_normalization_biases_of_ml_data_dict_3():
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()
    normalization_weights = {key: 0.95*normalization_biases[key]
                             for key in
                             normalization_biases}

    return normalization_biases



def save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases):
    pathlib.Path(ml_dataset_filename).parent.mkdir(parents=True, exist_ok=True)

    with h5py.File(ml_dataset_filename, "w") as file_obj:
        for key in ml_data_dict:
            hdf5_dataset_path = key
            file_obj[hdf5_dataset_path] = ml_data_dict[key]

            if key in normalization_weights:
                file_obj[hdf5_dataset_path].attrs["normalization_weight"] = \
                    normalization_weights[key]
                file_obj[hdf5_dataset_path].attrs["normalization_bias"] = \
                    normalization_biases[key]
            
        file_obj.close()

    return None



def generate_and_save_invalid_ml_dataset_0(ml_dataset_filename):
    ml_data_dict = \
        generate_ml_data_dict_0()
    ml_data_dict["disk_overlap_maps"] = \
        ml_data_dict["disk_overlap_maps"].astype(np.float32)

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_1(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()
    ml_data_dict["disk_objectness_sets"][0, 0] = 2

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_2(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_weights["distortion_centers"] = 2.0+3.0j
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_3(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_weights["common_undistorted_disk_radii"] = -1
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_4(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()
    normalization_biases["common_undistorted_disk_radii"] = 1000

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_5(ml_dataset_filename):
    ml_data_dict = \
        generate_ml_data_dict_0()
    ml_data_dict["disk_objectness_sets"] = \
        ml_data_dict["disk_objectness_sets"][:, 0]

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_6(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()
    N_B, N_D = ml_data_dict["disk_objectness_sets"].shape
    ml_data_dict["disk_objectness_sets"] = np.zeros((2*N_B, N_D),
                                                    dtype=np.float32)

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_7(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()
    N_B = ml_data_dict["distortion_centers"].shape[0]
    ml_data_dict["distortion_centers"] = 0.5*np.ones((N_B, 3), dtype=np.float32)

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_invalid_ml_dataset_8(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()
    ml_data_dict["cbed_pattern_images"][0, 0, 0] = 2

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_valid_ml_dataset_0(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_0()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_valid_ml_dataset_1(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_1()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_1()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_1()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_valid_ml_dataset_2(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_2()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_2()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_2()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_and_save_valid_ml_dataset_3(ml_dataset_filename):
    ml_data_dict = generate_ml_data_dict_3()

    normalization_weights = generate_normalization_weights_of_ml_data_dict_3()
    
    normalization_biases = generate_normalization_biases_of_ml_data_dict_3()

    save_ml_dataset(ml_dataset_filename,
                    ml_data_dict,
                    normalization_weights,
                    normalization_biases)

    return None



def generate_ml_dataset_manager_0():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_training_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_2(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_training_dataset = module_alias.MLDataset(**kwargs)

    kwargs = {"ml_training_dataset": ml_training_dataset,
              "mini_batch_size": 2}
    ml_dataset_manager_0 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_0



def generate_ml_dataset_manager_1():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_training_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_2(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_training_dataset = module_alias.MLDataset(**kwargs)

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_validation_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_0(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_validation_dataset = module_alias.MLDataset(**kwargs)

    kwargs = {"ml_training_dataset": ml_training_dataset,
              "ml_validation_dataset": ml_validation_dataset,
              "mini_batch_size": 2}
    ml_dataset_manager_1 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_1



def generate_ml_dataset_manager_2():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_training_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_2(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_training_dataset = module_alias.MLDataset(**kwargs)

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_validation_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_0(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_validation_dataset = module_alias.MLDataset(**kwargs)

    ml_testing_dataset = ml_validation_dataset

    kwargs = {"ml_training_dataset": ml_training_dataset,
              "ml_validation_dataset": ml_validation_dataset,
              "ml_testing_dataset": ml_testing_dataset}
    ml_dataset_manager_2 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_2



def generate_ml_dataset_manager_3():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_training_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_3(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_training_dataset = module_alias.MLDataset(**kwargs)

    kwargs = {"ml_training_dataset": ml_training_dataset}
    ml_dataset_manager_3 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_3



def generate_ml_dataset_manager_4():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_training_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_3(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_training_dataset = module_alias.MLDataset(**kwargs)

    kwargs = {"ml_training_dataset": ml_training_dataset,
              "ml_validation_dataset": ml_training_dataset,
              "ml_testing_dataset": ml_training_dataset,
              "rng_seed": 0}
    ml_dataset_manager_4 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_4



def generate_ml_dataset_manager_5():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_testing_dataset.h5")

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_3(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_testing_dataset = module_alias.MLDataset(**kwargs)

    kwargs = {"ml_testing_dataset": ml_testing_dataset}
    ml_dataset_manager_5 = module_alias.MLDatasetManager(**kwargs)

    return ml_dataset_manager_5



def generate_ml_model_0():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.MLModel

    N_x = 32

    kwargs = {"num_pixels_across_each_cbed_pattern": N_x,
              "max_num_disks_in_any_cbed_pattern": 8,
              "architecture": "distoptica_net"}
    ml_model_0 = module_alias.MLModel(**kwargs)

    return ml_model_0



def generate_ml_optimizer_0():
    module_alias = emicroml.modelling.optimizers

    ml_optimizer_params = {"base_lr": 5e-3,
                           "weight_decay": 7.25e-4,
                           "momentum_factor": 0.9}

    kwargs = {"ml_optimizer_name": "sgd",
              "ml_optimizer_params": ml_optimizer_params}
    ml_optimizer_0 = emicroml.modelling.optimizers.Generic(**kwargs)

    return ml_optimizer_0



def generate_ml_optimizer_1():
    module_alias = emicroml.modelling.optimizers

    ml_optimizer_params = dict()

    kwargs = {"ml_optimizer_name": "adam_w",
              "ml_optimizer_params": ml_optimizer_params}
    ml_optimizer_1 = emicroml.modelling.optimizers.Generic(**kwargs)

    return ml_optimizer_1



def generate_lr_scheduler_manager_0():
    lr_scheduler_params = {"ml_optimizer": generate_ml_optimizer_0(),
                           "total_num_steps": 4,
                           "scale_factor": 1}

    kwargs = {"lr_scheduler_name": "constant",
              "lr_scheduler_params": lr_scheduler_params}
    generic_lr_scheduler = emicroml.modelling.lr.schedulers.Generic(**kwargs)

    kwargs = {"lr_schedulers": (generic_lr_scheduler,),
              "phase_in_which_to_update_lr": "training"}
    lr_scheduler_manager_0 = emicroml.modelling.lr.LRSchedulerManager(**kwargs)

    return lr_scheduler_manager_0



def generate_lr_scheduler_manager_1():
    lr_scheduler_params = {"ml_optimizer": generate_ml_optimizer_0(),
                           "total_num_steps": 1,
                           "scale_factor": 1}

    kwargs = {"lr_scheduler_name": "constant",
              "lr_scheduler_params": lr_scheduler_params}
    generic_lr_scheduler = emicroml.modelling.lr.schedulers.Generic(**kwargs)

    kwargs = {"lr_schedulers": (generic_lr_scheduler,),
              "phase_in_which_to_update_lr": "validation"}
    lr_scheduler_manager_1 = emicroml.modelling.lr.LRSchedulerManager(**kwargs)

    return lr_scheduler_manager_1



def generate_lr_scheduler_manager_2():
    lr_scheduler_params = {"ml_optimizer": generate_ml_optimizer_1(),
                           "total_num_steps": 0,
                           "scale_factor": 1}

    kwargs = {"lr_scheduler_name": "constant",
              "lr_scheduler_params": lr_scheduler_params}
    generic_lr_scheduler = emicroml.modelling.lr.schedulers.Generic(**kwargs)

    kwargs = {"lr_schedulers": (generic_lr_scheduler,),
              "phase_in_which_to_update_lr": "training"}
    lr_scheduler_manager_2 = emicroml.modelling.lr.LRSchedulerManager(**kwargs)

    _ = lr_scheduler_manager_2.total_num_steps
    
    new_core_attr_subset_candidate = {"phase_in_which_to_update_lr": \
                                      "validation"}
    lr_scheduler_manager_2.update(new_core_attr_subset_candidate)

    return lr_scheduler_manager_2



def generate_lr_scheduler_manager_3():
    lr_scheduler_params = {"ml_optimizer": generate_ml_optimizer_1(),
                           "total_num_steps": 3,
                           "num_steps_in_first_cycle": 2,
                           "cycle_period_scale_factor": 1,
                           "min_lr_in_first_cycle": 1e-8,
                           "multiplicative_decay_factor": 2}

    kwargs = \
        {"lr_scheduler_name": "cosine_annealing_with_warm_restarts",
         "lr_scheduler_params": lr_scheduler_params}
    non_sequential_lr_scheduler_0 = \
        emicroml.modelling.lr.schedulers.Nonsequential(**kwargs)

    lr_scheduler_params = {"ml_optimizer": lr_scheduler_params["ml_optimizer"],
                           "total_num_steps": 2}

    kwargs = \
        {"lr_scheduler_name": "constant",
         "lr_scheduler_params": lr_scheduler_params}
    non_sequential_lr_scheduler_1 = \
        emicroml.modelling.lr.schedulers.Nonsequential(**kwargs)

    non_sequential_lr_schedulers = (non_sequential_lr_scheduler_0,
                                    non_sequential_lr_scheduler_1)

    lr_scheduler_params = {"non_sequential_lr_schedulers": \
                           non_sequential_lr_schedulers}

    kwargs = {"lr_scheduler_name": "sequential",
              "lr_scheduler_params": lr_scheduler_params}
    generic_lr_scheduler = emicroml.modelling.lr.schedulers.Generic(**kwargs)

    kwargs = {"lr_schedulers": (generic_lr_scheduler,),
              "phase_in_which_to_update_lr": "training"}
    lr_scheduler_manager_3 = emicroml.modelling.lr.LRSchedulerManager(**kwargs)

    return lr_scheduler_manager_3



def generate_lr_scheduler_name_set_0():
    lr_scheduler_name_set_0 = ("constant",
                               "linear",
                               "exponential",
                               "reduce_on_plateau")

    return lr_scheduler_name_set_0



def test_1_of_DefaultDistortionModelGenerator():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultDistortionModelGenerator

    kwargs = generate_default_distortion_model_generator_1_ctor_params()
    distortion_model_generator = cls_alias(**kwargs)

    distortion_model_generator.validation_and_conversion_funcs
    distortion_model_generator.pre_serialization_funcs
    distortion_model_generator.de_pre_serialization_funcs

    kwargs = {"serializable_rep": distortion_model_generator.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    distortion_model_generator.generate()

    new_core_attr_subset_candidate = {"sampling_grid_dims_in_pixels": (50, 45)}
    distortion_model_generator.update(new_core_attr_subset_candidate)

    return None



def test_2_of_DefaultDistortionModelGenerator():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultDistortionModelGenerator

    kwargs = generate_default_distortion_model_generator_2_ctor_params()
    distortion_model_generator = cls_alias(**kwargs)

    with pytest.raises(RuntimeError) as err_info:
        distortion_model_generator.generate()

    return None



def test_1_of_DefaultCBEDPatternGenerator():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultCBEDPatternGenerator

    kwargs = generate_default_cbed_pattern_generator_1_ctor_params()
    cbed_pattern_generator = cls_alias(**kwargs)

    cbed_pattern_generator.validation_and_conversion_funcs
    cbed_pattern_generator.pre_serialization_funcs
    cbed_pattern_generator.de_pre_serialization_funcs

    kwargs = {"serializable_rep": cbed_pattern_generator.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    for _ in range(2):
        cbed_pattern_generator.generate()

    new_core_attr_subset_candidate = {"rng_seed": 27}
    cbed_pattern_generator.update(new_core_attr_subset_candidate)

    cbed_pattern_generator.generate()

    new_core_attr_subset_candidate = {"max_num_disks_in_any_cbed_pattern": 4,
                                      "rng_seed": 0}
    cbed_pattern_generator.update(new_core_attr_subset_candidate)

    with pytest.raises(RuntimeError) as err_info:
        cbed_pattern_generator.generate()

    with pytest.raises(ValueError) as err_info:
        new_core_attr_subset_candidate = \
            {"num_pixels_across_each_cbed_pattern": 7}
        _ = \
            cbed_pattern_generator.update(new_core_attr_subset_candidate)

    return None



def test_1_of_generate_and_save_ml_dataset():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultCBEDPatternGenerator

    kwargs = generate_default_cbed_pattern_generator_2_ctor_params()
    valid_cbed_pattern_generator_1 = cls_alias(**kwargs)

    invalid_cbed_pattern_generator_1 = InvalidCBEDPatternGenerator1()
    invalid_cbed_pattern_generator_2 = InvalidCBEDPatternGenerator2(**kwargs)
    invalid_cbed_pattern_generator_3 = InvalidCBEDPatternGenerator3(**kwargs)
    invalid_cbed_pattern_generator_4 = InvalidCBEDPatternGenerator4(**kwargs)
    invalid_cbed_pattern_generator_5 = InvalidCBEDPatternGenerator5(**kwargs)

    output_filename = "./test_data/modelling/cbed/distortion/ml_dataset.h5"

    kwargs = {"num_cbed_patterns": 4,
              "max_num_disks_in_any_cbed_pattern": 90,
              "cbed_pattern_generator": valid_cbed_pattern_generator_1,
              "output_filename": output_filename,
              "max_num_ml_data_instances_per_file_update": 3}
    module_alias.generate_and_save_ml_dataset(**kwargs)

    error_cls_set = (RuntimeError, TypeError) + 4*(ValueError,) + (IOError,)
    
    cbed_pattern_generator_candidate_set = (2,
                                            invalid_cbed_pattern_generator_1,
                                            valid_cbed_pattern_generator_1,
                                            invalid_cbed_pattern_generator_2,
                                            invalid_cbed_pattern_generator_3,
                                            invalid_cbed_pattern_generator_4,
                                            invalid_cbed_pattern_generator_5)

    max_num_disks_in_any_cbed_pattern_set = 2*(90,) + (1,) + 4*(90,)

    num_iterations = len(error_cls_set)
    
    for iteration_idx in range(num_iterations):
        with pytest.raises(error_cls_set[iteration_idx]) as err_info:
            kwargs["cbed_pattern_generator"] = \
                cbed_pattern_generator_candidate_set[iteration_idx]
            kwargs["max_num_disks_in_any_cbed_pattern"] = \
                max_num_disks_in_any_cbed_pattern_set[iteration_idx]
            _ = \
                module_alias.generate_and_save_ml_dataset(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_generate_and_save_ml_dataset():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultCBEDPatternGenerator

    kwargs = generate_default_cbed_pattern_generator_2_ctor_params()
    valid_cbed_pattern_generator_1 = cls_alias(**kwargs)

    output_filename = "./test_data/modelling/cbed/distortion/ml_dataset.h5"

    path_to_test_data = generate_path_to_test_data()
    pathlib.Path(path_to_test_data).mkdir(parents=True, exist_ok=True)
    os.chmod(path_to_test_data, 0o111)

    with pytest.raises(IOError) as err_info:
        kwargs = {"num_cbed_patterns": 4,
                  "max_num_disks_in_any_cbed_pattern": 90,
                  "cbed_pattern_generator": valid_cbed_pattern_generator_1,
                  "output_filename": output_filename,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.generate_and_save_ml_dataset(**kwargs)

    os.chmod(path_to_test_data, 0o711)

    kwargs = {"num_cbed_patterns": 1,
              "max_num_disks_in_any_cbed_pattern": 90,
              "cbed_pattern_generator": None,
              "output_filename": output_filename,
              "max_num_ml_data_instances_per_file_update": 3}
    module_alias.generate_and_save_ml_dataset(**kwargs)

    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_combine_ml_dataset_files():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    cls_alias = module_alias.DefaultCBEDPatternGenerator

    kwargs = generate_default_cbed_pattern_generator_1_ctor_params()
    valid_cbed_pattern_generator_1 = cls_alias(**kwargs)

    input_ml_dataset_filenames = tuple()
    for ml_dataset_idx in range(2):
        output_filename = ("./test_data/modelling/cbed/distortion"
                           "/ml_dataset_{}.h5").format(ml_dataset_idx)
        input_ml_dataset_filenames += (output_filename,)

        kwargs = {"num_cbed_patterns": 2,
                  "max_num_disks_in_any_cbed_pattern": 90,
                  "cbed_pattern_generator": valid_cbed_pattern_generator_1,
                  "output_filename": output_filename,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.generate_and_save_ml_dataset(**kwargs)

    output_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                  "/ml_dataset.h5")

    for rm_input_ml_dataset_files in (False, True):
        kwargs = {"input_ml_dataset_filenames": input_ml_dataset_filenames,
                  "output_ml_dataset_filename": output_ml_dataset_filename,
                  "rm_input_ml_dataset_files": rm_input_ml_dataset_files,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.combine_ml_dataset_files(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_combine_ml_dataset_files():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    input_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                 "/invalid_ml_dataset.h5")
    input_ml_dataset_filenames = (input_ml_dataset_filename,)

    output_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                  "/ml_dataset.h5")

    error_cls_set = (2*(OSError,)
                     + (TypeError,)
                     + 2*(ValueError,)
                     + 4*(OSError,))
    num_invalid_ml_dataset_to_generate = len(error_cls_set)
    
    for ml_dataset_idx in range(num_invalid_ml_dataset_to_generate):
        func_name = ("generate_"
                     "and_save_invalid_ml_dataset_{}".format(ml_dataset_idx))
        func_alias = globals()[func_name]
        kwargs = {"ml_dataset_filename": input_ml_dataset_filename}
        func_alias(**kwargs)
        
        with pytest.raises(error_cls_set[ml_dataset_idx]) as err_info:
            kwargs = {"input_ml_dataset_filenames": input_ml_dataset_filenames,
                      "output_ml_dataset_filename": output_ml_dataset_filename,
                      "rm_input_ml_dataset_files": True,
                      "max_num_ml_data_instances_per_file_update": 3}
            module_alias.combine_ml_dataset_files(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_3_of_combine_ml_dataset_files():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    input_ml_dataset_filename_0 = ("./test_data/modelling/cbed/distortion"
                                   "/ml_dataset_0.h5")
    input_ml_dataset_filename_1 = ("./test_data/modelling/cbed/distortion"
                                   "/ml_dataset_1.h5")
    input_ml_dataset_filenames = (input_ml_dataset_filename_0,
                                  input_ml_dataset_filename_1)

    output_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                  "/combined_ml_dataset.h5")

    num_valid_ml_datasets_to_generate = len(input_ml_dataset_filenames)
    for ml_dataset_idx in range(num_valid_ml_datasets_to_generate):
        func_name = ("generate_"
                     "and_save_valid_ml_dataset_{}".format(ml_dataset_idx))
        func_alias = globals()[func_name]
        kwargs = {"ml_dataset_filename": \
                  input_ml_dataset_filenames[ml_dataset_idx]}
        func_alias(**kwargs)
        
    with pytest.raises(OSError) as err_info:
        kwargs = {"input_ml_dataset_filenames": input_ml_dataset_filenames,
                  "output_ml_dataset_filename": output_ml_dataset_filename,
                  "rm_input_ml_dataset_files": True,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.combine_ml_dataset_files(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"input_ml_dataset_filenames": tuple(),
                  "output_ml_dataset_filename": output_ml_dataset_filename,
                  "rm_input_ml_dataset_files": True,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.combine_ml_dataset_files(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_normalize_normalizable_elems_in_ml_data_dict():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    func_alias = module_alias.normalize_normalizable_elems_in_ml_data_dict

    ml_data_dict = generate_ml_data_dict_0()
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    for check_ml_data_dict_first in (True, False):
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": normalization_weights,
                  "normalization_biases": normalization_biases,
                  "check_ml_data_dict_first": check_ml_data_dict_first}
        _ = func_alias(**kwargs)

    kwargs = {"ml_data_dict": ml_data_dict,
              "normalization_weights": None,
              "normalization_biases": None,
              "check_ml_data_dict_first": False}
    _ = func_alias(**kwargs)
    
    return None



def test_2_of_normalize_normalizable_elems_in_ml_data_dict():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    func_alias = module_alias.normalize_normalizable_elems_in_ml_data_dict

    ml_data_dict = generate_ml_data_dict_0()
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    with pytest.raises(TypeError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": 2,
                  "normalization_biases": normalization_biases,
                  "check_ml_data_dict_first": False}
        _ = func_alias(**kwargs)

    with pytest.raises(TypeError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": normalization_weights,
                  "normalization_biases": 2,
                  "check_ml_data_dict_first": False}
        _ = func_alias(**kwargs)

    with pytest.raises(KeyError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": dict(),
                  "normalization_biases": normalization_biases,
                  "check_ml_data_dict_first": False}
        _ = func_alias(**kwargs)

    with pytest.raises(KeyError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": normalization_weights,
                  "normalization_biases": dict(),
                  "check_ml_data_dict_first": False}
        _ = func_alias(**kwargs)

    kwargs = {"ml_data_dict": {"distortion_centers": None},
              "normalization_weights": normalization_weights,
              "normalization_biases": normalization_biases,
              "check_ml_data_dict_first": False}
    _ = func_alias(**kwargs)
    
    return None



def test_3_of_normalize_normalizable_elems_in_ml_data_dict():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    func_alias = module_alias.normalize_normalizable_elems_in_ml_data_dict

    ml_data_dict = generate_ml_data_dict_0()
    N_B, N_D = ml_data_dict["disk_objectness_sets"].shape
    ml_data_dict["disk_objectness_sets"] = np.zeros((N_B, N_D, N_D),
                                                    dtype=np.float32)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": None,
                  "normalization_biases": None,
                  "check_ml_data_dict_first": True}
        _ = func_alias(**kwargs)

    ml_data_dict = generate_ml_data_dict_0()
    N_B = ml_data_dict["distortion_centers"].shape[0]
    ml_data_dict["distortion_centers"] = 0.5*np.ones((N_B, 3), dtype=np.float32)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": None,
                  "normalization_biases": None,
                  "check_ml_data_dict_first": True}
        _ = func_alias(**kwargs)
    
    return None



def test_1_of_unnormalize_normalizable_elems_in_ml_data_dict():
    module_alias = emicroml.modelling.cbed.distortion.estimation
    func_alias = module_alias.unnormalize_normalizable_elems_in_ml_data_dict

    ml_data_dict = generate_ml_data_dict_0()
    normalization_weights = generate_normalization_weights_of_ml_data_dict_0()
    normalization_biases = generate_normalization_biases_of_ml_data_dict_0()

    for check_ml_data_dict_first in (True, False):
        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": None,
                  "normalization_biases": None,
                  "check_ml_data_dict_first": check_ml_data_dict_first}
        _ = func_alias(**kwargs)

    kwargs = {"ml_data_dict": {"distortion_centers": None},
              "normalization_weights": None,
              "normalization_biases": None,
              "check_ml_data_dict_first": False}
    _ = func_alias(**kwargs)
    
    return None



def test_1_of_split_ml_dataset_file():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    input_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                 "/ml_dataset_to_split.h5")

    output_ml_dataset_filename_1 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_training.h5")
    output_ml_dataset_filename_2 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_validation.h5")
    output_ml_dataset_filename_3 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_testing.h5")

    for enable_shuffling in (True, False):
        for rm_input_ml_dataset_file in (True, False):
            kwargs = {"ml_dataset_filename": input_ml_dataset_filename}
            generate_and_save_valid_ml_dataset_0(**kwargs)

            kwargs = {"input_ml_dataset_filename": \
                      input_ml_dataset_filename,
                      "output_ml_dataset_filename_1": \
                      output_ml_dataset_filename_1,
                      "output_ml_dataset_filename_2": \
                      output_ml_dataset_filename_2,
                      "output_ml_dataset_filename_3": \
                      output_ml_dataset_filename_3,
                      "split_ratio": \
                      (0.8, 0.2, 0),
                      "enable_shuffling": \
                      enable_shuffling,
                      "rm_input_ml_dataset_file": \
                      rm_input_ml_dataset_file,
                      "max_num_ml_data_instances_per_file_update": \
                      3}
            module_alias.split_ml_dataset_file(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_split_ml_dataset_file():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    input_ml_dataset_filename = ("./test_data/modelling/cbed/distortion"
                                 "/ml_dataset_to_split.h5")

    output_ml_dataset_filename_1 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_training.h5")
    output_ml_dataset_filename_2 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_validation.h5")
    output_ml_dataset_filename_3 = ("./test_data/modelling/cbed/distortion"
                                    "/ml_dataset_for_testing.h5")

    kwargs = {"ml_dataset_filename": input_ml_dataset_filename}
    generate_and_save_invalid_ml_dataset_0(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"input_ml_dataset_filename": input_ml_dataset_filename,
                  "output_ml_dataset_filename_1": output_ml_dataset_filename_1,
                  "output_ml_dataset_filename_2": output_ml_dataset_filename_1,
                  "output_ml_dataset_filename_3": output_ml_dataset_filename_3,
                  "split_ratio": (0.8, 0.2, 0),
                  "enable_shuffling": False,
                  "rm_input_ml_dataset_file": False,
                  "max_num_ml_data_instances_per_file_update": 3}
        module_alias.split_ml_dataset_file(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs["output_ml_dataset_filename_2"] = output_ml_dataset_filename_2
        kwargs["output_ml_dataset_filename_3"] = output_ml_dataset_filename_2
        module_alias.split_ml_dataset_file(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs["output_ml_dataset_filename_3"] = output_ml_dataset_filename_3
        kwargs["split_ratio"] = 4*(0.2,)
        module_alias.split_ml_dataset_file(**kwargs)

    with pytest.raises(IOError) as err_info:
        kwargs["split_ratio"] = (0.8, 0.2, 0)
        module_alias.split_ml_dataset_file(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_ml_data_dict_to_distortion_models():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_data_dict = generate_ml_data_dict_0()

    kwargs = {"ml_data_dict": ml_data_dict,
              "sampling_grid_dims_in_pixels": (8, 8),
              "device_name": "cpu",
              "least_squares_alg_params": None}
    _ = module_alias.ml_data_dict_to_distortion_models(**kwargs)

    del ml_data_dict["distortion_centers"]

    with pytest.raises(KeyError) as err_info:
        _ = module_alias.ml_data_dict_to_distortion_models(**kwargs)

    ml_data_dict = generate_ml_data_dict_0()
    ml_data_dict["foobar"] = None

    with pytest.raises(KeyError) as err_info:
        kwargs["ml_data_dict"] = ml_data_dict
        _ = module_alias.ml_data_dict_to_distortion_models(**kwargs)

    del ml_data_dict["foobar"]
    disk_clipping_registries = ml_data_dict["disk_clipping_registries"]
    ml_data_dict["disk_clipping_registries"] = disk_clipping_registries.tolist()

    _ = module_alias.ml_data_dict_to_distortion_models(**kwargs)

    ml_data_dict["disk_clipping_registries"] = [[True], [True, False]]

    with pytest.raises(TypeError) as err_info:
        _ = module_alias.ml_data_dict_to_distortion_models(**kwargs)

    return None



def test_1_of_ml_data_dict_to_signals():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_data_dict = generate_ml_data_dict_0()
    ml_data_dict["disk_objectness_sets"][0, 0] = 1

    N_x = ml_data_dict["cbed_pattern_images"].shape[-1]

    kwargs = {"ml_data_dict": ml_data_dict,
              "sampling_grid_dims_in_pixels": (N_x, N_x),
              "device_name": "cpu",
              "least_squares_alg_params": None}
    _ = module_alias.ml_data_dict_to_signals(**kwargs)

    del ml_data_dict["distortion_centers"]
    del ml_data_dict["disk_overlap_maps"]
    del ml_data_dict["common_undistorted_disk_radii"]

    _ = module_alias.ml_data_dict_to_signals(**kwargs)

    ml_data_dict["cbed_pattern_images"] = \
        np.expand_dims(ml_data_dict["cbed_pattern_images"], axis=0)

    with pytest.raises(ValueError) as err_info:
        _ = module_alias.ml_data_dict_to_signals(**kwargs)

    return None



def test_1_of_MLDataset():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = "./test_data/modelling/cbed/distortion/ml_dataset.h5"

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_2(**kwargs)

    for entire_ml_dataset_is_to_be_cached in (True, False):
        for ml_data_values_are_to_be_checked in (True, False):
            for max_num_ml_data_instances_per_chunk in (3, float("inf")):
                kwargs = {"path_to_ml_dataset": \
                          path_to_ml_dataset,
                          "entire_ml_dataset_is_to_be_cached": \
                          entire_ml_dataset_is_to_be_cached,
                          "ml_data_values_are_to_be_checked": \
                          ml_data_values_are_to_be_checked,
                          "max_num_ml_data_instances_per_chunk": \
                          max_num_ml_data_instances_per_chunk,
                          "skip_validation_and_conversion": \
                          False}
                ml_dataset = module_alias.MLDataset(**kwargs)

                for decode in (True, False):
                    for unnormalize_normalizable_elems in (True, False):
                        kwargs = {"single_dim_slice": \
                                  slice(None),
                                  "device_name": \
                                  None,
                                  "decode": \
                                  decode,
                                  "unnormalize_normalizable_elems": \
                                  unnormalize_normalizable_elems}
                        _ = ml_dataset.get_ml_data_instances(**kwargs)

    ml_dataset.validation_and_conversion_funcs
    ml_dataset.pre_serialization_funcs
    ml_dataset.de_pre_serialization_funcs

    kwargs = {"serializable_rep": ml_dataset.pre_serialize()}
    module_alias.MLDataset.de_pre_serialize(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"single_dim_slice": -(len(ml_dataset)+1)}
        ml_dataset.get_ml_data_instances(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_MLDataset():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    path_to_ml_dataset = "./test_data/modelling/cbed/distortion/ml_dataset.h5"

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_2(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": False,
              "ml_data_values_are_to_be_checked": False,
              "max_num_ml_data_instances_per_chunk": 3,
              "skip_validation_and_conversion": False}
    ml_dataset = module_alias.MLDataset(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"single_dim_slice": slice(None),
                  "device_name": "foobar",
                  "decode": False,
                  "unnormalize_normalizable_elems": False}
        _ = ml_dataset.get_ml_data_instances(**kwargs)

    new_core_attr_subset_candidate = {"entire_ml_dataset_is_to_be_cached": True}
    ml_dataset.update(new_core_attr_subset_candidate)

    ml_dataset.normalization_weights
    ml_dataset.normalization_biases
    ml_dataset.num_pixels_across_each_cbed_pattern
    ml_dataset.max_num_disks_in_any_cbed_pattern

    ml_data_instance = ml_dataset[0]
    N_x = ml_data_instance["cbed_pattern_images"].shape[-1]

    kwargs = {"single_dim_slice": 0,
              "sampling_grid_dims_in_pixels": (N_x, N_x)}
    _ = ml_dataset.get_ml_data_instances_as_signals(**kwargs)

    ml_dataset_manager = generate_ml_dataset_manager_1()

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_MLDatasetManager():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()

    path_to_ml_dataset = ("./test_data/modelling/cbed"
                          "/distortion/ml_validation_dataset.h5")

    ml_dataset_manager.validation_and_conversion_funcs
    ml_dataset_manager.pre_serialization_funcs
    ml_dataset_manager.de_pre_serialization_funcs

    kwargs = {"serializable_rep": ml_dataset_manager.pre_serialize()}
    module_alias.MLDatasetManager.de_pre_serialize(**kwargs)

    kwargs = {"ml_dataset_filename": path_to_ml_dataset}
    generate_and_save_valid_ml_dataset_3(**kwargs)

    kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
              "entire_ml_dataset_is_to_be_cached": True,
              "ml_data_values_are_to_be_checked": False}
    ml_validation_dataset = module_alias.MLDataset(**kwargs)

    with pytest.raises(ValueError) as err_info:
        new_core_attr_subset_candidate = {"ml_validation_dataset": \
                                          ml_validation_dataset}
        ml_dataset_manager.update(new_core_attr_subset_candidate)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_MLDatasetManager():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()

    ml_training_dataset = \
        ml_dataset_manager.get_core_attrs()["ml_training_dataset"]

    new_core_attr_subset_candidate = {"ml_validation_dataset": \
                                      ml_training_dataset}
    ml_dataset_manager.update(new_core_attr_subset_candidate)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_MLModel():
    ml_model = generate_ml_model_0()

    N_x = 32

    ml_model.eval()

    cbed_pattern_images = np.zeros((1, N_x, N_x), dtype=np.float32)
    cbed_pattern_images[0, 0, 0] = 1

    for unnormalize_normalizable_elems_of_ml_predictions in (True, False):
        kwargs = {"ml_inputs": \
                  {"cbed_pattern_images": cbed_pattern_images},
                  "unnormalize_normalizable_elems_of_ml_predictions": \
                  unnormalize_normalizable_elems_of_ml_predictions}
        _ = ml_model.make_predictions(**kwargs)

    with pytest.raises(TypeError) as err_info:
        kwargs["ml_inputs"] = {"cbed_pattern_images": np.array(None)}
        _ = ml_model.make_predictions(**kwargs)

    kwargs = {"cbed_pattern_images": cbed_pattern_images,
              "sampling_grid_dims_in_pixels": (N_x//2, N_x//2),
              "least_squares_alg_params": None}
    _ = ml_model.predict_distortion_models(**kwargs)

    ml_model.get_core_attrs(deep_copy=False)
    ml_model.get_core_attrs(deep_copy=True)

    return None



def test_1_of_MLModelTrainer():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()
    output_dirname = "./test_data/modelling/cbed/distortion"

    kwargs = {"ml_dataset_manager": ml_dataset_manager,
              "output_dirname": output_dirname}
    ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

    ml_model_trainer.validation_and_conversion_funcs
    ml_model_trainer.pre_serialization_funcs
    ml_model_trainer.de_pre_serialization_funcs

    new_core_attr_subset_candidate = {"checkpoints": (0,)}
    ml_model_trainer.update(new_core_attr_subset_candidate)

    with pytest.raises(ValueError) as err_info:
        new_core_attr_subset_candidate = {"checkpoints": (-1,)}
        ml_model_trainer.update(new_core_attr_subset_candidate)

    with pytest.raises(ValueError) as err_info:
        new_core_attr_subset_candidate = {"misc_model_training_metadata": \
                                          {"foobar": slice(None)}}
        ml_model_trainer.update(new_core_attr_subset_candidate)

    new_core_attr_subset_candidate = {"lr_scheduler_manager": \
                                      generate_lr_scheduler_manager_0()}
    ml_model_trainer.update(new_core_attr_subset_candidate)

    kwargs = {"serializable_rep": ml_model_trainer.pre_serialize()}
    module_alias.MLModelTrainer.de_pre_serialize(**kwargs)

    ml_model = generate_ml_model_0()

    kwargs = {"ml_model": ml_model,
              "ml_model_param_groups": (ml_model.parameters(),)}
    ml_model_trainer.train_ml_model(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_2_of_MLModelTrainer():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    for iteration_idx in range(3):
        func_name = "generate_ml_dataset_manager_{}".format(iteration_idx+3)
        func_alias = globals()[func_name]
        ml_dataset_manager = func_alias()
        
        lr_scheduler_manager = generate_lr_scheduler_manager_0()
        
        output_dirname = "./test_data/modelling/cbed/distortion"

        if iteration_idx < 2:
            kwargs = {"ml_dataset_manager": ml_dataset_manager,
                      "lr_scheduler_manager": lr_scheduler_manager,
                      "output_dirname": output_dirname,
                      "checkpoints": tuple()}
            ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

            ml_model = generate_ml_model_0()
            ml_model_param_groups = (ml_model.parameters(),)

            kwargs = {"ml_model": ml_model,
                      "ml_model_param_groups": ml_model_param_groups}
            ml_model_trainer.train_ml_model(**kwargs)
        else:
            with pytest.raises(ValueError) as err_info:
                kwargs = {"ml_dataset_manager": ml_dataset_manager}
                ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_3_of_MLModelTrainer():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()
    lr_scheduler_manager = generate_lr_scheduler_manager_1()
    output_dirname = "./test_data/modelling/cbed/distortion"

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_dataset_manager": ml_dataset_manager,
                  "lr_scheduler_manager": lr_scheduler_manager,
                  "output_dirname": output_dirname,
                  "checkpoints": (0,)}
        ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

    kwargs["ml_dataset_manager"] = generate_ml_dataset_manager_4()
    ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

    ml_model = generate_ml_model_0()
    ml_model_param_groups = (ml_model.parameters(), ml_model.parameters())

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_model": ml_model,
                  "ml_model_param_groups": ml_model_param_groups}
        ml_model_trainer.train_ml_model(**kwargs)

    ml_model_param_groups = (ml_model.parameters(),)
    kwargs["ml_model_param_groups"] = ml_model_param_groups
    ml_model_trainer.train_ml_model(**kwargs)

    for checkpoint in (0, 1):
        new_core_attr_subset_candidate = {"ml_dataset_manager": \
                                          generate_ml_dataset_manager_3(),
                                          "lr_scheduler_manager": \
                                          generate_lr_scheduler_manager_2(),
                                          "checkpoints": \
                                          (checkpoint,)}
        ml_model_trainer.update(new_core_attr_subset_candidate)

        ml_model = generate_ml_model_0()
        ml_model_param_groups = (ml_model.parameters(),)

        kwargs = {"ml_model": ml_model,
                  "ml_model_param_groups": ml_model_param_groups}
        ml_model_trainer.train_ml_model(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_4_of_MLModelTrainer():
    module_alias_1 = emicroml.modelling.lr.schedulers
    module_alias_2 = emicroml.modelling.lr
    module_alias_3 = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()
    output_dirname = "./test_data/modelling/cbed/distortion"

    lr_scheduler_name_set = generate_lr_scheduler_name_set_0()

    for lr_scheduler_name in lr_scheduler_name_set:
        lr_scheduler_params = {"ml_optimizer": generate_ml_optimizer_1(),
                               "total_num_steps": 0}

        kwargs = {"lr_scheduler_name": lr_scheduler_name,
                  "lr_scheduler_params": lr_scheduler_params}
        generic_lr_scheduler = module_alias_1.Generic(**kwargs)

        kwargs = {"lr_schedulers": (generic_lr_scheduler,),
                  "phase_in_which_to_update_lr": "training"}
        lr_scheduler_manager = module_alias_2.LRSchedulerManager(**kwargs)

        kwargs = {"ml_dataset_manager": ml_dataset_manager,
                  "lr_scheduler_manager": lr_scheduler_manager,
                  "output_dirname": output_dirname,
                  "checkpoints": tuple()}
        ml_model_trainer = module_alias_3.MLModelTrainer(**kwargs)

        ml_model = generate_ml_model_0()
        ml_model_param_groups = (ml_model.parameters(),)

        kwargs = {"ml_model": ml_model,
                  "ml_model_param_groups": ml_model_param_groups}
        ml_model_trainer.train_ml_model(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_5_of_MLModelTrainer():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_0()
    lr_scheduler_manager = generate_lr_scheduler_manager_3()
    output_dirname = "./test_data/modelling/cbed/distortion"

    kwargs = {"ml_dataset_manager": ml_dataset_manager,
              "lr_scheduler_manager": lr_scheduler_manager,
              "output_dirname": output_dirname,
              "checkpoints": tuple()}
    ml_model_trainer = module_alias.MLModelTrainer(**kwargs)

    ml_model = generate_ml_model_0()
    ml_model_param_groups = (ml_model.parameters(),)

    kwargs = {"ml_model": ml_model,
              "ml_model_param_groups": ml_model_param_groups}
    ml_model_trainer.train_ml_model(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_MLModelTester():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_dataset_manager = generate_ml_dataset_manager_2()
    output_dirname = "./test_data/modelling/cbed/distortion"

    kwargs = {"ml_dataset_manager": ml_dataset_manager,
              "output_dirname": output_dirname}
    ml_model_tester = module_alias.MLModelTester(**kwargs)

    ml_model_tester.validation_and_conversion_funcs
    ml_model_tester.pre_serialization_funcs
    ml_model_tester.de_pre_serialization_funcs

    kwargs = {"serializable_rep": ml_model_tester.pre_serialize()}
    module_alias.MLModelTester.de_pre_serialize(**kwargs)

    with pytest.raises(ValueError) as err_info:
        new_core_attr_subset_candidate = {"misc_model_testing_metadata": \
                                          {"foobar": slice(None)}}
        ml_model_tester.update(new_core_attr_subset_candidate)

    new_core_attr_subset_candidate = {"device_name": "cpu"}
    ml_model_tester.update(new_core_attr_subset_candidate)

    ml_model = generate_ml_model_0()

    kwargs = {"ml_model": ml_model}
    ml_model_tester.test_ml_model(**kwargs)

    ml_dataset_manager = generate_ml_dataset_manager_5()

    kwargs = {"ml_dataset_manager": ml_dataset_manager,
              "output_dirname": output_dirname}
    ml_model_tester = module_alias.MLModelTester(**kwargs)

    kwargs = {"ml_model": ml_model}
    ml_model_tester.test_ml_model(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_load_ml_model_from_file():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_model = generate_ml_model_0()
    ml_model_state_dict_filename = ("./test_data/modelling/cbed"
                                    "/distortion/ml_model.pth")
    pathlib.Path(ml_model_state_dict_filename).parent.mkdir(parents=True,
                                                            exist_ok=True)
    torch.save(ml_model.state_dict(), ml_model_state_dict_filename)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_model_state_dict_filename": "./foobar.pth",
                  "device_name": None}
        ml_model = module_alias.load_ml_model_from_file(**kwargs)

    kwargs = {"ml_model_state_dict_filename": ml_model_state_dict_filename,
              "device_name": None}
    ml_model = module_alias.load_ml_model_from_file(**kwargs)

    path_to_test_data = generate_path_to_test_data()
    shutil.rmtree(path_to_test_data)

    return None



def test_1_of_load_ml_model_from_state_dict():
    module_alias = emicroml.modelling.cbed.distortion.estimation

    ml_model = generate_ml_model_0()
    valid_ml_model_state_dict = ml_model.state_dict()

    key = ("_ctor_params.obj_stored_as_dressed_up_buffer"
           ".foobar.obj_stored_as_dressed_up_buffer")
    invalid_ml_model_state_dict = collections.OrderedDict()
    invalid_ml_model_state_dict[key] = None

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_model_state_dict": invalid_ml_model_state_dict,
                  "device_name": None}
        ml_model = module_alias.load_ml_model_from_state_dict(**kwargs)

    kwargs = {"ml_model_state_dict": valid_ml_model_state_dict,
              "device_name": None}
    ml_model = module_alias.load_ml_model_from_state_dict(**kwargs)

    return None



###########################
## Define error messages ##
###########################
