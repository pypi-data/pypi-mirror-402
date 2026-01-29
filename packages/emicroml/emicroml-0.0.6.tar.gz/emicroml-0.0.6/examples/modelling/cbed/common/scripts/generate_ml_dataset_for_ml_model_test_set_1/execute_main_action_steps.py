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
r"""A script that is called by various other scripts used for generating
individual machine learning (ML) datasets that can be used to test ML models for
a specified task. The script retrieves an image, presumed to be an simulated
undistorted CBED pattern, and uses it to generate a set of distorted "fake" CBED
patterns that are then stored in a new ML dataset.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --ml_model_task=<ml_model_task> \
         --disk_size_idx=<disk_size_idx> \
         --disk_size=<disk_size> \
         --ml_dataset_idx=<ml_dataset_idx> \
         --data_dir_1=<data_dir_1> \
         --data_dir_2=<data_dir_2>

where ``<ml_model_task>`` is one of a set of accepted strings that specifies the
ML model task, ``<disk_size_idx>`` is an integer that is used to select a seed
for random number generation, ``<disk_size>`` is one of a set of accepted
strings that describes the size of the CBED disks in the distorted CBED patterns
to be stored in the ML dataset to be generated; ``<ml_dataset_idx>`` is an
integer that is used to label the ML dataset; ``<data_dir_1>`` is the absolute
path to an existing directory or one to be created, within which the output data
is to be saved.; and ``<data_dir_2>`` is the absolute path to a directory
directly containing the file that stores the undistorted CBED pattern to use to
generate the distorted CBED patterns that will make up the individual ML dataset
to be generated.

At the moment, the only accepted value of ``<ml_model_task>`` is
``cbed/distortion/estimation``, which specifies that the ML model task is
distortion estimation in CBED. ``<disk_size_idx>`` and ``<ml_dataset_idx>`` can
be any nonnegative integers. The accepted values of ``<disk_size>`` are
``small``, ``medium``, and ``large``. ``<data_dir_1>`` can be any valid absolute
path to any valid existing directory or one to be created. ``<data_dir_2>`` must
be the absolute path to an existing directory that contains the output files
resulting from an execution of the function :func:`prismatique.stem.sim.run`
that stores at least one CBED intensity pattern.

The only non-temporary output data generated from this script is a single HDF5
file, which stores the ML dataset. Upon successful execution of the script, the
HDF5 file is saved to
``<data_dir_1>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C/ml_datasets_with_<disk_size>_sized_disks/ml_dataset_<ml_dataset_idx>.h5``.

This script uses the module
:mod:`emicroml.modelling.cbed.distortion.estimation`. It is recommended that you
consult the documentation of said module as you explore the remainder of this
script. Furthermore, this script also uses the packages :mod:`embeam`,
:mod:`fakecbed`, :mod:`distoptica`, and :mod:`prismatique` It is recommended
that you consult the documentation of these packages as well.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse



# For general array handling.
import numpy as np
import torch

# For calculating electron beam wavelengths given mean beam energies.
import embeam

# For generating distortion models.
import distoptica

# For generating fake CBED patterns.
import fakecbed

# For loading STEM simulation parameters.
import prismatique

# For inpainting images.
import skimage.restoration



# For generating ML datsets.
import emicroml.modelling.cbed.distortion.estimation



##############################################
## Define classes, functions, and constants ##
##############################################

class CBEDPatternGenerator():
    def __init__(self,
                 ml_model_task,
                 path_to_stem_multislice_sim_intensity_output,
                 max_num_disks_in_any_cbed_pattern,
                 rng_seed,
                 device_name,
                 path_to_stem_multislice_sim_params):
        self._ml_model_task = \
            ml_model_task
        self._path_to_stem_multislice_sim_intensity_output = \
            path_to_stem_multislice_sim_intensity_output
        self._max_num_disks_in_any_cbed_pattern = \
            max_num_disks_in_any_cbed_pattern
        self._rng_seed = \
            rng_seed
        self._device_name = \
            device_name
        
        kwargs = {"path_to_stem_multislice_sim_params": \
                  path_to_stem_multislice_sim_params}
        self._store_relevant_stem_multislice_sim_params(**kwargs)
        
        self._wavelength = embeam.wavelength(self._mean_beam_energy)
        
        self._store_stem_multislice_sim_intensity_pattern_signal()
        self._store_property_subset_of_stem_multislice_sim_intensity_output()

        undistorted_image_dims_in_pixels = \
            self._stem_multislice_sim_intensity_pattern_signal.data.shape[-2:]
        self._sampling_grid_dims_in_pixels = \
            (undistorted_image_dims_in_pixels[0]//2,
             undistorted_image_dims_in_pixels[1]//2)
        
        self._distortion_model_generator = \
            self._generate_distortion_model_generator()
        self._undistorted_tds_model = \
            self._generate_undistorted_tds_model()
        self._undistorted_disks = \
            self._generate_undistorted_disks()

        self._rng = np.random.default_rng(self._rng_seed)

        self._initialize_and_cache_cbed_pattern_params()

        return None



    def _store_relevant_stem_multislice_sim_params(
            self, path_to_stem_multislice_sim_params):
        kwargs = {"filename": path_to_stem_multislice_sim_params,
                  "skip_validation_and_conversion": True}
        stem_multislice_sim_params = prismatique.stem.sim.Params.load(**kwargs)
        
        stem_system_model_params = \
            stem_multislice_sim_params.core_attrs["stem_system_model_params"]
        probe_model_params = \
            stem_system_model_params.core_attrs["probe_model_params"]
        gun_model_params = \
            probe_model_params.core_attrs["gun_model_params"]

        self._convergence_semiangle = \
            probe_model_params.core_attrs["convergence_semiangle"]  # In mrads.
        self._mean_beam_energy = \
            gun_model_params.core_attrs["mean_beam_energy"]  # in keVs.

        return None



    def _store_stem_multislice_sim_intensity_pattern_signal(self):
        kwargs = {"filename": \
                  self._path_to_stem_multislice_sim_intensity_output,
                  "multi_dim_slice": \
                  (0, 0)}
        signal, _ = prismatique.load.cbed_intensity_patterns(**kwargs)
        self._stem_multislice_sim_intensity_pattern_signal = signal

        return None



    def _store_property_subset_of_stem_multislice_sim_intensity_output(self):
        signal = self._stem_multislice_sim_intensity_pattern_signal

        k_x_axis_label = "$k_x$"
        self._k_x_offset = signal.axes_manager[k_x_axis_label].offset
        self._k_x_scale = signal.axes_manager[k_x_axis_label].scale
        self._k_x_size = signal.axes_manager[k_x_axis_label].size

        k_y_axis_label = "$k_y$"
        self._k_y_offset = signal.axes_manager[k_y_axis_label].offset
        self._k_y_scale = signal.axes_manager[k_y_axis_label].scale
        self._k_y_size = signal.axes_manager[k_y_axis_label].size

        return None



    def _generate_distortion_model_generator(self):
        if ml_model_task == "cbed/distortion/estimation":
            module_alias = emicroml.modelling.cbed.distortion.estimation
            cls_alias = module_alias.DefaultDistortionModelGenerator
            kwargs = {"reference_pt": \
                      (0.5, 0.5),
                      "rng_seed": \
                      self._rng_seed,
                      "sampling_grid_dims_in_pixels": \
                      self._sampling_grid_dims_in_pixels,
                      "least_squares_alg_params": \
                      None,
                      "device_name": \
                      self._device_name}

        distortion_model_generator = cls_alias(**kwargs)

        return distortion_model_generator



    def _generate_undistorted_tds_model(self):
        reference_pt_of_distortion_model_generator = \
            self._distortion_model_generator.core_attrs["reference_pt"]

        kwargs = {"center": reference_pt_of_distortion_model_generator,
                  "widths": 4*(1,),
                  "rotation_angle": 0,
                  "val_at_center": 0,
                  "functional_form": "asymmetric_gaussian"}
        tds_peak = fakecbed.shapes.Peak(**kwargs)

        kwargs = {"peaks": (tds_peak,), "constant_bg": 0}
        undistorted_tds_model = fakecbed.tds.Model(**kwargs)

        return undistorted_tds_model



    def _generate_undistorted_disks(self):
        a = 3.1604  # "a" lattice parameter of MoS2 in Å.

        # Magnitude of either primitive reciprocal lattice vector of MoS2.
        b_1_mag = (2*np.pi) * (2/a/np.sqrt(3))

        # MoS2 rescaled (non-primitive) unit-cell reciprocal lattice vectors.
        q_1 = (b_1_mag / (2*np.pi)) * np.array([np.sqrt(3), 0.0])
        q_2 = (b_1_mag / (2*np.pi)) * np.array([0.0, 1.0])

        # Positions of disks in unit cell.
        delta_disk_1 = (0/2)*q_1 + (0/2)*q_2
        delta_disk_2 = (1/2)*q_1 + (1/2)*q_2

        # Disk unit cell.
        disk_unit_cell = np.array((delta_disk_1, delta_disk_2))

        # Determine the number of tiles of the disk unit cell.
        k_x_tiling_indices = self._calc_k_x_tiling_indices(q_1)
        k_y_tiling_indices = self._calc_k_y_tiling_indices(q_2)

        undistorted_disks = tuple()

        for k_x_tiling_idx in k_x_tiling_indices:
            for k_y_tiling_idx in k_y_tiling_indices:
                shift = k_x_tiling_idx*q_1 + k_y_tiling_idx*q_2
                current_disk_cell = np.array(tuple(delta_disk+shift
                                                   for delta_disk
                                                   in disk_unit_cell))

                for (k_x_c_support, k_y_c_support) in current_disk_cell:
                    kwargs = {"k_x_c_support": k_x_c_support,
                              "k_y_c_support": k_y_c_support}
                    undistorted_disk = self._generate_undistorted_disk(**kwargs)
                    undistorted_disks += (undistorted_disk,)

        return undistorted_disks



    def _calc_k_x_tiling_indices(self, q_1):
        k_R_support = self._calc_k_R_support()

        q_1_norm = np.linalg.norm(q_1)

        k_x_offset = self._k_x_offset
        k_x_scale = self._k_x_scale
        k_x_size = self._k_x_size

        k_x_max_candidate_1 = (abs(k_x_offset)
                               + k_R_support)
        k_x_max_candidate_2 = (abs(k_x_offset + k_x_scale*(k_x_size-1))
                               + k_R_support)
        
        k_x_max = max(k_x_max_candidate_1, k_x_max_candidate_2)

        max_k_x_tiling_idx = int(k_x_max // q_1_norm)
        min_k_x_tiling_idx = -max_k_x_tiling_idx

        k_x_tiling_indices = range(min_k_x_tiling_idx, max_k_x_tiling_idx+1)

        return k_x_tiling_indices



    def _calc_k_R_support(self):
        k_R_support = (self._convergence_semiangle/1000) / self._wavelength

        return k_R_support



    def _generate_undistorted_disk(self, k_x_c_support, k_y_c_support):
        kwargs = {"k_x_coord": k_x_c_support}
        u_x_c_support = self._k_x_coord_to_u_x_coord(**kwargs)

        kwargs = {"k_y_coord": k_y_c_support}
        u_y_c_support = self._k_y_coord_to_u_y_coord(**kwargs)

        kwargs = {"center": (u_x_c_support, u_y_c_support),
                  "radius": self._calc_u_R_support(),
                  "intra_shape_val": 1,
                  "skip_validation_and_conversion": True}
        undistorted_disk_support = fakecbed.shapes.Circle(**kwargs)

        kwargs = {"support": undistorted_disk_support,
                  "intra_support_shapes": tuple(),
                  "skip_validation_and_conversion": True}
        undistorted_disk = fakecbed.shapes.NonuniformBoundedShape(**kwargs)

        return undistorted_disk



    def _calc_k_y_tiling_indices(self, q_2):
        k_R_support = self._calc_k_R_support()

        q_2_norm = np.linalg.norm(q_2)

        k_y_offset = self._k_y_offset
        k_y_scale = self._k_y_scale
        k_y_size = self._k_y_size

        k_y_max_candidate_1 = (abs(k_y_offset)
                               + k_R_support)
        k_y_max_candidate_2 = (abs(k_y_offset + k_y_scale*(k_y_size-1))
                               + k_R_support)
        
        k_y_max = max(k_y_max_candidate_1, k_y_max_candidate_2)

        max_k_y_tiling_idx = int(k_y_max // q_2_norm)
        min_k_y_tiling_idx = -max_k_y_tiling_idx

        k_y_tiling_indices = range(min_k_y_tiling_idx, max_k_y_tiling_idx+1)

        return k_y_tiling_indices



    def _k_x_coord_to_u_x_coord(self, k_x_coord):
        u_x_offset = 0.5/(self._k_x_size/2)
        u_x_scale = 1/(self._k_x_size/2)

        n_x = self._k_x_coord_to_pixel_coord(k_x_coord)

        u_x_coord = u_x_offset + n_x*u_x_scale

        return u_x_coord



    def _k_x_coord_to_pixel_coord(self, k_x_coord):
        pixel_coord = (k_x_coord-(self._k_x_offset/2))/self._k_x_scale
        
        return pixel_coord



    def _k_y_coord_to_u_y_coord(self, k_y_coord):
        u_y_offset = 1-(1-0.5)/(self._k_y_size/2)
        u_y_scale = -1/(self._k_y_size/2)

        n_y = self._k_y_coord_to_pixel_coord(k_y_coord)

        u_y_coord = u_y_offset + n_y*u_y_scale

        return u_y_coord



    def _k_y_coord_to_pixel_coord(self, k_y_coord):
        pixel_coord = (k_y_coord-(self._k_y_offset/2))/self._k_y_scale

        return pixel_coord



    def _calc_u_R_support(self):
        k_R_support = self._calc_k_R_support()

        u_x_scale = 1/(self._k_x_size/2)
        u_R_support = (k_R_support/self._k_x_scale)*u_x_scale

        return u_R_support



    def _initialize_and_cache_cbed_pattern_params(self):
        self._cbed_pattern_params = \
            {"undistorted_tds_model": \
             self._undistorted_tds_model,
             "undistorted_disks": \
             self._undistorted_disks,
             "undistorted_misc_shapes": \
             tuple(),
             "undistorted_outer_illumination_shape": \
             None,
             "gaussian_filter_std_dev": \
             0,
             "num_pixels_across_pattern": \
             self._sampling_grid_dims_in_pixels[0],
             "distortion_model": \
             None,
             "apply_shot_noise": \
             False,
             "rng_seed": \
             None,
             "cold_pixels": \
             tuple(),
             "detector_partition_width_in_pixels": \
             4,
             "mask_frame": \
             (0, 0, 0, 0)}

        return None



    def generate(self):
        cbed_pattern_params = self._cbed_pattern_params

        generation_attempt_count = 0
        max_num_generation_attempts = 10
        cbed_pattern_generation_has_not_been_completed = True

        while cbed_pattern_generation_has_not_been_completed:
            try:
                cbed_pattern_params["distortion_model"] = \
                    self._distortion_model_generator.generate()

                key_subset = ("mask_frame",
                              "undistorted_outer_illumination_shape")
                for key in key_subset:
                    method_name = "_generate_{}".format(key)
                    method_alias = getattr(self, method_name)
                    kwargs = {"cbed_pattern_params": cbed_pattern_params}
                    cbed_pattern_params[key] = method_alias(**kwargs)

                kwargs = cbed_pattern_params
                cbed_pattern = fakecbed.discretized.CBEDPattern(**kwargs)

                disk_clipping_registry = \
                    cbed_pattern.get_disk_clipping_registry(deep_copy=False)
                num_non_clipped_disks = \
                    (~disk_clipping_registry).sum().item()

                min_num_disks_in_any_cbed_pattern = 4

                if num_non_clipped_disks < min_num_disks_in_any_cbed_pattern:
                    unformatted_err_msg = _cbed_pattern_generator_err_msg_1
                    args = (min_num_disks_in_any_cbed_pattern,)
                    err_msg = unformatted_err_msg.format(*args)
                    raise ValueError(err_msg)

                cbed_pattern_generation_has_not_been_completed = False
            except:
                generation_attempt_count += 1                
                if generation_attempt_count == max_num_generation_attempts:
                    unformatted_err_msg = _cbed_pattern_generator_err_msg_2
                    args = ("", " ({})".format(max_num_generation_attempts))
                    err_msg = unformatted_err_msg.format(*args)                    
                    raise RuntimeError(err_msg)

        kwargs = {"overriding_image": self._generate_overriding_image()}
        cbed_pattern.override_image_then_reapply_mask(**kwargs)

        return cbed_pattern



    def _generate_mask_frame(self, cbed_pattern_params):
        distortion_model = cbed_pattern_params["distortion_model"]

        min_fractional_mask_frame_width = \
            self._distortion_model_generator._min_fractional_mask_frame_width
        max_fractional_mask_frame_width = \
            self._distortion_model_generator._max_fractional_mask_frame_width

        sampling_grid_dims_in_pixels = \
            self._sampling_grid_dims_in_pixels
        num_pixels_across_each_cbed_pattern = \
            sampling_grid_dims_in_pixels[0]

        attr_name = "mask_frame_of_distorted_then_resampled_images"
        quadruple_1 = np.array(getattr(distortion_model, attr_name),
                               dtype=float)
        quadruple_1[:2] /= sampling_grid_dims_in_pixels[0]
        quadruple_1[2:] /= sampling_grid_dims_in_pixels[1]

        kwargs = {"low": min_fractional_mask_frame_width,
                  "high": max_fractional_mask_frame_width,
                  "size": 4}
        quadruple_2 = self._rng.uniform(**kwargs)

        trivial_mask_frame_is_not_to_be_generated = \
            self._rng.choice((True, False), p=(1/2, 1-1/2)).item()

        mask_frame = \
            tuple(np.round(((quadruple_1>=quadruple_2)*quadruple_1
                            + (quadruple_1<quadruple_2)*quadruple_2)
                           * num_pixels_across_each_cbed_pattern).astype(int)
                  * trivial_mask_frame_is_not_to_be_generated)

        return mask_frame

    

    def _generate_undistorted_outer_illumination_shape(self,
                                                       cbed_pattern_params):
        mask_frame = cbed_pattern_params["mask_frame"]

        undistorted_outer_illumination_shape_is_elliptical = \
            self._rng.choice((True, False), p=(3/4, 1/4)).item()

        if undistorted_outer_illumination_shape_is_elliptical:
            method_name = ("_generate_elliptical"
                           "_undistorted_outer_illumination_shape")
        else:
            method_name = ("_generate_generic"
                           "_undistorted_outer_illumination_shape")
            
        method_alias = getattr(self, method_name)
        kwargs = {"mask_frame": mask_frame}
        undistorted_outer_illumination_shape = method_alias(**kwargs)

        return undistorted_outer_illumination_shape



    def _generate_elliptical_undistorted_outer_illumination_shape(self,
                                                                  mask_frame):
        rng = self._rng

        u_r_E = abs(rng.normal(loc=0, scale=1/20))
        u_phi_E = rng.uniform(low=0, high=2*np.pi)
        cos = np.cos
        sin = np.sin

        reference_pt_of_distortion_model_generator = \
            self._distortion_model_generator.core_attrs["reference_pt"]

        center = (reference_pt_of_distortion_model_generator[0]
                  - u_r_E*cos(u_phi_E),
                  reference_pt_of_distortion_model_generator[1]
                  - u_r_E*sin(u_phi_E))
        center = (center[0].item(), center[1].item())

        kwargs = {"reference_pt_of_distortion_model_generator": \
                  reference_pt_of_distortion_model_generator,
                  "mask_frame": \
                  mask_frame}
        semi_major_axis = self._generate_semi_major_axis(**kwargs)

        kwargs = {"center": center,
                  "semi_major_axis": semi_major_axis,
                  "eccentricity": abs(rng.uniform(low=0, high=0.6)),
                  "rotation_angle": rng.uniform(low=0, high=2*np.pi),
                  "intra_shape_val": 1.0,
                  "skip_validation_and_conversion": True}
        undistorted_outer_illumination_shape = fakecbed.shapes.Ellipse(**kwargs)

        return undistorted_outer_illumination_shape



    def _generate_semi_major_axis(self,
                                  reference_pt_of_distortion_model_generator,
                                  mask_frame):
        rng = self._rng

        choices = ((sum(mask_frame) != 0)*1e6, 1e6)

        loc = (max(reference_pt_of_distortion_model_generator[0],
                   1-reference_pt_of_distortion_model_generator[0],
                   reference_pt_of_distortion_model_generator[1],
                   1-reference_pt_of_distortion_model_generator[1])
               + rng.choice(choices, p=(3/4, 1-3/4)).item())
        semi_major_axis = loc + rng.uniform(low=-loc/6, high=loc/6)

        return semi_major_axis



    def _generate_generic_undistorted_outer_illumination_shape(self,
                                                               mask_frame):
        rng = self._rng

        u_r_GB = abs(rng.normal(loc=0, scale=1/20))
        u_phi_GB = rng.uniform(low=0, high=2*np.pi)
        cos = np.cos
        sin = np.sin

        reference_pt_of_distortion_model_generator = \
            self._distortion_model_generator.core_attrs["reference_pt"]

        radial_reference_pt_of_blob = \
            (reference_pt_of_distortion_model_generator[0]
             - u_r_GB*cos(u_phi_GB).item(),
             reference_pt_of_distortion_model_generator[1]
             - u_r_GB*sin(u_phi_GB).item())

        kwargs = {"reference_pt_of_distortion_model_generator": \
                  reference_pt_of_distortion_model_generator,
                  "mask_frame": \
                  mask_frame}
        radial_amplitude = self._generate_radial_amplitude(**kwargs)

        num_amplitudes = rng.integers(low=2, high=4, endpoint=True).item()
        radial_amplitudes = (radial_amplitude,)
        radial_phases = tuple()
        for amplitude_idx in range(1, num_amplitudes+1):
            kwargs = {"low": 0,
                      "high": radial_amplitudes[0]/num_amplitudes/4}
            radial_amplitude = rng.uniform(**kwargs)
            radial_amplitudes += (radial_amplitude,)

            kwargs = {"low": 0,
                      "high": 2*np.pi/amplitude_idx}
            radial_phase = rng.uniform(**kwargs)
            radial_phases += (radial_phase,)

        kwargs = \
            {"radial_reference_pt": radial_reference_pt_of_blob,
             "radial_amplitudes": radial_amplitudes,
             "radial_phases": radial_phases,
             "intra_shape_val": 1.0,
             "skip_validation_and_conversion": True}
        undistorted_outer_illumination_shape = \
            fakecbed.shapes.GenericBlob(**kwargs)

        return undistorted_outer_illumination_shape



    def _generate_radial_amplitude(self,
                                   reference_pt_of_distortion_model_generator,
                                   mask_frame):
        kwargs = {"reference_pt_of_distortion_model_generator": \
                  reference_pt_of_distortion_model_generator,
                  "mask_frame": \
                  mask_frame}
        semi_major_axis = self._generate_semi_major_axis(**kwargs)
        radial_amplitude = semi_major_axis

        return radial_amplitude



    def _generate_overriding_image(self):
        distortion_model = self._cbed_pattern_params["distortion_model"]
        device = distortion_model.device
        signal = self._stem_multislice_sim_intensity_pattern_signal

        input_tensor_to_sample = torch.from_numpy(signal.data)
        input_tensor_to_sample = input_tensor_to_sample.to(device)[None, None]

        method_name = "get_sampling_grid"
        method_alias = getattr(distortion_model, method_name)
        sampling_grid = method_alias(deep_copy=False)

        method_name = "get_flow_field_of_coord_transform_right_inverse"
        method_alias = getattr(distortion_model, method_name)
        flow_field = method_alias(deep_copy=False)

        u_x = flow_field[0]+sampling_grid[0]
        u_y = flow_field[1]+sampling_grid[1]

        kwargs = \
            {"sampling_grid": sampling_grid, "u_x": u_x, "u_y": u_y}
        jacobian_weights = \
            self._calc_jacobian_weights_for_distorting_then_resampling(**kwargs)

        resampling_normalization_weight = (input_tensor_to_sample.shape[-2]
                                           * input_tensor_to_sample.shape[-1]
                                           / jacobian_weights.shape[0]
                                           / jacobian_weights.shape[1])

        grid_shape = (1,) + self._sampling_grid_dims_in_pixels + (2,)
        grid = torch.zeros(grid_shape,
                           dtype=input_tensor_to_sample.dtype,
                           device=device)
        grid[0, :, :, 0] = u_x-0.5
        grid[0, :, :, 1] = -(u_y-0.5)

        kwargs = {"input": input_tensor_to_sample,
                  "grid": grid,
                  "mode": "bilinear",
                  "padding_mode": "zeros",
                  "align_corners": False}
        overriding_image = (torch.nn.functional.grid_sample(**kwargs)[0, 0]
                            * jacobian_weights[:, :]
                            * resampling_normalization_weight)

        kwargs = {"input_image": overriding_image}
        overriding_image = self._apply_shot_noise_to_image(**kwargs)
        overriding_image = self._apply_detector_partition_inpainting(**kwargs)

        return overriding_image



    def _calc_jacobian_weights_for_distorting_then_resampling(self,
                                                              sampling_grid,
                                                              u_x,
                                                              u_y):
        spacing = (sampling_grid[1][:, 0], sampling_grid[0][0, :])

        kwargs = {"input": u_x,
                  "spacing": spacing,
                  "dim": None,
                  "edge_order": 2}
        d_u_x_over_d_q_y, d_u_x_over_d_q_x = torch.gradient(**kwargs)

        kwargs["input"] = u_y
        d_u_y_over_d_q_y, d_u_y_over_d_q_x = torch.gradient(**kwargs)

        jacobian_weights_for_distorting_then_resampling = \
            torch.abs(d_u_x_over_d_q_x*d_u_y_over_d_q_y
                      - d_u_x_over_d_q_y*d_u_y_over_d_q_x)

        return jacobian_weights_for_distorting_then_resampling



    def _apply_shot_noise_to_image(self, input_image):
        torch_rng_seed = self._rng.integers(low=0, high=2**32-1).item()
        torch_rng = torch.Generator(device=input_image.device)
        torch_rng = torch_rng.manual_seed(torch_rng_seed)
        output_image = torch.poisson(input_image, torch_rng)

        return output_image



    def _apply_detector_partition_inpainting(self, input_image):
        N_DPW = self._cbed_pattern_params["detector_partition_width_in_pixels"]

        k_I_1 = ((input_image.shape[1]-1)//2) - (N_DPW//2)
        k_I_2 = k_I_1 + N_DPW - 1

        inpainting_mask = np.zeros(input_image.shape, dtype=bool)
        inpainting_mask[k_I_1:k_I_2+1, :] = True
        inpainting_mask[:, k_I_1:k_I_2+1] = True

        kwargs = {"image": input_image.numpy(force=True),
                  "mask": inpainting_mask}
        output_image = skimage.restoration.inpaint_biharmonic(**kwargs)
        output_image = torch.from_numpy(output_image)
        output_image = output_image.to(device=input_image.device,
                                       dtype=input_image.dtype)

        return output_image



def parse_and_convert_cmd_line_args():
    accepted_ml_model_tasks = ("cbed/distortion/estimation",)

    current_func_name = "parse_and_convert_cmd_line_args"

    try:
        parser = argparse.ArgumentParser()
        argument_names = ("ml_model_task",
                          "disk_size_idx",
                          "disk_size",
                          "ml_dataset_idx",
                          "data_dir_1",
                          "data_dir_2")
        for argument_name in argument_names:
            parser.add_argument("--"+argument_name)
        args = parser.parse_args()
        ml_model_task = args.ml_model_task
        disk_size_idx = int(args.disk_size_idx)
        disk_size = args.disk_size
        ml_dataset_idx = int(args.ml_dataset_idx)
        path_to_data_dir_1 = args.data_dir_1
        path_to_data_dir_2 = args.data_dir_2

        if ((ml_model_task not in accepted_ml_model_tasks)
            or (disk_size_idx < 0)
            or (ml_dataset_idx < 0)):
            raise
    except:
        unformatted_err_msg = globals()["_"+current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(accepted_ml_model_tasks[0])
        raise SystemExit(err_msg)

    converted_cmd_line_args = {"ml_model_task": ml_model_task,
                               "disk_size_idx": disk_size_idx,
                               "disk_size": disk_size,
                               "ml_dataset_idx": ml_dataset_idx,
                               "path_to_data_dir_1": path_to_data_dir_1,
                               "path_to_data_dir_2": path_to_data_dir_2}
    
    return converted_cmd_line_args



###########################
## Define error messages ##
###########################

_cbed_pattern_generator_err_msg_1 = \
    ("The CBED pattern must contain at least {} non-clipped CBED disks.")
_cbed_pattern_generator_err_msg_2 = \
    ("The CBED pattern generator{} has exceeded its programmed maximum number "
     "of attempts{} to generate a valid CBED pattern: see traceback for "
     "details.")

_parse_and_convert_cmd_line_args_err_msg_1 = \
    ("The correct form of the command is:\n"
     "\n"
     "    python execute_main_action_steps.py "
     "--ml_model_task=<ml_model_task> "
     "--disk_size_idx=<disk_size_idx> "
     "--disk_size=<disk_size> "
     "--ml_dataset_idx=<ml_dataset_idx> "
     "--data_dir_1=<data_dir_1> "
     "--data_dir_2=<data_dir_2>\n"
     "\n"
     "where ``<ml_model_task>`` must be set to {}; ``<disk_size_idx>`` must be "
     "a nonnegative integer; ``<disk_size>`` must be one of the strings "
     "``small``, ``medium``, or ``large``; ``<ml_dataset_idx>`` must be a "
     "nonnegative integer; ``<data_dir_1>`` must be a valid absolute path to a "
     "valid existing directory or one to be created; and ``<data_dir_2>`` "
     "must be the absolute path to a valid directory.")



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
converted_cmd_line_args = parse_and_convert_cmd_line_args()
ml_model_task = converted_cmd_line_args["ml_model_task"]
disk_size_idx = converted_cmd_line_args["disk_size_idx"]
disk_size = converted_cmd_line_args["disk_size"]
ml_dataset_idx = converted_cmd_line_args["ml_dataset_idx"]
path_to_data_dir_1 = converted_cmd_line_args["path_to_data_dir_1"]
path_to_data_dir_2 = converted_cmd_line_args["path_to_data_dir_2"]



# Select the ``emicroml`` submodule required to generate a ML dataset that is
# appropriate to the specified ML model task. Also, select the RNG seed
# according to the specified ML dataset index and disk size index.
if ml_model_task == "cbed/distortion/estimation":
    ml_model_task_module = emicroml.modelling.cbed.distortion.estimation
    rng_seed = disk_size_idx + ml_dataset_idx + 100000



# Construct the "fake" CBED pattern generator.
path_to_stem_multislice_sim_params = \
    path_to_data_dir_2 + "/stem_sim_params.json"
path_to_stem_multislice_sim_intensity_output = \
    path_to_data_dir_2 + "/stem_sim_intensity_output.h5"

max_num_disks_in_any_cbed_pattern = 90

kwargs = {"ml_model_task": \
          ml_model_task,
          "path_to_stem_multislice_sim_intensity_output": \
          path_to_stem_multislice_sim_intensity_output,
          "max_num_disks_in_any_cbed_pattern": \
          90,
          "rng_seed": \
          rng_seed,
          "device_name": \
          None,
          "path_to_stem_multislice_sim_params": \
          path_to_stem_multislice_sim_params}
cbed_pattern_generator = CBEDPatternGenerator(**kwargs)



# Generate and save the ML dataset.
sample_name = "MoS2_on_amorphous_C"

unformatted_output_filename = (path_to_data_dir_1
                               + "/ml_datasets"
                               + "/ml_datasets_for_ml_model_test_set_1"
                               + "/ml_datasets_with_cbed_patterns_of_{}"
                               + "/ml_datasets_with_{}_sized_disks"
                               + "/ml_dataset_{}.h5")
output_filename = unformatted_output_filename.format(sample_name,
                                                     disk_size,
                                                     ml_dataset_idx)

kwargs = \
    {"num_cbed_patterns": 2880,
     "cbed_pattern_generator": cbed_pattern_generator,
     "output_filename": output_filename,
     "max_num_ml_data_instances_per_file_update": 288}
if ml_model_task == "cbed/distortion/estimation":
    kwargs["max_num_disks_in_any_cbed_pattern"] = \
        max_num_disks_in_any_cbed_pattern
    
ml_model_task_module.generate_and_save_ml_dataset(**kwargs)
