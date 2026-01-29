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
"""Contains code common to various modules in the subpackage
:mod:`emicroml.modelling.cbed.distortion`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For performing deep copies.
import copy

# For generating all possible sequences of binary numbers of given length.
import itertools

# For generating the alphabet.
import string



# For general array handling.
import numpy as np

# For generating distortion models.
import distoptica

# For generating fake CBED patterns.
import fakecbed

# For calculating generalized Laguerre polynomials.
import scipy.special

# For building neural network models.
import torch

# For image processing tools that can be integrated into deep learning models.
import kornia

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation and updatability.
import fancytypes

# For closing HDF5 files.
import h5py



# Contains implementation code that is applicable to the current module.
import emicroml.modelling._common



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = []



def _get_device(device_name):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._get_device
    device = func_alias(device_name)

    return device



def _check_and_convert_reference_pt(params):
    obj_name = "reference_pt"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}    
    reference_pt = czekitout.convert.to_pair_of_floats(**kwargs)

    return reference_pt



def _pre_serialize_reference_pt(reference_pt):
    obj_to_pre_serialize = reference_pt
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_reference_pt(serializable_rep):
    reference_pt = serializable_rep

    return reference_pt



def _check_and_convert_rng_seed(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_rng_seed
    rng_seed = func_alias(params)

    return rng_seed



def _pre_serialize_rng_seed(rng_seed):
    obj_to_pre_serialize = rng_seed

    obj_name = "rng_seed"

    module_alias = fakecbed.discretized
    cls_alias = module_alias.CBEDPattern
    func_alias = cls_alias.get_pre_serialization_funcs()[obj_name]
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



def _de_pre_serialize_rng_seed(serializable_rep):
    obj_name = "rng_seed"

    module_alias = fakecbed.discretized
    cls_alias = module_alias.CBEDPattern
    func_alias = cls_alias.get_de_pre_serialization_funcs()[obj_name]
    rng_seed = func_alias(serializable_rep)

    return rng_seed



def _check_and_convert_sampling_grid_dims_in_pixels(params):
    obj_name = "sampling_grid_dims_in_pixels"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_validation_and_conversion_funcs()[obj_name]
    sampling_grid_dims_in_pixels = func_alias(params)

    return sampling_grid_dims_in_pixels



def _pre_serialize_sampling_grid_dims_in_pixels(sampling_grid_dims_in_pixels):
    obj_to_pre_serialize = sampling_grid_dims_in_pixels

    obj_name = "sampling_grid_dims_in_pixels"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_pre_serialization_funcs()[obj_name]
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



def _de_pre_serialize_sampling_grid_dims_in_pixels(serializable_rep):
    obj_name = "sampling_grid_dims_in_pixels"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_de_pre_serialization_funcs()[obj_name]
    sampling_grid_dims_in_pixels = func_alias(serializable_rep)

    return sampling_grid_dims_in_pixels



def _check_and_convert_least_squares_alg_params(params):
    obj_name = "least_squares_alg_params"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_validation_and_conversion_funcs()[obj_name]
    least_squares_alg_params = func_alias(params)

    return least_squares_alg_params



def _pre_serialize_least_squares_alg_params(least_squares_alg_params):
    obj_to_pre_serialize = least_squares_alg_params

    obj_name = "least_squares_alg_params"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_pre_serialization_funcs()[obj_name]
    serializable_rep = func_alias(least_squares_alg_params)
    
    return serializable_rep



def _de_pre_serialize_least_squares_alg_params(serializable_rep):
    obj_name = "least_squares_alg_params"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_de_pre_serialization_funcs()[obj_name]
    least_squares_alg_params = func_alias(serializable_rep)

    return least_squares_alg_params



def _check_and_convert_device_name(params):
    obj_name = "device_name"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_validation_and_conversion_funcs()[obj_name]
    device_name = func_alias(params)

    return device_name



def _pre_serialize_device_name(device_name):
    obj_to_pre_serialize = device_name

    obj_name = "device_name"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_pre_serialization_funcs()[obj_name]
    serializable_rep = func_alias(device_name)
    
    return serializable_rep



def _de_pre_serialize_device_name(serializable_rep):
    obj_name = "device_name"

    module_alias = distoptica
    cls_alias = module_alias.DistortionModel
    func_alias = cls_alias.get_de_pre_serialization_funcs()[obj_name]
    device_name = func_alias(serializable_rep)

    return device_name



_module_alias_1 = \
    emicroml.modelling._common
_module_alias_2 = \
    emicroml.modelling.optimizers
_default_reference_pt = \
    (0.5, 0.5)
_default_rng_seed = \
    _module_alias_1._default_rng_seed
_default_sampling_grid_dims_in_pixels = \
    (512, 512)
_default_least_squares_alg_params = \
    None
_default_device_name = \
    None
_default_skip_validation_and_conversion = \
    _module_alias_2._default_skip_validation_and_conversion



class _DefaultDistortionModelGenerator(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("reference_pt",
                        "rng_seed",
                        "sampling_grid_dims_in_pixels",
                        "least_squares_alg_params",
                        "device_name")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs



    def __init__(self,
                 reference_pt,
                 rng_seed,
                 sampling_grid_dims_in_pixels,
                 least_squares_alg_params,
                 device_name,
                 skip_validation_and_conversion):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self._set_fixed_attrs()

        self_core_attrs = self.get_core_attrs(deep_copy=False)
        for self_core_attr_name in self_core_attrs:
            attr_name = "_"+self_core_attr_name
            attr = self_core_attrs[self_core_attr_name]
            setattr(self, attr_name, attr)

        self._rng = np.random.default_rng(self._rng_seed)
        self._device = _get_device(device_name=self._device_name)
        
        return None



    def _set_fixed_attrs(self):
        self._quadratic_radial_distortion_amplitude_min = -0.3
        self._quadratic_radial_distortion_amplitude_max = 1.5

        self._elliptical_distortion_amplitude_min = 0
        self._elliptical_distortion_amplitude_max = 0.125

        self._elliptical_distortion_phase_min = 0
        self._elliptical_distortion_phase_max = np.pi

        self._spiral_distortion_amplitude_min = -0.75
        self._spiral_distortion_amplitude_max = 0.75

        self._parabolic_distortion_amplitude_min = 0
        self._parabolic_distortion_amplitude_max = 0.35

        self._parabolic_distortion_phase_min = 0
        self._parabolic_distortion_phase_max = 2*np.pi

        self._min_fractional_mask_frame_width = 0/6
        self._max_fractional_mask_frame_width = 1/6

        return None



    @classmethod
    def get_validation_and_conversion_funcs(cls):
        validation_and_conversion_funcs = \
            cls._validation_and_conversion_funcs_.copy()

        return validation_and_conversion_funcs


    
    @classmethod
    def get_pre_serialization_funcs(cls):
        pre_serialization_funcs = \
            cls._pre_serialization_funcs_.copy()

        return pre_serialization_funcs


    
    @classmethod
    def get_de_pre_serialization_funcs(cls):
        de_pre_serialization_funcs = \
            cls._de_pre_serialization_funcs_.copy()

        return de_pre_serialization_funcs



    def update(self,
               new_core_attr_subset_candidate,
               skip_validation_and_conversion=\
               _default_skip_validation_and_conversion):
        super().update(new_core_attr_subset_candidate,
                       skip_validation_and_conversion)
        self.execute_post_core_attrs_update_actions()

        return None



    def generate(self):
        r"""Generate a random distortion model.

        See the summary documentation for the current class for details on how
        distortion models are randomly generated.

        Returns
        -------
        distortion_model : :class:`distoptica.DistortionModel`
            The distortion model.

        """
        generation_attempt_count = 0
        max_num_generation_attempts = 10
        distortion_model_generation_has_not_been_completed = True
        
        while distortion_model_generation_has_not_been_completed:
            unformatted_err_msg = _default_distortion_model_generator_err_msg_1
            args = ("({})".format(max_num_generation_attempts),)
            err_msg = unformatted_err_msg.format(*args)
            err_type = RuntimeError

            try:
                kwargs = {"standard_coord_transform_params": \
                          self._generate_standard_coord_transform_params(),
                          "sampling_grid_dims_in_pixels": \
                          self._sampling_grid_dims_in_pixels,
                          "device_name": \
                          self._device_name,
                          "least_squares_alg_params": \
                          self._least_squares_alg_params,
                          "skip_validation_and_conversion": \
                          True}
                func_alias = distoptica.generate_standard_distortion_model
                distortion_model = func_alias(**kwargs)

                method_alias = \
                    self._distortion_model_requires_an_invalid_mask_frame
                distortion_model_requires_an_invalid_mask_frame = \
                    method_alias(distortion_model)

                err_msg = _default_distortion_model_generator_err_msg_2
                err_type = ValueError

                # Raises an error if the denominator is ``True``.
                True//(not distortion_model_requires_an_invalid_mask_frame)

                distortion_model_generation_has_not_been_completed = False
            except:
                generation_attempt_count += 1
                
                if generation_attempt_count == max_num_generation_attempts:
                    raise err_type(err_msg)

        return distortion_model



    def _generate_standard_coord_transform_params(self):
        kwargs = \
            {"center": \
             self._generate_distortion_center(),
             "quadratic_radial_distortion_amplitude": \
             self._generate_quadratic_radial_distortion_amplitude(),
             "elliptical_distortion_vector": \
             self._generate_elliptical_distortion_vector(),
             "spiral_distortion_amplitude": \
             self._generate_spiral_distortion_amplitude(),
             "parabolic_distortion_vector": \
             self._generate_parabolic_distortion_vector(),
             "skip_validation_and_conversion": \
             True}
        standard_coord_transform_params = \
            distoptica.StandardCoordTransformParams(**kwargs)

        return standard_coord_transform_params



    def _generate_distortion_center(self):
        reference_pt = self._reference_pt

        u_r_c_D = abs(self._rng.normal(loc=0, scale=1/20))
        u_phi_c_D = self._rng.uniform(low=0, high=2*np.pi)

        u_x_c_D = reference_pt[0] - u_r_c_D*np.cos(u_phi_c_D)
        u_y_c_D = reference_pt[1] - u_r_c_D*np.sin(u_phi_c_D)
        distortion_center = (u_x_c_D.item(), u_y_c_D.item())

        return distortion_center



    def _generate_quadratic_radial_distortion_amplitude(self):
        kwargs = {"low": self._quadratic_radial_distortion_amplitude_min,
                  "high": self._quadratic_radial_distortion_amplitude_max}
        quadratic_radial_distortion_amplitude = self._rng.uniform(**kwargs)

        return quadratic_radial_distortion_amplitude



    def _generate_elliptical_distortion_vector(self):
        kwargs = {"low": self._elliptical_distortion_amplitude_min,
                  "high": self._elliptical_distortion_amplitude_max}
        elliptical_distortion_amplitude = self._rng.uniform(**kwargs)

        kwargs = {"low": self._elliptical_distortion_phase_min,
                  "high": self._elliptical_distortion_phase_max}
        elliptical_distortion_phase = self._rng.uniform(**kwargs)

        elliptical_distortion_vector = (elliptical_distortion_amplitude
                                        * np.cos(2*elliptical_distortion_phase),
                                        elliptical_distortion_amplitude
                                        * np.sin(2*elliptical_distortion_phase))
        elliptical_distortion_vector = (elliptical_distortion_vector[0].item(),
                                        elliptical_distortion_vector[1].item())

        return elliptical_distortion_vector



    def _generate_spiral_distortion_amplitude(self):
        kwargs = {"low": self._spiral_distortion_amplitude_min,
                  "high": self._spiral_distortion_amplitude_max}
        spiral_distortion_amplitude = self._rng.uniform(**kwargs)

        return spiral_distortion_amplitude



    def _generate_parabolic_distortion_vector(self):
        kwargs = {"low": self._parabolic_distortion_amplitude_min,
                  "high": self._parabolic_distortion_amplitude_max}
        parabolic_distortion_amplitude = self._rng.uniform(**kwargs)

        kwargs = {"low": self._parabolic_distortion_phase_min,
                  "high": self._parabolic_distortion_phase_max}
        parabolic_distortion_phase = self._rng.uniform(**kwargs)

        parabolic_distortion_vector = (parabolic_distortion_amplitude
                                       * np.cos(parabolic_distortion_phase),
                                       parabolic_distortion_amplitude
                                       * np.sin(parabolic_distortion_phase))
        parabolic_distortion_vector = (parabolic_distortion_vector[0].item(),
                                       parabolic_distortion_vector[1].item())

        return parabolic_distortion_vector



    def _distortion_model_requires_an_invalid_mask_frame(self,
                                                         distortion_model):
        attr_name = "convergence_map_of_distorted_then_resampled_images"
        convergence_map = getattr(distortion_model, attr_name)

        attr_name = "mask_frame_of_distorted_then_resampled_images"
        mask_frame = getattr(distortion_model, attr_name)

        L, R, B, T = mask_frame
        sampling_grid_dims_in_pixels = self._sampling_grid_dims_in_pixels
        fractional_mask_frame = (L/sampling_grid_dims_in_pixels[0],
                                 R/sampling_grid_dims_in_pixels[0],
                                 B/sampling_grid_dims_in_pixels[1],
                                 T/sampling_grid_dims_in_pixels[1])

        min_w = self._min_fractional_mask_frame_width
        max_w = self._max_fractional_mask_frame_width

        distortion_model_requires_an_invalid_mask_frame = \
            np.any(tuple((w<min_w) or (max_w<w) for w in fractional_mask_frame))
        distortion_model_requires_an_invalid_mask_frame = \
            distortion_model_requires_an_invalid_mask_frame.item()

        return distortion_model_requires_an_invalid_mask_frame



_building_block_counts_in_stages_of_distoptica_net = \
    (3, 5, 2)



def _check_and_convert_num_pixels_across_each_cbed_pattern(params):
    obj_name = "num_pixels_across_each_cbed_pattern"

    func_alias = czekitout.convert.to_positive_int
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    num_pixels_across_each_cbed_pattern = func_alias(**kwargs)

    max_num_downsampling_steps_in_any_encoder_used_in_ml_model = \
        (emicroml.modelling._common._DistopticaNetEntryFlow._num_downsamplings
         + len(_building_block_counts_in_stages_of_distoptica_net))

    current_func_name = "_check_and_convert_num_pixels_across_each_cbed_pattern"

    M = 2**max_num_downsampling_steps_in_any_encoder_used_in_ml_model
    if num_pixels_across_each_cbed_pattern % M != 0:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(M)
        raise ValueError(err_msg)

    return num_pixels_across_each_cbed_pattern



def _pre_serialize_num_pixels_across_each_cbed_pattern(
        num_pixels_across_each_cbed_pattern):
    obj_to_pre_serialize = num_pixels_across_each_cbed_pattern
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_num_pixels_across_each_cbed_pattern(serializable_rep):
    num_pixels_across_each_cbed_pattern = serializable_rep

    return num_pixels_across_each_cbed_pattern



def _check_and_convert_max_num_disks_in_any_cbed_pattern(params):
    obj_name = \
        "max_num_disks_in_any_cbed_pattern"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    max_num_disks_in_any_cbed_pattern = \
        czekitout.convert.to_positive_int(**kwargs)

    return max_num_disks_in_any_cbed_pattern



def _pre_serialize_max_num_disks_in_any_cbed_pattern(
        max_num_disks_in_any_cbed_pattern):
    obj_to_pre_serialize = max_num_disks_in_any_cbed_pattern
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_max_num_disks_in_any_cbed_pattern(serializable_rep):
    max_num_disks_in_any_cbed_pattern = serializable_rep

    return max_num_disks_in_any_cbed_pattern



_default_num_pixels_across_each_cbed_pattern = \
    _default_sampling_grid_dims_in_pixels[0]
_default_max_num_disks_in_any_cbed_pattern = \
    90



class _DefaultCBEDPatternGenerator(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("num_pixels_across_each_cbed_pattern",
                        "max_num_disks_in_any_cbed_pattern",
                        "rng_seed",
                        "sampling_grid_dims_in_pixels",
                        "least_squares_alg_params",
                        "device_name")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs

    
    
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
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)
        for self_core_attr_name in self_core_attrs:
            attr_name = "_"+self_core_attr_name
            attr = self_core_attrs[self_core_attr_name]
            setattr(self, attr_name, attr)
        
        kwargs = \
            {"reference_pt": (0.5, 0.5),
             "rng_seed": self._rng_seed,
             "sampling_grid_dims_in_pixels": self._sampling_grid_dims_in_pixels,
             "least_squares_alg_params": self._least_squares_alg_params,
             "device_name": self._device_name,
             "skip_validation_and_conversion": True}
        self._distortion_model_generator = \
            _DefaultDistortionModelGenerator(**kwargs)

        self._rng = self._distortion_model_generator._rng

        self._device = self._distortion_model_generator._device

        self._min_num_disks_in_any_cbed_pattern = 4

        self._A_0_min = 20
        self._A_0_max = 100

        self._n_orbital_max = 4

        self._characteristic_sizes_of_orbitals = \
            self._generate_characteristic_sizes_of_orbitals()
        self._characteristic_scales_of_orbitals = \
            self._generate_characteristic_scales_of_orbitals()

        self._min_fractional_mask_frame_width = \
            self._distortion_model_generator._min_fractional_mask_frame_width
        self._max_fractional_mask_frame_width = \
            self._distortion_model_generator._max_fractional_mask_frame_width

        return None



    def _generate_characteristic_sizes_of_orbitals(self):
        num_pts = 10000
        u_rho_min = 0
        u_rho_max = 50
        u_rho = np.linspace(u_rho_min, u_rho_max, num_pts)

        n_orbital_max = self._n_orbital_max

        characteristic_sizes_of_orbitals = dict()
        dict_level_0 = characteristic_sizes_of_orbitals

        for n_orbital in range(1, n_orbital_max+1):
            dict_level_1 = dict()

            for l_orbital in range(0, n_orbital):
                L = scipy.special.genlaguerre(n_orbital-l_orbital-1,
                                              2*l_orbital+1)

                threshold = 0.05

                f = (np.exp(-u_rho)
                     * u_rho**(2*l_orbital)
                     * L(u_rho) * L(u_rho))
                f += 1e-10
                f /= f.max()
                f = np.log10(f) - np.log10(threshold)

                idx_1 = (f.size - np.argmax(f[::-1]>0) - 1)
                idx_2 = idx_1+1

                approx_root_of_f = (u_rho[idx_1]+u_rho[idx_2]) / 2

                characteristic_size = (1 / n_orbital / approx_root_of_f).item()

                dict_level_1[l_orbital] = characteristic_size

            dict_level_0[n_orbital] = dict_level_1

        return characteristic_sizes_of_orbitals



    def _generate_characteristic_scales_of_orbitals(self):
        num_pts = 256
        coord_min = 0.5
        coord_max = 1
        single_1d_coord_array = torch.linspace(coord_min,
                                               coord_max,
                                               num_pts,
                                               device=self._device)
        pair_of_1d_coord_arrays = (single_1d_coord_array, single_1d_coord_array)
        sampling_grid = torch.meshgrid(*pair_of_1d_coord_arrays, indexing="xy")

        n_orbital_max = self._n_orbital_max

        characteristic_scales_of_orbitals = dict()
        dict_level_0 = characteristic_scales_of_orbitals

        for n_orbital in range(1, n_orbital_max+1):
            dict_level_1 = dict()

            for l_orbital in range(0, n_orbital):
                dict_level_2 = dict()

                for m_orbital in range(0, l_orbital+1):
                    characteristic_sizes = \
                        self._characteristic_sizes_of_orbitals
                    characteristic_size = \
                        characteristic_sizes[n_orbital][l_orbital]

                    kwargs = {"center": (0.5, 0.5),
                              "principal_quantum_number": n_orbital,
                              "azimuthal_quantum_number": l_orbital,
                              "magnetic_quantum_number": m_orbital,
                              "effective_size": characteristic_size,
                              "renormalization_factor": 1,
                              "rotation_angle": 0}
                    orbital = fakecbed.shapes.Orbital(**kwargs)

                    kwargs = {"u_x": sampling_grid[0],
                              "u_y": sampling_grid[1],
                              "skip_validation_and_conversion": True}
                    max_intensity = orbital.eval(**kwargs).max().item()

                    characteristic_scale = 1 / max_intensity
                    dict_level_2[m_orbital] = characteristic_scale

                dict_level_1[l_orbital] = dict_level_2

            dict_level_0[n_orbital] = dict_level_1

        return characteristic_scales_of_orbitals



    @classmethod
    def get_validation_and_conversion_funcs(cls):
        validation_and_conversion_funcs = \
            cls._validation_and_conversion_funcs_.copy()

        return validation_and_conversion_funcs


    
    @classmethod
    def get_pre_serialization_funcs(cls):
        pre_serialization_funcs = \
            cls._pre_serialization_funcs_.copy()

        return pre_serialization_funcs


    
    @classmethod
    def get_de_pre_serialization_funcs(cls):
        de_pre_serialization_funcs = \
            cls._de_pre_serialization_funcs_.copy()

        return de_pre_serialization_funcs



    def update(self,
               new_core_attr_subset_candidate,
               skip_validation_and_conversion=\
               _default_skip_validation_and_conversion):
        super().update(new_core_attr_subset_candidate,
                       skip_validation_and_conversion)
        self.execute_post_core_attrs_update_actions()

        return None



    def generate(self):
        r"""Generate a fake CBED pattern.

        The randomization scheme employed by the current class to generate
        random fake CBED patterns is somewhat convoluted, and will not be
        documented here in detail. For those who are interested, you can parse
        through the source code of the current class for more details on the
        scheme.

        Returns
        -------
        cbed_pattern : :class:`fakecbed.discretized.CBEDPattern`
            The fake CBED pattern.

        """
        generation_attempt_count = 0
        max_num_generation_attempts = 10
        cbed_pattern_generation_has_not_been_completed = True
        
        while cbed_pattern_generation_has_not_been_completed:
            try:
                cbed_pattern_params = self._generate_cbed_pattern_params()
                kwargs = cbed_pattern_params
                cbed_pattern = fakecbed.discretized.CBEDPattern(**kwargs)

                disk_clipping_registry = \
                    cbed_pattern.get_disk_clipping_registry(deep_copy=False)
                num_non_clipped_disks = \
                    (~disk_clipping_registry).sum().item()

                min_num_disks_in_any_cbed_pattern = \
                    self._min_num_disks_in_any_cbed_pattern
                
                if num_non_clipped_disks < min_num_disks_in_any_cbed_pattern:
                    unformatted_err_msg = \
                        _default_cbed_pattern_generator_err_msg_1

                    args = (min_num_disks_in_any_cbed_pattern,)
                    err_msg = unformatted_err_msg.format(*args)
                    raise ValueError(err_msg)

                cbed_pattern.get_signal(deep_copy=False)

                cbed_pattern_generation_has_not_been_completed = False
            except:
                generation_attempt_count += 1
                
                if generation_attempt_count == max_num_generation_attempts:
                    unformatted_err_msg = \
                        _default_cbed_pattern_generator_err_msg_2

                    args = ("", " ({})".format(max_num_generation_attempts))
                    err_msg = unformatted_err_msg.format(*args)
                    raise RuntimeError(err_msg)

        return cbed_pattern



    def _generate_cbed_pattern_params(self):
        undistorted_tds_model_1, undistorted_tds_model_2 = \
            self._generate_undistorted_tds_models()

        distortion_model = \
            self._generate_distortion_model(undistorted_tds_model_1)
        
        mask_frame = self._generate_mask_frame(distortion_model)
        
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1,
             "distortion_model": distortion_model,
             "mask_frame": mask_frame}
        undistorted_outer_illumination_shape = \
            self._generate_undistorted_outer_illumination_shape(**kwargs)
            
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1,
             "undistorted_tds_model_2": undistorted_tds_model_2}
        undistorted_disks, undistorted_misc_shapes = \
            self._generate_undistorted_disks_and_misc_shapes(**kwargs)

        cbed_pattern_params = {"undistorted_tds_model": \
                               undistorted_tds_model_2,
                               "undistorted_disks": \
                               undistorted_disks,
                               "undistorted_misc_shapes": \
                               undistorted_misc_shapes,
                               "undistorted_outer_illumination_shape": \
                               undistorted_outer_illumination_shape,
                               "gaussian_filter_std_dev": \
                               self._rng.uniform(low=1, high=5),
                               "num_pixels_across_pattern": \
                               self._num_pixels_across_each_cbed_pattern,
                               "distortion_model": \
                               distortion_model,
                               "apply_shot_noise": \
                               True,
                               "rng_seed": \
                               self._rng.integers(low=0, high=2**32-1).item(),
                               "cold_pixels": \
                               self._generate_cold_pixels(),
                               "detector_partition_width_in_pixels": \
                               2*self._rng.integers(low=0, high=4).item(),
                               "mask_frame": \
                               mask_frame}

        return cbed_pattern_params



    def _generate_undistorted_tds_models(self):
        undistorted_tds_model_1 = \
            self._generate_undistorted_tds_model_1()
        undistorted_tds_model_2 = \
            self._generate_undistorted_tds_model_2(undistorted_tds_model_1)

        return undistorted_tds_model_1, undistorted_tds_model_2



    def _generate_undistorted_tds_model_1(self):
        num_peaks = self._rng.choice((1, 2), p=(1/2, 1-1/2)).item()
        possible_functional_forms = ("asymmetric_gaussian",
                                     "asymmetric_exponential",
                                     "asymmetric_lorentzian")
        rng = self._rng

        pt_0 = rng.uniform(low=1/4, high=3/4, size=2)
        A_0 = rng.uniform(low=self._A_0_min, high=self._A_0_max)
        sigma_0 = rng.uniform(low=0, high=1/2)

        peaks = tuple()
        kwargs = {"val_at_center": rng.uniform(low=0.4*A_0, high=0.6*A_0)}
        for peak_idx in range(num_peaks):
            center = pt_0 + rng.uniform(low=-1/20, high=1/20, size=2)
            center = tuple(elem.item() for elem in center)

            widths = rng.uniform(low=0.8*sigma_0, high=1.2*sigma_0, size=4)
            widths = tuple(widths.tolist())

            functional_form = rng.choice(possible_functional_forms).item()

            kwargs["center"] = center
            kwargs["widths"] = widths
            kwargs["rotation_angle"] = rng.uniform(low=0, high=2*np.pi)
            kwargs["val_at_center"] = A_0-kwargs["val_at_center"]
            kwargs["functional_form"] = functional_form
            kwargs["skip_validation_and_conversion"] = True
            peak = fakecbed.shapes.Peak(**kwargs)
            peaks += (peak,)

        kwargs = {"peaks": peaks,
                  "constant_bg": 0,
                  "skip_validation_and_conversion": True}
        undistorted_tds_model_1 = fakecbed.tds.Model(**kwargs)

        return undistorted_tds_model_1



    def _generate_undistorted_tds_model_2(self, undistorted_tds_model_1):
        rng = self._rng
        no_peaks = rng.choice((False, True), p=(4/5, 1/5)).item()

        if no_peaks:
            peaks = tuple()
        else:
            undistorted_tds_model_1_core_attrs = \
                undistorted_tds_model_1.get_core_attrs(deep_copy=False)

            peaks = copy.deepcopy(undistorted_tds_model_1_core_attrs["peaks"])

            A_set = (rng.uniform(low=self._A_0_min, high=self._A_0_max),)
            for peak in peaks:
                peak_core_attrs = peak.get_core_attrs(deep_copy=False)
                A_set += (peak_core_attrs["val_at_center"],)
            A_set += (sum(A_set[1:]),)

            for peak in peaks:
                peak_core_attrs = peak.get_core_attrs(deep_copy=False)
                old_val_at_center = peak_core_attrs["val_at_center"]
                new_val_at_center = (A_set[0]/A_set[-1]) * old_val_at_center
                new_core_attr_subset_candidate = {"val_at_center": \
                                                  new_val_at_center}
                kwargs = {"new_core_attr_subset_candidate": \
                          new_core_attr_subset_candidate,
                          "skip_validation_and_conversion": \
                          True}
                peak.update(**kwargs)

        kwargs = \
            {"peaks": peaks,
             "constant_bg": rng.integers(low=1, high=8, endpoint=True).item(),
             "skip_validation_and_conversion": True}
        undistorted_tds_model_2 = fakecbed.tds.Model(**kwargs)

        return undistorted_tds_model_2



    def _generate_distortion_model(self, undistorted_tds_model_1):
        rng = self._rng

        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1}
        reference_pt_of_distortion_model_generator = \
            self._generate_reference_pt_of_distortion_model_generator(**kwargs)

        rng_seed = rng.integers(low=0, high=2**32, endpoint=True).item()

        new_core_attr_subset_candidate = \
            {"reference_pt": reference_pt_of_distortion_model_generator,
             "rng_seed": rng_seed}
        
        kwargs = {"new_core_attr_subset_candidate": \
                  new_core_attr_subset_candidate,
                  "skip_validation_and_conversion": \
                  True}
        self._distortion_model_generator.update(**kwargs)

        distortion_model = self._distortion_model_generator.generate()

        return distortion_model



    def _generate_reference_pt_of_distortion_model_generator(
            self, undistorted_tds_model_1):
        undistorted_tds_model_1_core_attrs = \
            undistorted_tds_model_1.get_core_attrs(deep_copy=False)
        peaks = \
            undistorted_tds_model_1_core_attrs["peaks"]

        num_peaks = len(peaks)

        reference_pt_of_distortion_model_generator = \
            np.array((0.0, 0.0))
        for peak in peaks:
            peak_core_attrs = \
                peak.get_core_attrs(deep_copy=False)
            reference_pt_of_distortion_model_generator += \
                np.array(peak_core_attrs["center"])
        reference_pt_of_distortion_model_generator /= \
            num_peaks
        reference_pt_of_distortion_model_generator = \
            tuple(reference_pt_of_distortion_model_generator.tolist())

        return reference_pt_of_distortion_model_generator



    def _generate_mask_frame(self, distortion_model):
        sampling_grid_dims_in_pixels = \
            self._sampling_grid_dims_in_pixels
        num_pixels_across_each_cbed_pattern = \
            self._num_pixels_across_each_cbed_pattern

        attr_name = "mask_frame_of_distorted_then_resampled_images"
        quadruple_1 = np.array(getattr(distortion_model, attr_name),
                               dtype=float)
        quadruple_1[:2] /= sampling_grid_dims_in_pixels[0]
        quadruple_1[2:] /= sampling_grid_dims_in_pixels[1]

        kwargs = {"low": self._min_fractional_mask_frame_width,
                  "high": self._max_fractional_mask_frame_width,
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



    def _generate_undistorted_outer_illumination_shape(
            self, undistorted_tds_model_1, distortion_model, mask_frame):
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1}
        reference_pt_of_distortion_model_generator = \
            self._generate_reference_pt_of_distortion_model_generator(**kwargs)

        undistorted_outer_illumination_shape_is_elliptical = \
            self._rng.choice((True, False), p=(3/4, 1/4)).item()

        if undistorted_outer_illumination_shape_is_elliptical:
            method_name = ("_generate_elliptical"
                           "_undistorted_outer_illumination_shape")
        else:
            method_name = ("_generate_generic"
                           "_undistorted_outer_illumination_shape")
            
        method_alias = getattr(self, method_name)
        kwargs = {"reference_pt_of_distortion_model_generator": \
                  reference_pt_of_distortion_model_generator,
                  "mask_frame": \
                  mask_frame}
        undistorted_outer_illumination_shape = method_alias(**kwargs)

        return undistorted_outer_illumination_shape



    def _generate_elliptical_undistorted_outer_illumination_shape(
            self,
            reference_pt_of_distortion_model_generator,
            mask_frame):
        rng = self._rng

        u_r_E = abs(rng.normal(loc=0, scale=1/20))
        u_phi_E = rng.uniform(low=0, high=2*np.pi)
        cos = np.cos
        sin = np.sin

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



    def _generate_generic_undistorted_outer_illumination_shape(
            self,
            reference_pt_of_distortion_model_generator,
            mask_frame):
        rng = self._rng

        u_r_GB = abs(rng.normal(loc=0, scale=1/20))
        u_phi_GB = rng.uniform(low=0, high=2*np.pi)
        cos = np.cos
        sin = np.sin

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



    def _generate_undistorted_disks_and_misc_shapes(self,
                                                    undistorted_tds_model_1,
                                                    undistorted_tds_model_2):
        method_alias = \
            self._generate_undistorted_disks_and_max_abs_amplitude_sums
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1,
             "undistorted_tds_model_2": undistorted_tds_model_2}
        undistorted_disks, max_abs_amplitude_sums = \
            method_alias(**kwargs)

        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1,
             "undistorted_disks": undistorted_disks,
             "max_abs_amplitude_sums": max_abs_amplitude_sums}
        undistorted_misc_shapes = \
            self._generate_undistorted_misc_shapes(**kwargs)

        return undistorted_disks, undistorted_misc_shapes



    def _generate_undistorted_disks_and_max_abs_amplitude_sums(
            self,
            undistorted_tds_model_1,
            undistorted_tds_model_2):
        undistorted_disk_supports = \
            self._generate_undistorted_disk_supports(undistorted_tds_model_1)
            
        undistorted_disks = tuple()
        max_abs_amplitude_sums = []

        for undistorted_disk_support in undistorted_disk_supports:
            method_alias = \
                self._generate_intra_disk_shapes_and_max_abs_amplitude_sum
            kwargs = \
                {"undistorted_disk_support": undistorted_disk_support,
                 "undistorted_tds_model_1": undistorted_tds_model_1,
                 "undistorted_tds_model_2": undistorted_tds_model_2}
            intra_disk_shapes, max_abs_amplitude_sum = \
                method_alias(**kwargs)

            if len(intra_disk_shapes) > 0:
                NonuniformBoundedShape = fakecbed.shapes.NonuniformBoundedShape
                kwargs = {"support": undistorted_disk_support,
                          "intra_support_shapes": intra_disk_shapes,
                          "skip_validation_and_conversion": True}
                undistorted_disk = NonuniformBoundedShape(**kwargs)
                undistorted_disks += (undistorted_disk,)
                max_abs_amplitude_sums += [max_abs_amplitude_sum]

        num_disks = len(undistorted_disks)
        if num_disks > 1:
            additional_rescaling_is_to_be_performed = \
                self._rng.choice((True, False), p=(1/4, 1-1/4)).item()
            if additional_rescaling_is_to_be_performed:
                method_alias = \
                    self._perform_additional_rescaling_to_undistorted_disks
                kwargs = \
                    {"undistorted_disks": undistorted_disks,
                     "max_abs_amplitude_sums": max_abs_amplitude_sums}
                _ = \
                    method_alias(**kwargs)

        max_abs_amplitude_sums = tuple(max_abs_amplitude_sums)

        return undistorted_disks, max_abs_amplitude_sums



    def _generate_undistorted_disk_supports(self, undistorted_tds_model_1):
        u_R_support = self._generate_u_R_support()

        kwargs = \
            {"u_R_support": u_R_support,
             "undistorted_tds_model_1": undistorted_tds_model_1}
        undistorted_disk_support_centers = \
            self._generate_undistorted_disk_support_centers(**kwargs)

        undistorted_disk_supports = tuple()
        for undistorted_disk_support_center in undistorted_disk_support_centers:
            kwargs = {"center": undistorted_disk_support_center,
                      "radius": u_R_support,
                      "intra_shape_val": 1,
                      "skip_validation_and_conversion": True}
            undistorted_disk_support = fakecbed.shapes.Circle(**kwargs)
            undistorted_disk_supports += (undistorted_disk_support,)

        return undistorted_disk_supports



    def _generate_u_R_support(self):
        u_R_support = self._rng.uniform(low=1/40, high=1/8)

        return u_R_support



    def _generate_undistorted_disk_support_centers(self,
                                                   u_R_support,
                                                   undistorted_tds_model_1):
        center_generation_has_not_been_completed = True
        while center_generation_has_not_been_completed:
            centers_approximately_form_a_grid = \
                self._rng.choice((True, False), p=(1/2, 1-1/2)).item()

            if centers_approximately_form_a_grid:
                kwargs = \
                    {"u_R_support": u_R_support,
                     "undistorted_tds_model_1": undistorted_tds_model_1}
                undistorted_disk_support_centers = \
                    self._generate_positions_from_a_jittered_grid(**kwargs)
            else:
                subset_of_centers_approximately_form_a_grid = \
                    self._rng.choice((True, False), p=(1/2, 1-1/2)).item()

                kwargs = \
                    {"u_R_support": u_R_support,
                     "undistorted_tds_model_1": undistorted_tds_model_1}
                if subset_of_centers_approximately_form_a_grid:
                    undistorted_disk_support_centers = \
                        self._generate_positions_from_a_jittered_grid(**kwargs)
                else:
                    undistorted_disk_support_centers = \
                        tuple()

                kwargs["undistorted_disk_support_centers"] = \
                    undistorted_disk_support_centers
                undistorted_disk_support_centers += \
                    self._sample_positions_quasi_uniformly_from_space(**kwargs)

            center_generation_has_not_been_completed = \
                (len(undistorted_disk_support_centers) == 0)

        return undistorted_disk_support_centers



    def _generate_positions_from_a_jittered_grid(self,
                                                 u_R_support,
                                                 undistorted_tds_model_1):
        jitter = 1/8
        rotation_matrix = self._generate_rotation_matrix()
        positions_from_a_jittered_grid = tuple()

        generation_attempt_count = 0
        max_num_generation_attempts = 10
        positions_from_a_jittered_grid = tuple()

        while len(positions_from_a_jittered_grid) == 0:
            kwargs = {"u_R_support": u_R_support, "jitter": jitter}
            a_1, a_2 = self._generate_primitive_lattice_vectors(**kwargs)

            kwargs = {"undistorted_tds_model_1": undistorted_tds_model_1}
            approx_tiling_radius = self._generate_approx_tiling_radius(**kwargs)

            kwargs = {"approx_tiling_radius": approx_tiling_radius, "a_2": a_2}
            tiling_idx_set_2 = self._generate_tiling_idx_set_2(**kwargs)

            for tiling_idx_2 in tiling_idx_set_2:
                kwargs = \
                    {"approx_tiling_radius": approx_tiling_radius,
                     "a_1": a_1,
                     "a_2": a_2,
                     "tiling_idx_2": tiling_idx_2,
                     "undistorted_tds_model_1": undistorted_tds_model_1,
                     "jitter": jitter,
                     "nn_distance": self._calc_nn_distance(a_1, a_2),
                     "rotation_matrix": rotation_matrix,
                     "u_R_support": u_R_support}
                positions_from_a_jittered_grid += \
                    self._generate_positions_from_a_jittered_row(**kwargs)

            num_disks = len(positions_from_a_jittered_grid)
            min_num_disks = self._min_num_disks_in_any_cbed_pattern
            max_num_disks = self._max_num_disks_in_any_cbed_pattern

            generation_attempt_count += 1

            position_generation_has_been_completed = \
                ((min_num_disks <= num_disks <= max_num_disks)
                 or (generation_attempt_count == max_num_generation_attempts))
            single_dim_slice = \
                slice(0, position_generation_has_been_completed*max_num_disks)
            positions_from_a_jittered_grid = \
                positions_from_a_jittered_grid[single_dim_slice]

        return positions_from_a_jittered_grid



    def _generate_rotation_matrix(self):
        rotation_angle = \
            self._rng.uniform(low=0, high=2*np.pi)
        rotation_matrix = \
            np.array(((np.cos(rotation_angle), -np.sin(rotation_angle)),
                      (np.sin(rotation_angle), np.cos(rotation_angle))))

        return rotation_matrix



    def _generate_primitive_lattice_vectors(self, u_R_support, jitter):
        min_distance_between_undistorted_disk_support_centers = u_R_support/3

        nn_distance_threshold = \
            (1.001
             * (1+2*jitter)
             * min_distance_between_undistorted_disk_support_centers)

        primitive_lattice_vector_generation_has_not_been_completed = True
        while primitive_lattice_vector_generation_has_not_been_completed:
            min_num_disks_in_any_cbed_pattern = \
                self._min_num_disks_in_any_cbed_pattern
            max_num_disks_in_any_cbed_pattern = \
                self._max_num_disks_in_any_cbed_pattern

            theta = self._rng.uniform(low=np.pi/6, high=np.pi/2)

            a_1_norm_min = \
                max(1 / (np.sqrt(max_num_disks_in_any_cbed_pattern)-1+1e-10),
                    nn_distance_threshold)
            a_1_norm_max = \
                max(1 / (np.sqrt(min_num_disks_in_any_cbed_pattern)+1+1e-10),
                    a_1_norm_min)
            a_1_norm = \
                self._rng.uniform(low=a_1_norm_min, high=a_1_norm_max)

            norm_ratio_min = max(0.5, a_1_norm_min/a_1_norm)
            norm_ratio_max = min(2, a_1_norm_max/a_1_norm)
            norm_ratio = self._rng.uniform(low=norm_ratio_min,
                                           high=norm_ratio_max)

            a_2_norm = norm_ratio * a_1_norm

            a_1 = a_1_norm * np.array((1, 0))
            a_2 = a_2_norm * np.array((np.cos(theta), np.sin(theta)))

            nn_distance = \
                self._calc_nn_distance(a_1, a_2)
            primitive_lattice_vector_generation_has_not_been_completed = \
                (nn_distance <= nn_distance_threshold)

        return a_1, a_2



    def _calc_nn_distance(self, a_1, a_2):
        vectors = (a_1, a_2, a_1+a_2, a_1-a_2)
        distances = tuple(np.linalg.norm(vector) for vector in vectors)
        nn_distance = min(distances)

        return nn_distance



    def _generate_approx_tiling_radius(self, undistorted_tds_model_1):
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1}
        reference_pt_of_distortion_model_generator = \
            self._generate_reference_pt_of_distortion_model_generator(**kwargs)
        reference_pt = \
            np.array(reference_pt_of_distortion_model_generator)

        corners = np.array(((0, 0), (1, 0), (0, 1), (1, 1)))

        approx_tiling_radius = \
            0
        for corner in corners:
            distance_from_corner_to_reference_pt = \
                np.linalg.norm(reference_pt-corner)
            approx_tiling_radius = \
                max(approx_tiling_radius,
                    2*distance_from_corner_to_reference_pt)
        approx_tiling_radius = \
            approx_tiling_radius.item()

        return approx_tiling_radius



    def _generate_tiling_idx_set_2(self, approx_tiling_radius, a_2):
        num_tiles_along_a_2 = int(2*np.ceil(approx_tiling_radius/a_2[1])+1)
        min_tiling_idx_2 = -(num_tiles_along_a_2//2)
        max_tiling_idx_2 = min_tiling_idx_2 + num_tiles_along_a_2 - 1
        tiling_idx_set_2 = range(min_tiling_idx_2, max_tiling_idx_2+1)

        return tiling_idx_set_2



    def _generate_positions_from_a_jittered_row(self,
                                                approx_tiling_radius,
                                                a_1,
                                                a_2,
                                                tiling_idx_2,
                                                undistorted_tds_model_1,
                                                jitter,
                                                nn_distance,
                                                rotation_matrix,
                                                u_R_support):
        kwargs = {"approx_tiling_radius": approx_tiling_radius,
                  "a_1": a_1,
                  "a_2": a_2,
                  "tiling_idx_2": tiling_idx_2}
        tiling_idx_set_1 = self._generate_tiling_idx_set_1(**kwargs)

        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1}
        reference_pt_of_distortion_model_generator = \
            self._generate_reference_pt_of_distortion_model_generator(**kwargs)
        
        positions_from_a_jittered_row = tuple()
        for tiling_idx_1 in tiling_idx_set_1:
            d_u_x, d_u_y = \
                self._generate_displacement_from_grid(jitter, nn_distance)
            candidate_position = \
                (reference_pt_of_distortion_model_generator
                 + rotation_matrix @ (tiling_idx_1*a_1
                                      + tiling_idx_2*a_2
                                      + np.array((d_u_x, d_u_y))))
            candidate_position = \
                tuple(candidate_position.tolist())

            kwargs = {"u_R_support": u_R_support,
                      "disk_center": candidate_position}
            if self._disk_center_is_within_acceptable_bounds(**kwargs):
                positions_from_a_jittered_row += (candidate_position,)

        return positions_from_a_jittered_row



    def _generate_tiling_idx_set_1(self,
                                   approx_tiling_radius,
                                   a_1,
                                   a_2,
                                   tiling_idx_2):
        num_tiles_along_a_1 = int(2*np.ceil(approx_tiling_radius/a_1[0])+1)
        offset = int(np.round(tiling_idx_2*a_2[0]/a_1[0]))
        min_tiling_idx_1 = -(num_tiles_along_a_1//2) + offset
        max_tiling_idx_1 = min_tiling_idx_1 + num_tiles_along_a_1 - 1
        tiling_idx_set_1 = range(min_tiling_idx_1, max_tiling_idx_1+1)

        return tiling_idx_set_1



    def _generate_displacement_from_grid(self, jitter, nn_distance):
        d_u_r = self._rng.uniform(low=0, high=jitter*nn_distance)
        theta = self._rng.uniform(low=0, high=2*np.pi)
        
        d_u_x = d_u_r * np.cos(theta)
        d_u_y = d_u_r * np.sin(theta)

        displacement_from_grid = np.array((d_u_x, d_u_y))

        return displacement_from_grid



    def _disk_center_is_within_acceptable_bounds(self, u_R_support, disk_center):
        u_x_min = -(3/4)*u_R_support
        u_x_max = 1 + (3/4)*u_R_support
                
        u_y_min = -(3/4)*u_R_support
        u_y_max = 1 + (3/4)*u_R_support
                
        result = ((u_x_min <= disk_center[0] <= u_x_max)
                  and (u_y_min <= disk_center[1] <= u_y_max))

        return result



    def _sample_positions_quasi_uniformly_from_space(
            self,
            u_R_support,
            undistorted_tds_model_1,
            undistorted_disk_support_centers):
        disk_overlapping_is_enabled = \
            self._rng.choice((True, False), p=(1/2, 1-1/2)).item()
        
        min_distance_between_undistorted_disk_support_centers = \
            (u_R_support/3 if disk_overlapping_is_enabled else 2*u_R_support)

        kwargs = {"low": self._min_num_disks_in_any_cbed_pattern,
                  "high": self._max_num_disks_in_any_cbed_pattern+1}
        rand_int = (self._rng.integers(**kwargs).item()
                    - len(undistorted_disk_support_centers))
        target_num_sampled_positions = max(0, rand_int)

        sampled_positions = tuple()
        while (len(sampled_positions) < target_num_sampled_positions):
            kwargs = \
                {"previously_sampled_positions": \
                 sampled_positions,
                 "undistorted_disk_support_centers": \
                 undistorted_disk_support_centers,
                 "min_distance_between_undistorted_disk_support_centers": \
                 min_distance_between_undistorted_disk_support_centers,
                 "undistorted_tds_model_1": \
                 undistorted_tds_model_1,
                 "u_R_support": \
                 u_R_support}
            sampled_position = \
                self._sample_position_quasi_uniformly_from_space(**kwargs)
            sampled_positions += \
                (sampled_position,)

        return sampled_positions



    def _sample_position_quasi_uniformly_from_space(
            self,
            previously_sampled_positions,
            undistorted_disk_support_centers,
            min_distance_between_undistorted_disk_support_centers,
            undistorted_tds_model_1,
            u_R_support):
        previously_sampled_positions = \
            np.array(previously_sampled_positions)
        undistorted_disk_support_centers = \
            np.array(undistorted_disk_support_centers)

        displacement_origins = (undistorted_disk_support_centers.tolist()
                                + previously_sampled_positions.tolist())
        displacement_origins = np.array(displacement_origins)

        target_distance_threshold = \
            min_distance_between_undistorted_disk_support_centers

        generation_attempt_count = 0
        max_num_generation_attempts = 10
        position_sampling_has_not_been_completed = True

        while position_sampling_has_not_been_completed:
            if ((len(previously_sampled_positions) == 0)
                and (len(undistorted_disk_support_centers) == 0)):
                method_name = ("_generate_reference_pt"
                               "_of_distortion_model_generator")
                method_alias = getattr(self, method_name)
                kwargs = {"undistorted_tds_model_1": undistorted_tds_model_1}
                sampled_position = method_alias(**kwargs)

                position_sampling_has_not_been_completed = False
            else:
                u_x = self._rng.uniform(low=-(3/4)*u_R_support,
                                        high=1+(3/4)*u_R_support)                
                u_y = self._rng.uniform(low=-(3/4)*u_R_support,
                                        high=1+(3/4)*u_R_support)

                candidate_position = np.array((u_x, u_y))
                displacements = displacement_origins - candidate_position
                distances = np.linalg.norm(displacements, axis=-1)

                generation_attempt_count += 1
                if ((generation_attempt_count == max_num_generation_attempts)
                    or np.all(distances > target_distance_threshold)):
                    sampled_position = tuple(candidate_position.tolist())
                    position_sampling_has_not_been_completed = False

        return sampled_position



    def _generate_intra_disk_shapes_and_max_abs_amplitude_sum(
            self,
            undistorted_disk_support,
            undistorted_tds_model_1,
            undistorted_tds_model_2):
        method_alias = \
            self._generate_prescaled_intra_disk_shapes_and_amplitude_sums
        kwargs = \
            {"undistorted_disk_support": undistorted_disk_support}
        prescaled_intra_disk_shapes, prescaled_amplitude_sums = \
            method_alias(**kwargs)

        max_abs_prescaled_amplitude_sum = \
            np.amax(np.abs(prescaled_amplitude_sums))
        
        kwargs = \
            {"undistorted_disk_support": undistorted_disk_support,
             "undistorted_tds_model_1": undistorted_tds_model_1,
             "undistorted_tds_model_2": undistorted_tds_model_2,
             "max_abs_prescaled_amplitude_sum": max_abs_prescaled_amplitude_sum}
        rescaling_factor_1 = \
            self._generate_rescaling_factor_1(**kwargs)

        max_abs_amplitude_sum = (max_abs_prescaled_amplitude_sum
                                 * rescaling_factor_1)
        intra_disk_shapes = tuple()
        if rescaling_factor_1 > 0:
            intra_disk_shapes += prescaled_intra_disk_shapes
            
            for intra_disk_shape in intra_disk_shapes:
                kwargs = {"intra_disk_shape": intra_disk_shape,
                          "rescaling_factor": rescaling_factor_1}
                self._rescale_intra_disk_shape(**kwargs)

        return intra_disk_shapes, max_abs_amplitude_sum



    def _generate_prescaled_intra_disk_shapes_and_amplitude_sums(
            self, undistorted_disk_support):
        intra_disk_shape_wishlist_keys = \
            self._generate_intra_disk_shape_wishlist_keys()

        intra_disk_shape_wishlist = \
            self._generate_intra_disk_shape_wishlist()
        
        unformatted_method_name_1 = "_generate_{}"
        unformatted_method_name_2 = "_generate_prescaled_amplitude_set_of_{}"
        prescaled_intra_disk_shapes = tuple()
        prescaled_amplitudes = tuple()

        for key in intra_disk_shape_wishlist_keys:
            prescaled_intra_disk_shape_subset_is_to_be_generated = \
                intra_disk_shape_wishlist[key]

            if prescaled_intra_disk_shape_subset_is_to_be_generated:
                method_name = unformatted_method_name_1.format(key)
                method_alias = getattr(self, method_name)
                kwargs = {"undistorted_disk_support": undistorted_disk_support}
                prescaled_intra_disk_shape_subset = method_alias(**kwargs)
                prescaled_intra_disk_shapes += prescaled_intra_disk_shape_subset

                method_name = unformatted_method_name_2.format(key)
                method_alias = getattr(self, method_name)
                kwargs = {"prescaled_intra_disk_shape_subset": \
                          prescaled_intra_disk_shape_subset}
                prescaled_amplitude_subset = method_alias(**kwargs)
                prescaled_amplitudes += prescaled_amplitude_subset

        kwargs = \
            {"prescaled_intra_disk_shapes": prescaled_intra_disk_shapes,
             "prescaled_amplitudes": prescaled_amplitudes}
        prescaled_amplitude_sums = \
            self._generate_prescaled_amplitude_sums(**kwargs)

        return prescaled_intra_disk_shapes, prescaled_amplitude_sums



    def _generate_intra_disk_shape_wishlist_keys(self):
        intra_disk_shape_wishlist_keys = ("uniform_disk_set",
                                          "plane_wave_set",
                                          "nonuniform_lune_set",
                                          "orbital_set",
                                          "peak_set")

        return intra_disk_shape_wishlist_keys



    def _generate_intra_disk_shape_wishlist(self):
        intra_disk_shape_wishlist = \
            {"uniform_disk_set": \
             self._rng.choice((True, False), p=(3/6, 1-3/6)).item(),
             "nonuniform_lune_set": \
             self._rng.choice((True, False), p=(1/3, 1-1/3)).item(),
             "plane_wave_set": \
             True,
             "orbital_set": \
             self._rng.choice((True, False), p=(1/2, 1-1/2)).item(),
             "peak_set": \
             self._rng.choice((True, False), p=(1/2, 1-1/2)).item()}

        return intra_disk_shape_wishlist



    def _generate_uniform_disk_set(self, undistorted_disk_support):
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        kwargs = {"center": (u_x_c_support, u_y_c_support),
                  "radius": u_R_support,
                  "intra_shape_val": 1,
                  "skip_validation_and_conversion": True}
        uniform_disk = fakecbed.shapes.Circle(**kwargs)
        uniform_disk_set = (uniform_disk,)

        return uniform_disk_set



    def _generate_prescaled_amplitude_set_of_uniform_disk_set(
            self, prescaled_intra_disk_shape_subset):
        prescaled_amplitude_set_of_uniform_disk_set = \
            tuple()
        for uniform_disk in prescaled_intra_disk_shape_subset:
            uniform_disk_core_attrs = \
                uniform_disk.get_core_attrs(deep_copy=False)
            A_uniform_disk = \
                uniform_disk_core_attrs["intra_shape_val"]

            prescaled_amplitude_set_of_uniform_disk_set += \
                (A_uniform_disk,)

        return prescaled_amplitude_set_of_uniform_disk_set



    def _generate_nonuniform_lune_set(self, undistorted_disk_support):
        kwargs = {"undistorted_disk_support": undistorted_disk_support}
        fg_ellipse = self._generate_fg_ellipse(**kwargs)
        bg_ellipse = self._generate_bg_ellipse(**kwargs)

        kwargs = {"bg_ellipse": bg_ellipse,
                  "fg_ellipse": fg_ellipse,
                  "skip_validation_and_conversion": True}
        uniform_lune = fakecbed.shapes.Lune(**kwargs)

        kwargs = \
            {"nonuniform_lune_support": uniform_lune}
        intra_support_shapes = \
            self._generate_intra_support_shapes_of_nonuniform_lune(**kwargs)

        kwargs = {"support": uniform_lune,
                  "intra_support_shapes": intra_support_shapes,
                  "skip_validation_and_conversion": True}
        nonuniform_lune = fakecbed.shapes.NonuniformBoundedShape(**kwargs)
        nonuniform_lune_set = (nonuniform_lune,)

        return nonuniform_lune_set



    def _generate_fg_ellipse(self, undistorted_disk_support):
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        u_R_fg_ellipse_min = (13/12)*u_R_support
        u_R_fg_ellipse_max = (5/4)*u_R_support
        u_R_fg_ellipse = self._rng.uniform(low=u_R_fg_ellipse_min,
                                           high=u_R_fg_ellipse_max)

        u_r_c_fg_ellipse_min = u_R_fg_ellipse - (2/3)*u_R_support
        u_r_c_fg_ellipse_max = u_R_fg_ellipse - (1/3)*u_R_support
        u_r_c_fg_ellipse = self._rng.uniform(low=u_r_c_fg_ellipse_min,
                                             high=u_r_c_fg_ellipse_max)

        u_phi_c_fg_ellipse = self._rng.uniform(low=0, high=2*np.pi)
    
        u_x_c_fg_ellipse = (u_x_c_support
                            + (u_r_c_fg_ellipse
                               * np.cos(u_phi_c_fg_ellipse))).item()
        u_y_c_fg_ellipse = (u_y_c_support
                            + (u_r_c_fg_ellipse
                               * np.sin(u_phi_c_fg_ellipse))).item()

        kwargs = {"center": (u_x_c_fg_ellipse, u_y_c_fg_ellipse),
                  "radius": u_R_fg_ellipse,
                  "intra_shape_val": 1,
                  "skip_validation_and_conversion": True}
        fg_ellipse = fakecbed.shapes.Circle(**kwargs)

        return fg_ellipse



    def _generate_bg_ellipse(self, undistorted_disk_support):
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        kwargs = {"center": (u_x_c_support, u_y_c_support),
                  "radius": u_R_support,
                  "intra_shape_val": 1,
                  "skip_validation_and_conversion": True}
        bg_ellipse = fakecbed.shapes.Circle(**kwargs)

        return bg_ellipse



    def _generate_intra_support_shapes_of_nonuniform_lune(
            self,
            nonuniform_lune_support):
        possible_functional_forms = ("asymmetric_exponential",
                                     "asymmetric_lorentzian",
                                     "asymmetric_gaussian")
        functional_form = self._rng.choice(possible_functional_forms).item()

        method_alias = \
            self._generate_center_of_intra_support_shape_of_nonuniform_lune
        center_of_intra_support_shape_of_nonuniform_lune = \
            method_alias(nonuniform_lune_support)

        nonuniform_lune_support_core_attrs = \
            nonuniform_lune_support.get_core_attrs(deep_copy=False)
        bg_ellipse = \
            nonuniform_lune_support_core_attrs["bg_ellipse"]

        bg_ellipse_core_attrs = bg_ellipse.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = bg_ellipse_core_attrs["center"]
        u_R_support = bg_ellipse_core_attrs["radius"]

        sigma_peak = self._rng.uniform(low=u_R_support/2, high=2*u_R_support)
        
        widths = sigma_peak * self._rng.uniform(low=0.8, high=1.2, size=4)
        widths = tuple(widths.tolist())

        abs_A_peak_min = 1/3
        abs_A_peak_max = 2*abs_A_peak_min
        abs_A_peak = self._rng.uniform(low=abs_A_peak_min, high=abs_A_peak_max)
        sign_A_peak = 2*self._rng.binomial(n=1, p=0.5) - 1
        A_peak = sign_A_peak*abs_A_peak

        kwargs = {"center": center_of_intra_support_shape_of_nonuniform_lune,
                  "widths": widths,
                  "rotation_angle": self._rng.uniform(low=0, high=2*np.pi),
                  "val_at_center": A_peak,
                  "functional_form": functional_form,
                  "skip_validation_and_conversion": True}
        peak = fakecbed.shapes.Peak(**kwargs)
        intra_support_shapes_of_nonuniform_lune = (peak,)

        return intra_support_shapes_of_nonuniform_lune



    def _generate_center_of_intra_support_shape_of_nonuniform_lune(
            self, nonuniform_lune_support):
        nonuniform_lune_support_core_attrs = \
            nonuniform_lune_support.get_core_attrs(deep_copy=False)
        bg_ellipse = \
            nonuniform_lune_support_core_attrs["bg_ellipse"]
        fg_ellipse = \
            nonuniform_lune_support_core_attrs["fg_ellipse"]

        bg_ellipse_core_attrs = bg_ellipse.get_core_attrs(deep_copy=False)
        u_x_c_bg_ellipse, u_y_c_bg_ellipse = bg_ellipse_core_attrs["center"]
        u_R_bg_ellipse = bg_ellipse_core_attrs["radius"]

        fg_ellipse_core_attrs = fg_ellipse.get_core_attrs(deep_copy=False)
        u_x_c_fg_ellipse, u_y_c_fg_ellipse = fg_ellipse_core_attrs["center"]
        u_R_fg_ellipse = fg_ellipse_core_attrs["radius"]

        u_r_c_fg_ellipse = np.sqrt((u_x_c_fg_ellipse-u_x_c_bg_ellipse)**2
                                   + (u_y_c_fg_ellipse-u_y_c_bg_ellipse)**2)
        
        u_phi_c_fg_ellipse = np.arctan2(u_y_c_fg_ellipse-u_y_c_bg_ellipse,
                                        u_x_c_fg_ellipse-u_x_c_bg_ellipse)

        u_r_c_peak_min = 0.5 * ((u_r_c_fg_ellipse+u_R_bg_ellipse)
                                + u_R_fg_ellipse)
        u_r_c_peak_max = u_r_c_fg_ellipse+u_R_bg_ellipse
        u_r_c_peak = self._rng.uniform(low=u_r_c_peak_min, high=u_r_c_peak_max)

        u_phi_c_peak = -(u_phi_c_fg_ellipse
                         + self._rng.uniform(low=-np.pi/6, high=np.pi/6))

        u_x_c_peak = (u_x_c_fg_ellipse
                      + u_r_c_peak*np.cos(u_phi_c_peak)).item()
        u_y_c_peak = (u_y_c_fg_ellipse
                      + u_r_c_peak*np.sin(u_phi_c_peak)).item()
        
        center_of_intra_support_shape_of_nonuniform_lune = (u_x_c_peak,
                                                            u_y_c_peak)

        return center_of_intra_support_shape_of_nonuniform_lune



    def _generate_prescaled_amplitude_set_of_nonuniform_lune_set(
            self, prescaled_intra_disk_shape_subset):
        prescaled_amplitude_set_of_nonuniform_lune_set = \
            tuple()
        for nonuniform_lune in prescaled_intra_disk_shape_subset:
            nonuniform_lune_core_attrs = \
                nonuniform_lune.get_core_attrs(deep_copy=False)
            peak = \
                nonuniform_lune_core_attrs["intra_support_shapes"][0]
                
            peak_core_attrs = \
                peak.get_core_attrs(deep_copy=False)
            A_peak = \
                peak_core_attrs["val_at_center"]

            prescaled_amplitude_set_of_nonuniform_lune_set += \
                (A_peak,)

        return prescaled_amplitude_set_of_nonuniform_lune_set



    def _generate_plane_wave_set(self, undistorted_disk_support):
        num_plane_waves = self._rng.choice((0, 1, 2), p=(1/2, 1/4, 1/4)).item()

        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        amplitude_min = 1/3/max(num_plane_waves, 1)
        amplitude_max = 2*amplitude_min

        plane_wave_set = tuple()
        for _ in range(num_plane_waves):
            amplitude = self._rng.uniform(low=amplitude_min, high=amplitude_max)

            wavelength = self._rng.uniform(low=(2*u_R_support)/9,
                                           high=(2*u_R_support)/3)

            propagation_direction = self._rng.uniform(low=0, high=2*np.pi)
            phase = self._rng.uniform(low=0, high=2*np.pi)

            kwargs = {"amplitude": amplitude,
                      "wavelength": wavelength,
                      "propagation_direction": propagation_direction,
                      "phase": phase,
                      "skip_validation_and_conversion": True}
            plane_wave = fakecbed.shapes.PlaneWave(**kwargs)
            plane_wave_set += (plane_wave,)

        return plane_wave_set



    def _generate_prescaled_amplitude_set_of_plane_wave_set(
            self, prescaled_intra_disk_shape_subset):
        prescaled_amplitude_set_of_plane_wave_set = tuple()
        for plane_wave in prescaled_intra_disk_shape_subset:
            plane_wave_core_attrs = plane_wave.get_core_attrs(deep_copy=False)
            amplitude = plane_wave_core_attrs["amplitude"]

            prescaled_amplitude_set_of_plane_wave_set += (amplitude,)

        return prescaled_amplitude_set_of_plane_wave_set



    def _generate_orbital_set(self, undistorted_disk_support):
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        u_r_c_orbital = self._rng.uniform(low=0, high=u_R_support)
        u_phi_c_orbital = self._rng.uniform(low=0, high=2*np.pi)
            
        u_x_c_orbital = (u_x_c_support
                         + u_r_c_orbital*np.cos(u_phi_c_orbital)).item()
        u_y_c_orbital = (u_y_c_support
                         + u_r_c_orbital*np.sin(u_phi_c_orbital)).item()

        n_orbital = self._rng.integers(low=1, high=5).item()
        l_orbital = self._rng.integers(low=0, high=n_orbital).item()
        m_orbital = self._rng.integers(low=0, high=l_orbital+1).item()

        a_orbital = self._generate_a_orbital(n_orbital,
                                             l_orbital,
                                             u_R_support)

        A_orbital = self._generate_A_orbital(n_orbital,
                                             l_orbital,
                                             m_orbital,
                                             a_orbital)

        kwargs = {"center": (u_x_c_orbital, u_y_c_orbital),
                  "principal_quantum_number": n_orbital,
                  "azimuthal_quantum_number": l_orbital,
                  "magnetic_quantum_number": m_orbital,
                  "effective_size": a_orbital,
                  "renormalization_factor": A_orbital,
                  "rotation_angle": self._rng.uniform(low=0, high=2*np.pi),
                  "skip_validation_and_conversion": True}
        orbital = fakecbed.shapes.Orbital(**kwargs)
        orbital_set = (orbital,)

        return orbital_set



    def _generate_a_orbital(self,
                            n_orbital,
                            l_orbital,
                            u_R_support):
        characteristic_sizes_of_orbitals = \
            self._characteristic_sizes_of_orbitals
        characteristic_size_of_orbital = \
            characteristic_sizes_of_orbitals[n_orbital][l_orbital]

        a_orbital = ((u_R_support/0.5)
                     * characteristic_size_of_orbital
                     * self._rng.uniform(low=3/5, high=7/5))

        return a_orbital



    def _generate_A_orbital(self,
                            n_orbital,
                            l_orbital,
                            m_orbital,
                            a_orbital):
        characteristic_scales_of_orbitals = \
            self._characteristic_scales_of_orbitals
        characteristic_scale_of_orbital = \
            characteristic_scales_of_orbitals[n_orbital][l_orbital][m_orbital]

        characteristic_sizes_of_orbitals = \
            self._characteristic_sizes_of_orbitals
        characteristic_size_of_orbital = \
            characteristic_sizes_of_orbitals[n_orbital][l_orbital]

        abs_A_orbital = ((a_orbital/characteristic_size_of_orbital)**3
                         * characteristic_scale_of_orbital
                         * self._rng.uniform(low=1, high=2))
        sign_A_orbital = 2*self._rng.binomial(n=1, p=0.5) - 1
        A_orbital = sign_A_orbital*abs_A_orbital

        return A_orbital



    def _generate_prescaled_amplitude_set_of_orbital_set(
            self, prescaled_intra_disk_shape_subset):
        characteristic_scales_of_orbitals = \
            self._characteristic_scales_of_orbitals
        characteristic_sizes_of_orbitals = \
                self._characteristic_sizes_of_orbitals

        prescaled_amplitude_set_of_orbital_set = tuple()
        for orbital in prescaled_intra_disk_shape_subset:
            orbital_core_attrs = orbital.get_core_attrs(deep_copy=False)
            n_orbital = orbital_core_attrs["principal_quantum_number"]
            l_orbital = orbital_core_attrs["azimuthal_quantum_number"]
            m_orbital = orbital_core_attrs["magnetic_quantum_number"]
            a_orbital = orbital_core_attrs["effective_size"]
            A_orbital = orbital_core_attrs["renormalization_factor"]

            characteristic_scales = \
                characteristic_scales_of_orbitals
            characteristic_scale = \
                characteristic_scales[n_orbital][l_orbital][m_orbital]

            characteristic_sizes = \
                characteristic_sizes_of_orbitals
            characteristic_size = \
                characteristic_sizes[n_orbital][l_orbital]

            prescaled_amplitude = \
                (A_orbital
                 / (a_orbital/characteristic_size)**3
                 / characteristic_scale)

            prescaled_amplitude_set_of_orbital_set += \
                (prescaled_amplitude,)

        return prescaled_amplitude_set_of_orbital_set



    def _generate_peak_set(self, undistorted_disk_support):
        num_peaks = self._rng.integers(low=0, high=6).item()

        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        possible_functional_forms = ("asymmetric_exponential",
                                     "asymmetric_lorentzian")
        functional_form = self._rng.choice(possible_functional_forms).item()

        peak_set = tuple()
        for _ in range(num_peaks):
            abs_A_peak = self._rng.uniform(low=1, high=2)
            sign_peak = 2*self._rng.binomial(n=1, p=0.5) - 1
            A_peak = sign_peak*abs_A_peak

            sigma_peak = self._rng.uniform(low=u_R_support/(4*num_peaks),
                                           high=u_R_support/(2*num_peaks))
            
            widths = sigma_peak * self._rng.uniform(low=0.8, high=1.2, size=4)
            widths = tuple(widths.tolist())

            u_r_c_peak = self._rng.uniform(low=0, high=u_R_support+sigma_peak)
            u_phi_c_peak = self._rng.uniform(low=0, high=2*np.pi)
            
            u_x_c_peak = (u_x_c_support
                          + u_r_c_peak*np.cos(u_phi_c_peak)).item()
            u_y_c_peak = (u_y_c_support
                          + u_r_c_peak*np.sin(u_phi_c_peak)).item()

            kwargs = {"center": (u_x_c_peak, u_y_c_peak),
                      "widths": widths,
                      "rotation_angle": self._rng.uniform(low=0, high=2*np.pi),
                      "val_at_center": A_peak,
                      "functional_form": functional_form,
                      "skip_validation_and_conversion": True}
            peak = fakecbed.shapes.Peak(**kwargs)
            peak_set += (peak,)

        return peak_set



    def _generate_prescaled_amplitude_set_of_peak_set(
            self, prescaled_intra_disk_shape_subset):
        prescaled_amplitude_set_of_peak_set = tuple()
        for peak in prescaled_intra_disk_shape_subset:
            peak_core_attrs = peak.get_core_attrs(deep_copy=False)
            A_peak = peak_core_attrs["val_at_center"]

            prescaled_amplitude_set_of_peak_set += (A_peak,)

        return prescaled_amplitude_set_of_peak_set



    def _generate_prescaled_amplitude_sums(self,
                                           prescaled_intra_disk_shapes,
                                           prescaled_amplitudes):
        num_peaks = 0

        prescaled_amplitude_sums = np.array((0.0,))
        for shape_idx, shape in enumerate(prescaled_intra_disk_shapes):
            shape_type_subset_1 = (fakecbed.shapes.Orbital,
                                   fakecbed.shapes.NonuniformBoundedShape,
                                   fakecbed.shapes.Peak)
            if isinstance(shape, shape_type_subset_1):
                shape_type_subset_2 = shape_type_subset_1[:2]
                if isinstance(shape, shape_type_subset_2):
                    prescaled_amplitude = prescaled_amplitudes[shape_idx]
                    prescaled_amplitude_sum_subset_1 = prescaled_amplitude_sums
                    prescaled_amplitude_sum_subset_2 = (prescaled_amplitude_sums
                                                        + prescaled_amplitude)
                    arrays_to_join = (prescaled_amplitude_sum_subset_1,
                                      prescaled_amplitude_sum_subset_2)
                    prescaled_amplitude_sums = np.concatenate(arrays_to_join)
                else:
                    num_peaks = len(prescaled_intra_disk_shapes) - shape_idx
                    break
            else:
                prescaled_amplitude = prescaled_amplitudes[shape_idx]
                prescaled_amplitude_sums[0] += prescaled_amplitude

        if num_peaks > 0:
            binary_seqs = tuple(itertools.product((0, 1), repeat=num_peaks))
            num_binary_seqs = len(binary_seqs)

            arrays_to_join = num_binary_seqs*(prescaled_amplitude_sums,)
            prescaled_amplitude_sums = np.concatenate(arrays_to_join)
            
            for binary_seq_idx, binary_seq in enumerate(binary_seqs):
                for peak_idx in range(num_peaks):
                    shape_idx = -(peak_idx+1)
                    prescaled_amplitude = prescaled_amplitudes[shape_idx]

                    M = len(prescaled_amplitude_sums) // num_binary_seqs
                    sum_idx_subset = range(M*binary_seq_idx,
                                           M*(binary_seq_idx+1))
                    
                    for sum_idx in sum_idx_subset:
                        prescaled_amplitude_sums[sum_idx] += prescaled_amplitude
                        
        return prescaled_amplitude_sums



    def _generate_rescaling_factor_1(self,
                                     undistorted_disk_support,
                                     undistorted_tds_model_1,
                                     undistorted_tds_model_2,
                                     max_abs_prescaled_amplitude_sum):
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]

        undistorted_tds_model_2_core_attrs = \
            undistorted_tds_model_2.get_core_attrs(deep_copy=False)
        constant_bg = \
            undistorted_tds_model_2_core_attrs["constant_bg"]

        kwargs = {"u_x": torch.tensor(((u_x_c_support,),), device=self._device),
                  "u_y": torch.tensor(((u_y_c_support,),), device=self._device),
                  "device": self._device,
                  "skip_validation_and_conversion": True}
        temp_1 = undistorted_tds_model_1.eval(**kwargs)[0, 0].item()
        
        temp_2 = 0.25 + abs(self._rng.normal(loc=0, scale=4))
        
        temp_3 = 2*constant_bg
        
        temp_4 = max(temp_1*temp_2, temp_3)
        
        temp_5 = (max_abs_prescaled_amplitude_sum
                  if (max_abs_prescaled_amplitude_sum != 0)
                  else 1)
        
        temp_6 = self._rng.choice((temp_5, 1))
        
        rescaling_factor_1 = (abs(temp_4/temp_6).item()
                              if (temp_4>temp_6)
                              else 0)

        return rescaling_factor_1



    def _rescale_intra_disk_shape(self, intra_disk_shape, rescaling_factor):
        intra_disk_shape_core_attrs = \
            intra_disk_shape.get_core_attrs(deep_copy=False)

        if isinstance(intra_disk_shape, fakecbed.shapes.NonuniformBoundedShape):
            peak = intra_disk_shape_core_attrs["intra_support_shapes"][0]

            peak_core_attrs = peak.get_core_attrs(deep_copy=False)
            A_peak = peak_core_attrs["val_at_center"]

            attr_name = "val_at_center"
            attr_val = A_peak*rescaling_factor
            kwargs = {"new_core_attr_subset_candidate": {attr_name: attr_val},
                      "skip_validation_and_conversion": True}
            peak.update(**kwargs)

            attr_name = "intra_support_shapes"
            attr_val = (peak,)
        else:
            for key in intra_disk_shape_core_attrs:
                if ("val" in key) or ("amplitude" in key) or ("factor" in key):
                    attr_name = key
                    attr_val = (intra_disk_shape_core_attrs[key]
                                * rescaling_factor)

        kwargs = {"new_core_attr_subset_candidate": {attr_name: attr_val},
                  "skip_validation_and_conversion": True}
        intra_disk_shape.update(**kwargs)

        return None



    def _perform_additional_rescaling_to_undistorted_disks(
            self, undistorted_disks, max_abs_amplitude_sums):
        num_disks = len(undistorted_disks)

        num_disks_to_rescale = self._rng.integers(low=1, high=4).item()

        kwargs = {"a": range(0, num_disks),
                  "size": num_disks_to_rescale,
                  "replace": False,
                  "p": None}
        disk_indices = self._rng.choice(**kwargs)

        for disk_idx in disk_indices:
            temp_1 = np.sort(max_abs_amplitude_sums)[-2].item()
            temp_2 = self._rng.uniform(low=10, high=11)
            temp_3 = (max_abs_amplitude_sums[disk_idx]
                      if (max_abs_amplitude_sums[disk_idx] != 0)
                      else 1)
            temp_4 = self._rng.uniform(low=1/5, high=1/3)
            rescaling_factor_2 = (temp_1*temp_2/temp_3
                                  if disk_idx > 0
                                  else temp_4)

            undistorted_disk = \
                undistorted_disks[disk_idx]
            undistorted_disk_core_attrs = \
                undistorted_disk.get_core_attrs(deep_copy=False)
            intra_disk_shapes = \
                undistorted_disk_core_attrs["intra_support_shapes"]

            for intra_disk_shape in intra_disk_shapes:
                kwargs = {"intra_disk_shape": intra_disk_shape,
                          "rescaling_factor": rescaling_factor_2}
                self._rescale_intra_disk_shape(**kwargs)

            attr_name = "intra_disk_shapes"
            attr_val = intra_disk_shapes
            kwargs = {"new_core_attr_subset_candidate": {attr_name: attr_val},
                      "skip_validation_and_conversion": True}
            undistorted_disk.update(**kwargs)

            max_abs_amplitude_sums[disk_idx] *= rescaling_factor_2

        return None



    def _generate_undistorted_misc_shapes(self,
                                          undistorted_tds_model_1,
                                          undistorted_disks,
                                          max_abs_amplitude_sums):
        no_misc_shapes_are_present = self._rng.choice((False, True),
                                                      p=(1/2, 1-1/2)).item()

        if no_misc_shapes_are_present:
            undistorted_misc_shapes = \
                tuple()
        else:
            kwargs = \
                {"undistorted_disks": undistorted_disks,
                 "undistorted_tds_model_1": undistorted_tds_model_1,
                 "max_abs_amplitude_sums": max_abs_amplitude_sums}
            undistorted_misc_shapes = \
                self._generate_undistorted_nonuniform_bands(**kwargs)

        return undistorted_misc_shapes



    def _generate_undistorted_nonuniform_bands(self,
                                               undistorted_disks,
                                               undistorted_tds_model_1,
                                               max_abs_amplitude_sums):
        num_disks = len(undistorted_disks)
        
        num_bands = self._rng.integers(low=1, high=max(num_disks, 2)).item()

        kwargs = \
            {"undistorted_disks": undistorted_disks, "num_bands": num_bands}
        num_bands_pinned_to_disks = \
            self._generate_num_bands_pinned_to_disks(**kwargs)
        
        num_bands_not_pinned_to_disks = num_bands - num_bands_pinned_to_disks

        kwargs = {"a": range(1, num_disks),
                  "size": num_bands_pinned_to_disks,
                  "replace": False,
                  "p": None}
        disk_idx_subset_1 = self._rng.choice(**kwargs)
        
        kwargs["size"] = num_bands_not_pinned_to_disks
        disk_idx_subset_2 = self._rng.choice(**kwargs)
        disk_idx_subsets = (disk_idx_subset_1, disk_idx_subset_2)

        undistorted_nonuniform_bands = tuple()
        for band_is_pinned_to_disk in (True, False):
            disk_idx_subset = (disk_idx_subset_1
                               if band_is_pinned_to_disk
                               else disk_idx_subset_2)
            for disk_idx in disk_idx_subset:
                undistorted_disk = undistorted_disks[disk_idx]
                max_abs_amplitude_sum = max_abs_amplitude_sums[disk_idx]

                method_alias = self._generate_undistorted_nonuniform_band
                kwargs = {"undistorted_disk": undistorted_disk,
                          "band_is_pinned_to_disk": band_is_pinned_to_disk,
                          "undistorted_tds_model_1": undistorted_tds_model_1,
                          "max_abs_amplitude_sum": max_abs_amplitude_sum}
                undistorted_nonuniform_band = method_alias(**kwargs)
                undistorted_nonuniform_bands += (undistorted_nonuniform_band,)

        return undistorted_nonuniform_bands



    def _generate_num_bands_pinned_to_disks(self, undistorted_disks, num_bands):
        undistorted_disk_core_attrs = \
            undistorted_disks[0].get_core_attrs(deep_copy=False)
        undistorted_disk_support = \
            undistorted_disk_core_attrs["support"]

        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]
        
        threshold = 1/20
        min_num_bands_pinned_to_disks = 0
        max_num_bands_pinned_to_disks = (0
                                         if (u_R_support > threshold)
                                         else num_bands)
        
        kwargs = {"low": min_num_bands_pinned_to_disks,
                  "high": max_num_bands_pinned_to_disks+1}
        num_bands_pinned_to_disks = self._rng.integers(**kwargs).item()

        return num_bands



    def _generate_undistorted_nonuniform_band(self,
                                              undistorted_disk,
                                              band_is_pinned_to_disk,
                                              undistorted_tds_model_1,
                                              max_abs_amplitude_sum):
        end_pt_1, end_pt_2 = self._generate_band_end_pts(undistorted_disk,
                                                         band_is_pinned_to_disk)
        
        band_width = self._generate_band_width(undistorted_disk)

        method_alias = self._generate_intra_band_val_without_decay
        intra_band_val_without_decay = method_alias(undistorted_tds_model_1,
                                                    max_abs_amplitude_sum)

        Band = fakecbed.shapes.Band
        kwargs = {"end_pt_1": end_pt_1,
                  "end_pt_2": end_pt_2,
                  "width": band_width,
                  "intra_shape_val": intra_band_val_without_decay,
                  "skip_validation_and_conversion": True}
        undistorted_uniform_band = Band(**kwargs)

        NonuniformBoundedShape = fakecbed.shapes.NonuniformBoundedShape
        kwargs = {"support": undistorted_uniform_band,
                  "intra_support_shapes": (undistorted_tds_model_1,),
                  "skip_validation_and_conversion": True}
        undistorted_nonuniform_band = NonuniformBoundedShape(**kwargs)

        return undistorted_nonuniform_band



    def _generate_band_end_pts(self, undistorted_disk, band_is_pinned_to_disk):
        undistorted_disk_core_attrs = \
            undistorted_disk.get_core_attrs(deep_copy=False)
        undistorted_disk_support = \
            undistorted_disk_core_attrs["support"]

        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_x_c_support, u_y_c_support = \
            undistorted_disk_support_core_attrs["center"]
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        r_band_min = 0
        r_band_max = (0 if band_is_pinned_to_disk else 5/4)*u_R_support
        r_band = self._rng.uniform(low=r_band_min, high=r_band_max)

        phi_band = self._rng.uniform(low=0, high=2*np.pi)

        x_c_band = u_x_c_support + r_band*np.cos(phi_band).item()
        y_c_band = u_y_c_support + r_band*np.sin(phi_band).item()

        theta_band = self._rng.uniform(low=0, high=2*np.pi)

        L_1_band = self._rng.uniform(low=0, high=np.sqrt(2))
        
        L_2_band = self._rng.uniform(low=0, high=np.sqrt(2))

        end_pt_1 = (x_c_band + L_1_band*np.cos(theta_band).item(),
                    y_c_band + L_1_band*np.sin(theta_band).item())
        end_pt_2 = (x_c_band + L_2_band*np.cos(theta_band+np.pi).item(),
                    y_c_band + L_2_band*np.sin(theta_band+np.pi).item())

        return end_pt_1, end_pt_2



    def _generate_intra_band_val_without_decay(self,
                                               undistorted_tds_model_1,
                                               max_abs_amplitude_sum):
        kwargs = \
            {"undistorted_tds_model_1": undistorted_tds_model_1}
        reference_pt_of_distortion_model_generator = \
            self._generate_reference_pt_of_distortion_model_generator(**kwargs)

        u_x_c_support, u_y_c_support = \
            reference_pt_of_distortion_model_generator

        kwargs = {"u_x": torch.tensor(((u_x_c_support,),), device=self._device),
                  "u_y": torch.tensor(((u_y_c_support,),), device=self._device),
                  "device": self._device,
                  "skip_validation_and_conversion": True}
        A_unnormalized_decay_peak = undistorted_tds_model_1.eval(**kwargs)[0, 0]
        A_unnormalized_decay_peak = A_unnormalized_decay_peak.item()

        scale_factor = (A_unnormalized_decay_peak
                        if (A_unnormalized_decay_peak != 0)
                        else 1)

        abs_A_band_min = abs(max_abs_amplitude_sum
                             / scale_factor
                             / 3)
        abs_A_band_max = 2*abs_A_band_min
        abs_A_band = self._rng.uniform(low=abs_A_band_min, high=abs_A_band_max)
        sign_band = 2*self._rng.binomial(n=1, p=0.5) - 1
        A_band = sign_band*abs_A_band

        intra_band_val_without_decay = A_band

        return intra_band_val_without_decay



    def _generate_band_width(self, undistorted_disk):
        undistorted_disk_core_attrs = \
            undistorted_disk.get_core_attrs(deep_copy=False)
        undistorted_disk_support = \
            undistorted_disk_core_attrs["support"]
        
        undistorted_disk_support_core_attrs = \
            undistorted_disk_support.get_core_attrs(deep_copy=False)
        u_R_support = \
            undistorted_disk_support_core_attrs["radius"]

        w_band = self._rng.uniform(low=(1/5)*u_R_support,
                                   high=(99/100)*u_R_support)

        band_width = w_band

        return band_width



    def _generate_cold_pixels(self):
        N = self._num_pixels_across_each_cbed_pattern

        min_fraction_cold_pixels = 0
        min_num_cold_pixels = int(np.ceil(min_fraction_cold_pixels*N))

        max_fraction_cold_pixels = 0.02
        max_num_cold_pixels = int(np.floor(max_fraction_cold_pixels*N))

        num_cold_pixels = self._rng.integers(low=min_num_cold_pixels,
                                             high=max_num_cold_pixels+1).item()

        num_possible_cold_pixel_labels_to_sample_from = N*N

        kwargs = {"a": range(num_possible_cold_pixel_labels_to_sample_from),
                  "size": num_cold_pixels,
                  "replace": False,
                  "p": None}
        cold_pixel_labels = tuple(self._rng.choice(**kwargs).tolist())

        cold_pixels = tuple()
        for cold_pixel_label in cold_pixel_labels:
            cold_pixel = (cold_pixel_label//N, cold_pixel_label%N)
            cold_pixels += (cold_pixel,)

        return cold_pixels



def _generate_keys_of_unnormalizable_ml_data_dict_elems():
    unformatted_func_name = ("_generate_keys_of_unnormalizable"
                             "_ml_data_dict_elems{}_having_decoders")

    keys_of_unnormalizable_ml_data_dict_elems = tuple()
    global_symbol_table = globals()
    for format_arg in ("_not", ""):
        args = (format_arg,)
        func_name = unformatted_func_name.format(*args)
        func_alias = global_symbol_table[func_name]
        keys_of_unnormalizable_ml_data_dict_elems += func_alias()

    return keys_of_unnormalizable_ml_data_dict_elems



def _generate_keys_of_unnormalizable_ml_data_dict_elems_not_having_decoders():
    keys_of_unnormalizable_ml_data_dict_elems_not_having_decoders = \
        ("cbed_pattern_images",
         "disk_overlap_maps",
         "disk_clipping_registries",
         "disk_objectness_sets")

    return keys_of_unnormalizable_ml_data_dict_elems_not_having_decoders



def _generate_keys_of_unnormalizable_ml_data_dict_elems_having_decoders():
    keys_of_unnormalizable_ml_data_dict_elems_having_decoders = tuple()

    return keys_of_unnormalizable_ml_data_dict_elems_having_decoders



def _generate_keys_of_normalizable_ml_data_dict_elems():
    keys_of_normalizable_ml_data_dict_elems = \
        _generate_keys_of_normalizable_ml_data_dict_elems_not_having_decoders()
    keys_of_normalizable_ml_data_dict_elems += \
         _generate_keys_of_normalizable_ml_data_dict_elems_having_decoders()

    return keys_of_normalizable_ml_data_dict_elems



def _generate_keys_of_normalizable_ml_data_dict_elems_not_having_decoders():
    keys_of_normalizable_ml_data_dict_elems_not_having_decoders = \
        ("common_undistorted_disk_radii", "undistorted_disk_center_sets")
    keys_of_normalizable_ml_data_dict_elems_not_having_decoders += \
        _generate_keys_related_to_distortion_params()

    return keys_of_normalizable_ml_data_dict_elems_not_having_decoders



def _generate_keys_related_to_distortion_params():
    keys_related_to_distortion_params = \
        ("distortion_centers",
         "quadratic_radial_distortion_amplitudes",
         "elliptical_distortion_vectors",
         "spiral_distortion_amplitudes",
         "parabolic_distortion_vectors")

    return keys_related_to_distortion_params



def _generate_keys_of_normalizable_ml_data_dict_elems_having_decoders():
    keys_of_normalizable_ml_data_dict_elems_having_decoders = tuple()

    return keys_of_normalizable_ml_data_dict_elems_having_decoders



def _generate_keys_of_ml_data_dict_elems_having_decoders():
    keys_of_ml_data_dict_elems_having_decoders = \
        _generate_keys_of_unnormalizable_ml_data_dict_elems_having_decoders()
    keys_of_ml_data_dict_elems_having_decoders += \
        _generate_keys_of_normalizable_ml_data_dict_elems_having_decoders()

    return keys_of_ml_data_dict_elems_having_decoders



def _generate_all_valid_ml_data_dict_keys():
    ml_data_dict_keys = _generate_keys_of_unnormalizable_ml_data_dict_elems()
    ml_data_dict_keys += _generate_keys_of_normalizable_ml_data_dict_elems()
    
    return ml_data_dict_keys



def _generate_cbed_pattern_signal(cbed_pattern_generator):
    current_func_name = "_generate_cbed_pattern_signal"

    try:
        cbed_pattern = cbed_pattern_generator.generate()
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        args = (" ``cbed_pattern_generator``", "")
        err_msg = unformatted_err_msg.format(*args)
        raise RuntimeError(err_msg)

    try:
        accepted_types = (fakecbed.discretized.CBEDPattern,)
        kwargs = {"obj": cbed_pattern,
                  "obj_name": "cbed_pattern",
                  "accepted_types": accepted_types}
        czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    except:
        err_msg = globals()[current_func_name+"_err_msg_2"]
        raise TypeError(err_msg)

    cbed_pattern_signal = cbed_pattern.get_signal(deep_copy=False)

    return cbed_pattern_signal



def _check_cbed_pattern_signal(cbed_pattern_signal,
                               max_num_disks_in_any_cbed_pattern):
    disk_absence_registry = \
        np.array(cbed_pattern_signal.metadata.FakeCBED.disk_absence_registry)
    num_disk_in_cbed_pattern_image = \
        (~disk_absence_registry).sum()

    current_func_name = "_check_cbed_pattern_signal"
    
    if num_disk_in_cbed_pattern_image > max_num_disks_in_any_cbed_pattern:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)

    return cbed_pattern_signal



def _extract_ml_data_dict_from_cbed_pattern_signal(
        cbed_pattern_signal, max_num_disks_in_any_cbed_pattern):
    func_alias = _extract_disk_related_features_from_cbed_pattern_signal
    kwargs = {"cbed_pattern_signal": \
              cbed_pattern_signal,
              "max_num_disks_in_any_cbed_pattern": \
              max_num_disks_in_any_cbed_pattern}
    ml_data_dict = func_alias(**kwargs)

    cbed_pattern_image = cbed_pattern_signal.data[0]
    ml_data_dict["cbed_pattern_images"] = np.expand_dims(cbed_pattern_image,
                                                         axis=0)

    func_alias = _extract_distortion_param_val_set_from_cbed_pattern_signal
    distortion_param_val_set = func_alias(cbed_pattern_signal)

    key_subset = _generate_keys_of_ml_data_dict_elems_having_decoders()
    ml_data_dict = {**ml_data_dict, **{key: None for key in key_subset}}
        
    key_subset = _generate_keys_related_to_distortion_params()
    for key_idx, key in enumerate(key_subset):
        distortion_param_val = distortion_param_val_set[key_idx]
        ml_data_dict[key] = np.expand_dims(distortion_param_val, axis=0)

    return ml_data_dict



def _extract_disk_related_features_from_cbed_pattern_signal(
        cbed_pattern_signal, max_num_disks_in_any_cbed_pattern):
    disk_overlap_map = cbed_pattern_signal.data[2]

    func_alias = \
        _extract_common_undistorted_disk_radius_from_cbed_pattern_signal
    common_undistorted_disk_radius = \
        func_alias(cbed_pattern_signal)

    func_alias = _extract_intra_disk_avgs_from_cbed_pattern_signal
    intra_disk_avgs = func_alias(cbed_pattern_signal)

    func_alias = _extract_disk_clipping_registry_from_cbed_pattern_signal
    kwargs = {"cbed_pattern_signal": \
              cbed_pattern_signal,
              "intra_disk_avgs": \
              intra_disk_avgs,
              "new_disk_order": \
              np.argsort(intra_disk_avgs)[::-1],
              "max_num_disks_in_any_cbed_pattern": \
              max_num_disks_in_any_cbed_pattern}
    disk_clipping_registry = func_alias(**kwargs)

    func_alias = _extract_undistorted_disk_center_set_from_cbed_pattern_signal
    undistorted_disk_center_set = func_alias(**kwargs)

    func_alias = _extract_disk_objectness_set_from_cbed_pattern_signal
    del kwargs["cbed_pattern_signal"]
    disk_objectness_set = func_alias(**kwargs)

    ml_data_dict = \
        {"disk_overlap_maps": [disk_overlap_map],
         "common_undistorted_disk_radii": [common_undistorted_disk_radius],
         "disk_clipping_registries": [disk_clipping_registry],
         "undistorted_disk_center_sets": [undistorted_disk_center_set],
         "disk_objectness_sets": [disk_objectness_set]}
    for key in ml_data_dict:
        ml_data_dict[key] = np.expand_dims(ml_data_dict[key][0], axis=0)

    return ml_data_dict



def _extract_common_undistorted_disk_radius_from_cbed_pattern_signal(
        cbed_pattern_signal):
    path_to_item = \
        "FakeCBED.pre_serialized_core_attrs.undistorted_disks"
    pre_serializable_rep_of_undistorted_disk = \
        cbed_pattern_signal.metadata.get_item(path_to_item)[0]
    pre_serializable_rep_of_undistorted_disk_support = \
        pre_serializable_rep_of_undistorted_disk["support"]
    common_undistorted_disk_radius = \
        np.array(pre_serializable_rep_of_undistorted_disk_support["radius"])

    return common_undistorted_disk_radius



def _extract_intra_disk_avgs_from_cbed_pattern_signal(cbed_pattern_signal):
    path_to_item = "FakeCBED.num_disks"
    num_disks = cbed_pattern_signal.metadata.get_item(path_to_item)

    num_pixels_across_cbed_pattern = cbed_pattern_signal.data.shape[-1]

    undistorted_disk_radii = np.zeros((num_disks,))
    intra_disk_avgs = np.zeros((num_disks,))

    cbed_pattern_image = cbed_pattern_signal.inav[0].data

    current_func_name = "_extract_intra_disk_avgs_from_cbed_pattern_signal"

    for disk_idx in range(num_disks):
        path_to_item = \
            "FakeCBED.pre_serialized_core_attrs.undistorted_disks"
        pre_serializable_rep_of_undistorted_disk = \
            cbed_pattern_signal.metadata.get_item(path_to_item)[disk_idx]
        pre_serializable_rep_of_undistorted_disk_support = \
            pre_serializable_rep_of_undistorted_disk["support"]

        undistorted_disk_radii[disk_idx] = \
            pre_serializable_rep_of_undistorted_disk_support["radius"]

        if disk_idx > 0:
            current_radius = undistorted_disk_radii[disk_idx]
            previous_radius = undistorted_disk_radii[disk_idx-1]
            err_msg = globals()[current_func_name+"_err_msg_1"]
            if current_radius != previous_radius:
                raise ValueError(err_msg)

        support_data_of_current_disk = cbed_pattern_signal.inav[3+disk_idx].data

        intra_disk_sum = (cbed_pattern_image*support_data_of_current_disk).sum()
        disk_area = (support_data_of_current_disk.sum()
                     / num_pixels_across_cbed_pattern**2)
        intra_disk_avgs[disk_idx] = ((intra_disk_sum/disk_area)
                                     if (disk_area > 0)
                                     else 0)

    return intra_disk_avgs



def _extract_disk_clipping_registry_from_cbed_pattern_signal(
        cbed_pattern_signal,
        intra_disk_avgs,
        new_disk_order,
        max_num_disks_in_any_cbed_pattern):
    path_to_item = "FakeCBED.disk_clipping_registry"
    disk_clipping_registry = cbed_pattern_signal.metadata.get_item(path_to_item)
    disk_clipping_registry = np.array(disk_clipping_registry)
    disk_clipping_registry = disk_clipping_registry[new_disk_order]

    num_disks = len(intra_disk_avgs)
    num_elems_to_pad = max(max_num_disks_in_any_cbed_pattern-num_disks, 0)
    single_dim_slice = slice(0, max_num_disks_in_any_cbed_pattern)
    
    kwargs = {"array": disk_clipping_registry,
              "pad_width": (0, num_elems_to_pad),
              "mode": "constant",
              "constant_values": True}
    disk_clipping_registry = np.pad(**kwargs)[single_dim_slice]

    return disk_clipping_registry



def _extract_undistorted_disk_center_set_from_cbed_pattern_signal(
        cbed_pattern_signal,
        intra_disk_avgs,
        new_disk_order,
        max_num_disks_in_any_cbed_pattern):
    num_disks = len(intra_disk_avgs)
    undistorted_disk_center_set = np.ones((num_disks, 2))/2

    for disk_idx, intra_disk_avg in enumerate(intra_disk_avgs):
        disk_is_present_in_image = (intra_disk_avg > 0)
        
        if disk_is_present_in_image:
            path_to_item = \
                "FakeCBED.pre_serialized_core_attrs.undistorted_disks"
            pre_serializable_rep_of_undistorted_disk = \
                cbed_pattern_signal.metadata.get_item(path_to_item)[disk_idx]
            pre_serializable_rep_of_undistorted_disk_support = \
                pre_serializable_rep_of_undistorted_disk["support"]
            undistorted_disk_center_set[disk_idx] = \
                pre_serializable_rep_of_undistorted_disk_support["center"]

    undistorted_disk_center_set = undistorted_disk_center_set[new_disk_order]

    num_rows_to_pad = max(max_num_disks_in_any_cbed_pattern-num_disks, 0)
    single_dim_slice = slice(0, max_num_disks_in_any_cbed_pattern)

    kwargs = {"array": undistorted_disk_center_set,
              "pad_width": ((0, num_rows_to_pad), (0, 0)),
              "mode": "constant",
              "constant_values": 0.5}
    undistorted_disk_center_set = np.pad(**kwargs)[single_dim_slice]

    return undistorted_disk_center_set



def _extract_disk_objectness_set_from_cbed_pattern_signal(
        intra_disk_avgs, new_disk_order, max_num_disks_in_any_cbed_pattern):
    num_disks = len(intra_disk_avgs)

    disk_objectness_set = (intra_disk_avgs > 0).astype("float")
    disk_objectness_set = disk_objectness_set[new_disk_order]

    num_elems_to_pad = max(max_num_disks_in_any_cbed_pattern-num_disks, 0)
    single_dim_slice = slice(0, max_num_disks_in_any_cbed_pattern)

    kwargs = {"array": disk_objectness_set,
              "pad_width": (0, num_elems_to_pad),
              "mode": "constant",
              "constant_values": 0.0}
    disk_objectness_set = np.pad(**kwargs)[single_dim_slice]

    return disk_objectness_set



_module_alias = emicroml.modelling._common
_tol_for_comparing_floats = _module_alias._tol_for_comparing_floats



def _extract_distortion_param_val_set_from_cbed_pattern_signal(
        cbed_pattern_signal):
    path_to_item_1 = ("FakeCBED.pre_serialized_core_attrs.distortion_model"
                      ".coord_transform_params")
    path_to_item_2 = path_to_item_1 + ".center"
    path_to_item_3 = path_to_item_1 + ".radial_cosine_coefficient_matrix"
    path_to_item_4 = path_to_item_1 + ".radial_sine_coefficient_matrix"
    path_to_item_5 = path_to_item_1 + ".tangential_cosine_coefficient_matrix"

    serializable_rep_of_coord_transform_params = \
        cbed_pattern_signal.metadata.get_item(path_to_item_1).as_dictionary()
    distortion_center = \
        cbed_pattern_signal.metadata.get_item(path_to_item_2)
    radial_cosine_coefficient_matrix = \
        cbed_pattern_signal.metadata.get_item(path_to_item_3)
    radial_sine_coefficient_matrix = \
        cbed_pattern_signal.metadata.get_item(path_to_item_4)
    tangential_cosine_coefficient_matrix = \
        cbed_pattern_signal.metadata.get_item(path_to_item_5)

    kwargs = \
        {"serializable_rep": serializable_rep_of_coord_transform_params}
    coord_transform_params = \
        _de_pre_serialize_coord_transform_params(**kwargs)

    distortion_model_is_not_standard = \
        (not coord_transform_params.is_corresponding_model_standard)
    
    if distortion_model_is_not_standard:
        current_func_name = ("_extract_distortion_param_val_set"
                             "_from_cbed_pattern_signal")
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    quadratic_radial_distortion_amplitude = \
        radial_cosine_coefficient_matrix[0][2]
    elliptical_distortion_vector = \
        (radial_cosine_coefficient_matrix[2][0],
         radial_sine_coefficient_matrix[1][0])
    spiral_distortion_amplitude = \
        tangential_cosine_coefficient_matrix[0][2]
    parabolic_distortion_vector = \
        (radial_cosine_coefficient_matrix[1][1],
         radial_sine_coefficient_matrix[0][1])

    return (distortion_center,
            quadratic_radial_distortion_amplitude,
            elliptical_distortion_vector,
            spiral_distortion_amplitude,
            parabolic_distortion_vector)



def _de_pre_serialize_coord_transform_params(serializable_rep):
    key = \
        "coord_transform_params"
    de_pre_serialize_coord_transform_params = \
        distoptica.DistortionModel.get_de_pre_serialization_funcs()[key]
    
    kwargs = {"serializable_rep": serializable_rep}
    coord_transform_params = de_pre_serialize_coord_transform_params(**kwargs)

    return coord_transform_params
        



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._UnnormalizedMLDataInstanceGenerator
class _UnnormalizedMLDataInstanceGenerator(_cls_alias):
    def __init__(self,
                 cbed_pattern_generator,
                 max_num_disks_in_any_cbed_pattern):
        self._cbed_pattern_generator = \
            cbed_pattern_generator
        self._max_num_disks_in_any_cbed_pattern = \
            max_num_disks_in_any_cbed_pattern

        self._expected_cbed_pattern_dims_in_pixels = None
        
        cbed_pattern_signal = \
            _generate_cbed_pattern_signal(cbed_pattern_generator)
        self._expected_cbed_pattern_dims_in_pixels = \
            cbed_pattern_signal.axes_manager.signal_shape

        cached_ml_data_instances = self._generate(num_ml_data_instances=1)

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._UnnormalizedMLDataInstanceGenerator
        kwargs = {"cached_ml_data_instances": cached_ml_data_instances}
        cls_alias.__init__(self, **kwargs)

        return None



    def _generate_ml_data_dict_containing_only_one_ml_data_instance(self):
        max_num_disks_in_any_cbed_pattern = \
            self._max_num_disks_in_any_cbed_pattern
        cbed_pattern_generator = \
            self._cbed_pattern_generator
        cbed_pattern_signal = \
            _generate_cbed_pattern_signal(cbed_pattern_generator)
        cbed_pattern_dims_in_pixels = \
            cbed_pattern_signal.axes_manager.signal_shape
        expected_cbed_pattern_dims_in_pixels = \
            self._expected_cbed_pattern_dims_in_pixels

        _check_cbed_pattern_signal(cbed_pattern_signal,
                                   max_num_disks_in_any_cbed_pattern)

        if cbed_pattern_dims_in_pixels != expected_cbed_pattern_dims_in_pixels:
            err_msg = _unnormalized_ml_data_instance_generator_err_msg_1
            raise ValueError(err_msg)

        self._expected_cbed_pattern_dims_in_pixels = \
            cbed_pattern_signal.axes_manager.signal_shape

        method_alias = \
            super()._generate_ml_data_dict_containing_only_one_ml_data_instance
        ml_data_dict = \
            method_alias()

        func_alias = _extract_ml_data_dict_from_cbed_pattern_signal
        kwargs = {"cbed_pattern_signal": \
                  cbed_pattern_signal,
                  "max_num_disks_in_any_cbed_pattern": \
                  max_num_disks_in_any_cbed_pattern}
        ml_data_dict = {**ml_data_dict, **func_alias(**kwargs)}

        return ml_data_dict



def _generate_ml_data_dict_elem_decoders():
    keys_of_ml_data_dict_elems_having_decoders = \
        _generate_keys_of_ml_data_dict_elems_having_decoders()

    global_symbol_table = \
        globals()
    
    ml_data_dict_elem_decoders = \
        {key+"_decoder": global_symbol_table[key+"_decoder"]
         for key
         in keys_of_ml_data_dict_elems_having_decoders}

    return ml_data_dict_elem_decoders



def _generate_ml_data_dict_key_to_shape_template_map():
    ml_data_dict_key_to_shape_template_map = dict()

    variable_axis_size_dict_keys = _generate_variable_axis_size_dict_keys()
    all_valid_ml_data_dict_keys = _generate_all_valid_ml_data_dict_keys()

    for key in all_valid_ml_data_dict_keys:
        if key in ("cbed_pattern_images", "disk_overlap_maps"):
            shape_template = (variable_axis_size_dict_keys[0],
                              variable_axis_size_dict_keys[1],
                              variable_axis_size_dict_keys[1])
        elif key in ("disk_objectness_sets", "disk_clipping_registries"):
            shape_template = (variable_axis_size_dict_keys[0],
                              variable_axis_size_dict_keys[2])
        elif key == "undistorted_disk_center_sets":
            shape_template = (variable_axis_size_dict_keys[0],
                              variable_axis_size_dict_keys[2],
                              2)
        elif ("centers" in key) or ("vectors" in key):
            shape_template = (variable_axis_size_dict_keys[0], 2)
        else:
            shape_template = (variable_axis_size_dict_keys[0],)

        ml_data_dict_key_to_shape_template_map[key] = shape_template

    return ml_data_dict_key_to_shape_template_map



def _generate_variable_axis_size_dict_keys():
    num_keys = 3
    
    alphabet = tuple(string.ascii_uppercase)
    subset_of_alphabet = alphabet[:num_keys]

    variable_axis_size_dict_keys = tuple("axis size "+letter
                                         for letter
                                         in subset_of_alphabet)

    return variable_axis_size_dict_keys



def _generate_ml_data_dict_elem_decoding_order():
    ml_data_dict_elem_decoding_order = \
        _generate_keys_of_ml_data_dict_elems_having_decoders()

    return ml_data_dict_elem_decoding_order



def _generate_overriding_normalization_weights_and_biases():
    overriding_normalization_weights_and_biases = dict()

    return overriding_normalization_weights_and_biases



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataNormalizer
class _MLDataNormalizer(_cls_alias):
    def __init__(self, max_num_ml_data_instances_per_file_update):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataNormalizer
        kwargs = {"keys_of_unnormalizable_ml_data_dict_elems": \
                  _generate_keys_of_unnormalizable_ml_data_dict_elems(),
                  "keys_of_normalizable_ml_data_dict_elems": \
                  _generate_keys_of_normalizable_ml_data_dict_elems(),
                  "ml_data_dict_elem_decoders": \
                  _generate_ml_data_dict_elem_decoders(),
                  "overriding_normalization_weights_and_biases": \
                  _generate_overriding_normalization_weights_and_biases(),
                  "max_num_ml_data_instances_per_file_update": \
                  max_num_ml_data_instances_per_file_update}
        cls_alias.__init__(self, **kwargs)

        return None



_module_alias = \
    emicroml.modelling._common
_default_max_num_ml_data_instances_per_file_update = \
    _module_alias._default_max_num_ml_data_instances_per_file_update



def _generate_default_ml_data_normalizer():
    kwargs = {"max_num_ml_data_instances_per_file_update": \
              _default_max_num_ml_data_instances_per_file_update}
    ml_data_normalizer = _MLDataNormalizer(**kwargs)

    return ml_data_normalizer



def _generate_ml_data_dict_key_to_dtype_map():
    ml_data_dict_key_to_dtype_map = dict()

    all_valid_ml_data_dict_keys = _generate_all_valid_ml_data_dict_keys()

    for key in all_valid_ml_data_dict_keys:
        if "clipping" in key:
            dtype = np.bool_
        elif "overlap_map" in key:
            dtype = np.uint8
        else:
            dtype = np.float32
            
        ml_data_dict_key_to_dtype_map[key] = dtype

    return ml_data_dict_key_to_dtype_map



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataTypeValidator
class _MLDataTypeValidator(_cls_alias):
    def __init__(self):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataTypeValidator
        kwargs = {"ml_data_dict_key_to_dtype_map": \
                  _generate_ml_data_dict_key_to_dtype_map()}
        cls_alias.__init__(self, **kwargs)

        return None



def _generate_ml_data_dict_key_to_unnormalized_value_limits_map():
    ml_data_dict_key_to_unnormalized_value_limits_map = dict()

    all_valid_ml_data_dict_keys = _generate_all_valid_ml_data_dict_keys()

    for key in all_valid_ml_data_dict_keys:
        if ((key == "cbed_pattern_images")
            or (key == "disk_clipping_registries")
            or (key == "common_undistorted_disk_radii")
            or (key == "disk_objectness_sets")):
            unnormalized_value_limits = (0, 1)
        elif key == "disk_overlap_maps":
            unnormalized_value_limits = (0, np.inf)
        else:
            unnormalized_value_limits = (-np.inf, np.inf)
                
        ml_data_dict_key_to_unnormalized_value_limits_map[key] = \
            unnormalized_value_limits

    return ml_data_dict_key_to_unnormalized_value_limits_map



def _generate_ml_data_dict_key_to_custom_value_checker_map():
    ml_data_dict_key_to_custom_value_checker_map = \
        {"cbed_pattern_images": _custom_value_checker_for_cbed_pattern_images}

    return ml_data_dict_key_to_custom_value_checker_map



def _custom_value_checker_for_cbed_pattern_images(
        data_chunk_is_expected_to_be_normalized_if_normalizable,
        key_used_to_get_data_chunk,
        data_chunk,
        name_of_obj_alias_from_which_data_chunk_was_obtained,
        obj_alias_from_which_data_chunk_was_obtained):
    lower_value_limit = 0
    upper_value_limit = 1
    tol = _tol_for_comparing_floats
    current_func_name = "_custom_value_checker_for_cbed_pattern_images"

    for cbed_pattern_image in data_chunk:
        if ((abs(cbed_pattern_image.min().item()-lower_value_limit) > tol)
            or (abs(cbed_pattern_image.max().item()-upper_value_limit) > tol)):
            obj_alias = obj_alias_from_which_data_chunk_was_obtained

            unformatted_err_msg = \
                (globals()[current_func_name+"_err_msg_1"]
                 if isinstance(obj_alias, h5py.Dataset)
                 else globals()[current_func_name+"_err_msg_2"])

            format_arg_1 = \
                (key_used_to_get_data_chunk
                 if isinstance(obj_alias, h5py.Dataset)
                 else name_of_obj_alias_from_which_data_chunk_was_obtained)
            format_arg_2 = \
                (obj_alias.file.filename
                 if isinstance(obj_alias, h5py.Dataset)
                 else key_used_to_get_data_chunk)

            args = (format_arg_1, format_arg_2)
            
            err_msg = unformatted_err_msg.format(*args)
            raise ValueError(err_msg)

    return None



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataValueValidator
class _MLDataValueValidator(_cls_alias):
    def __init__(self):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataValueValidator
        kwargs = {"ml_data_dict_key_to_unnormalized_value_limits_map": \
                  _generate_ml_data_dict_key_to_unnormalized_value_limits_map(),
                  "ml_data_dict_key_to_custom_value_checker_map": \
                  _generate_ml_data_dict_key_to_custom_value_checker_map(),
                  "ml_data_normalizer": \
                  _generate_default_ml_data_normalizer()}
        cls_alias.__init__(self, **kwargs)

        return None



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataNormalizationWeightsAndBiasesLoader
class _MLDataNormalizationWeightsAndBiasesLoader(_cls_alias):
    def __init__(self, max_num_ml_data_instances_per_file_update):
        ml_data_normalizer = \
            _MLDataNormalizer(max_num_ml_data_instances_per_file_update)
        ml_data_value_validator = \
            _MLDataValueValidator()

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataNormalizationWeightsAndBiasesLoader
        kwargs = {"ml_data_normalizer": ml_data_normalizer,
                  "ml_data_value_validator": ml_data_value_validator}
        cls_alias.__init__(self, **kwargs)
        
        return None



def _generate_default_ml_data_normalization_weights_and_biases_loader():
    kwargs = \
        {"max_num_ml_data_instances_per_file_update": 1}
    ml_data_normalization_weights_and_biases_loader = \
        _MLDataNormalizationWeightsAndBiasesLoader(**kwargs)

    return ml_data_normalization_weights_and_biases_loader



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataRenormalizer
class _MLDataRenormalizer(_cls_alias):
    def __init__(self,
                 input_ml_dataset_filenames,
                 max_num_ml_data_instances_per_file_update):
        kwargs = \
            {"max_num_ml_data_instances_per_file_update": \
             max_num_ml_data_instances_per_file_update}
        ml_data_normalization_weights_and_biases_loader = \
            _MLDataNormalizationWeightsAndBiasesLoader(**kwargs)

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataRenormalizer
        kwargs = {"input_ml_dataset_filenames": \
                  input_ml_dataset_filenames,
                  "max_num_ml_data_instances_per_file_update": \
                  max_num_ml_data_instances_per_file_update,
                  "ml_data_normalization_weights_and_biases_loader": \
                  ml_data_normalization_weights_and_biases_loader}
        cls_alias.__init__(self, **kwargs)

        return None



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataShapeAnalyzer
class _MLDataShapeAnalyzer(_cls_alias):
    def __init__(self):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataShapeAnalyzer
        kwargs = {"variable_axis_size_dict_keys": \
                  _generate_variable_axis_size_dict_keys(),
                  "ml_data_dict_key_to_shape_template_map": \
                  _generate_ml_data_dict_key_to_shape_template_map(),
                  "ml_data_dict_elem_decoders": \
                  _generate_ml_data_dict_elem_decoders()}
        cls_alias.__init__(self, **kwargs)

        return None



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataSplitter
class _MLDataSplitter(_cls_alias):
    def __init__(self,
                 input_ml_dataset_filename,
                 enable_shuffling,
                 rng_seed,
                 max_num_ml_data_instances_per_file_update,
                 split_ratio):
        kwargs = \
            {"max_num_ml_data_instances_per_file_update": \
             max_num_ml_data_instances_per_file_update}
        ml_data_normalization_weights_and_biases_loader = \
            _MLDataNormalizationWeightsAndBiasesLoader(**kwargs)

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataSplitter
        kwargs = {"input_ml_dataset_filename": \
                  input_ml_dataset_filename,
                  "ml_data_normalization_weights_and_biases_loader": \
                  ml_data_normalization_weights_and_biases_loader,
                  "enable_shuffling": \
                  enable_shuffling,
                  "rng_seed": \
                  rng_seed,
                  "max_num_ml_data_instances_per_file_update": \
                  max_num_ml_data_instances_per_file_update,
                  "split_ratio": \
                  split_ratio}
        cls_alias.__init__(self, **kwargs)

        return None
    


def _generate_axes_labels_of_hdf5_datasets_of_ml_dataset_file():
    axes_labels_of_hdf5_datasets_of_ml_dataset_file = dict()
    
    all_valid_ml_data_dict_keys = _generate_all_valid_ml_data_dict_keys()

    for key in all_valid_ml_data_dict_keys:
        if key == "cbed_pattern_images":
            axes_labels_of_hdf5_dataset = ("cbed pattern idx", "row", "col")
        elif key == "disk_overlap_maps":
            axes_labels_of_hdf5_dataset = ("cbed pattern idx", "row", "col")
        elif key in ("disk_objectness_sets", "disk_clipping_registries"):
            axes_labels_of_hdf5_dataset = ("cbed pattern idx", "disk idx")
        elif key == "undistorted_disk_center_sets":
            axes_labels_of_hdf5_dataset = ("cbed pattern idx",
                                           "disk idx",
                                           "vector cmpnt idx [0->x, 1->y]")
        elif ("centers" in key) or ("vectors" in key):
            axes_labels_of_hdf5_dataset = ("cbed pattern idx",
                                           "vector cmpnt idx [0->x, 1->y]")
        else:
            axes_labels_of_hdf5_dataset = ("cbed pattern idx",)
        
        axes_labels_of_hdf5_datasets_of_ml_dataset_file[key] = \
            axes_labels_of_hdf5_dataset

    return axes_labels_of_hdf5_datasets_of_ml_dataset_file



def _check_and_convert_generate_and_save_ml_dataset_params(params):
    params = params.copy()

    module_alias = \
        emicroml.modelling._common
    func_alias = \
        module_alias._check_and_convert_generate_and_save_ml_dataset_params
    params = \
        func_alias(params)

    param_name_subset = ("num_cbed_patterns",
                         "cbed_pattern_generator",
                         "max_num_disks_in_any_cbed_pattern")

    global_symbol_table = globals()
    for param_name in param_name_subset:
        func_name = "_check_and_convert_" + param_name
        func_alias = global_symbol_table[func_name]
        params[param_name] = func_alias(params)

    return params



def _check_and_convert_num_cbed_patterns(params):
    obj_name = "num_cbed_patterns"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}    
    num_cbed_patterns = czekitout.convert.to_positive_int(**kwargs)

    return num_cbed_patterns



def _check_and_convert_cbed_pattern_generator(params):
    obj_name = "cbed_pattern_generator"
    obj = params[obj_name]

    if obj is None:
        kwargs = {"num_pixels_across_each_cbed_pattern": \
                  _default_num_pixels_across_each_cbed_pattern,
                  "max_num_disks_in_any_cbed_pattern": \
                  _default_max_num_disks_in_any_cbed_pattern,
                  "rng_seed": \
                  _default_rng_seed,
                  "sampling_grid_dims_in_pixels": \
                  _default_sampling_grid_dims_in_pixels,
                  "least_squares_alg_params": \
                  _default_least_squares_alg_params,
                  "device_name": \
                  _default_device_name,
                  "skip_validation_and_conversion": \
                  False}
        cbed_pattern_generator = _DefaultCBEDPatternGenerator(**kwargs)
    else:
        cbed_pattern_generator = obj

    return cbed_pattern_generator



_module_alias = emicroml.modelling._common
_default_cbed_pattern_generator = None
_default_num_cbed_patterns = 1500
_default_output_filename = _module_alias._default_output_filename



def _generate_and_save_ml_dataset(cbed_pattern_generator,
                                  max_num_disks_in_any_cbed_pattern,
                                  max_num_ml_data_instances_per_file_update,
                                  num_cbed_patterns,
                                  output_filename,
                                  start_time):
    kwargs = \
        {"cbed_pattern_generator":
         cbed_pattern_generator,
         "max_num_disks_in_any_cbed_pattern": \
         max_num_disks_in_any_cbed_pattern}
    unnormalized_ml_data_instance_generator = \
        _UnnormalizedMLDataInstanceGenerator(**kwargs)

    kwargs = {"max_num_ml_data_instances_per_file_update": \
              max_num_ml_data_instances_per_file_update}
    ml_data_normalizer = _MLDataNormalizer(**kwargs)

    num_ml_data_instances = num_cbed_patterns

    ml_data_type_validator = \
        _MLDataTypeValidator()
    ml_data_dict_key_to_dtype_map = \
        ml_data_type_validator._ml_data_dict_key_to_dtype_map

    func_alias = _generate_axes_labels_of_hdf5_datasets_of_ml_dataset_file
    axes_labels_of_hdf5_datasets_of_ml_dataset_file = func_alias()

    module_alias = emicroml.modelling._common
    func_alias = module_alias._generate_and_save_ml_dataset
    func_alias(output_filename,
               unnormalized_ml_data_instance_generator,
               ml_data_normalizer,
               num_ml_data_instances,
               ml_data_dict_key_to_dtype_map,
               axes_labels_of_hdf5_datasets_of_ml_dataset_file,
               start_time)

    return None



def _check_and_convert_combine_ml_dataset_files_params(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_combine_ml_dataset_files_params
    params = func_alias(params)

    return params



_module_alias = \
    emicroml.modelling._common
_default_output_ml_dataset_filename = \
    _module_alias._default_output_ml_dataset_filename
_default_rm_input_ml_dataset_files = \
    _module_alias._default_rm_input_ml_dataset_files



def _combine_ml_dataset_files(max_num_ml_data_instances_per_file_update,
                              input_ml_dataset_filenames,
                              output_ml_dataset_filename,
                              rm_input_ml_dataset_files,
                              start_time):
    ml_data_type_validator = _MLDataTypeValidator()

    ml_data_shape_analyzer = _MLDataShapeAnalyzer()

    func_alias = _generate_axes_labels_of_hdf5_datasets_of_ml_dataset_file
    axes_labels_of_hdf5_datasets_of_ml_dataset_file = func_alias()

    kwargs = {"input_ml_dataset_filenames": \
              input_ml_dataset_filenames,
              "max_num_ml_data_instances_per_file_update": \
              max_num_ml_data_instances_per_file_update}
    ml_data_renormalizer = _MLDataRenormalizer(**kwargs)

    module_alias = emicroml.modelling._common
    func_alias = module_alias._combine_ml_dataset_files
    func_alias(input_ml_dataset_filenames,
               output_ml_dataset_filename,
               ml_data_type_validator,
               ml_data_shape_analyzer,
               axes_labels_of_hdf5_datasets_of_ml_dataset_file,
               ml_data_renormalizer,
               rm_input_ml_dataset_files,
               start_time)

    return None



def _check_and_convert_split_ml_dataset_file_params(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_split_ml_dataset_file_params
    params = func_alias(params)

    return params



_module_alias = \
    emicroml.modelling._common
_default_output_ml_dataset_filename_1 = \
    _module_alias._default_output_ml_dataset_filename_1
_default_output_ml_dataset_filename_2 = \
    _module_alias._default_output_ml_dataset_filename_2
_default_output_ml_dataset_filename_3 = \
    _module_alias._default_output_ml_dataset_filename_3
_default_split_ratio = \
    _module_alias._default_split_ratio
_default_enable_shuffling = \
    _module_alias._default_enable_shuffling
_default_rm_input_ml_dataset_file = \
    _module_alias._default_rm_input_ml_dataset_file



def _split_ml_dataset_file(output_ml_dataset_filename_1,
                           output_ml_dataset_filename_2,
                           output_ml_dataset_filename_3,
                           max_num_ml_data_instances_per_file_update,
                           input_ml_dataset_filename,
                           split_ratio,
                           enable_shuffling,
                           rng_seed,
                           rm_input_ml_dataset_file,
                           start_time):
    output_ml_dataset_filenames = (output_ml_dataset_filename_1,
                                   output_ml_dataset_filename_2,
                                   output_ml_dataset_filename_3)

    ml_data_type_validator = _MLDataTypeValidator()

    ml_data_shape_analyzer = _MLDataShapeAnalyzer()

    func_alias = _generate_axes_labels_of_hdf5_datasets_of_ml_dataset_file
    axes_labels_of_hdf5_datasets_of_ml_dataset_file = func_alias()

    kwargs = {"input_ml_dataset_filename": \
              input_ml_dataset_filename,
              "enable_shuffling": \
              enable_shuffling,
              "rng_seed": \
              rng_seed,
              "max_num_ml_data_instances_per_file_update": \
              max_num_ml_data_instances_per_file_update,
              "split_ratio": split_ratio}
    ml_data_splitter = _MLDataSplitter(**kwargs)

    module_alias = emicroml.modelling._common
    func_alias = module_alias._split_ml_dataset_file
    func_alias(ml_data_splitter,
               output_ml_dataset_filenames,
               ml_data_type_validator,
               ml_data_shape_analyzer,
               axes_labels_of_hdf5_datasets_of_ml_dataset_file,
               rm_input_ml_dataset_file,
               start_time)

    return None



def _get_num_pixels_across_each_cbed_pattern(path_to_ml_dataset,
                                             ml_data_shape_analyzer):
    obj_alias = \
        ml_data_shape_analyzer
    method_alias = \
        obj_alias._hdf5_dataset_path_to_shape_map_of_ml_dataset_file
    hdf5_dataset_path_to_shape_map = \
        method_alias(path_to_ml_dataset)

    hdf5_dataset_shape = \
        hdf5_dataset_path_to_shape_map["cbed_pattern_images"]
    num_pixels_across_each_cbed_pattern = \
        hdf5_dataset_shape[-1]

    return num_pixels_across_each_cbed_pattern



def _get_max_num_disks_in_any_cbed_pattern(path_to_ml_dataset,
                                           ml_data_shape_analyzer):
    obj_alias = \
        ml_data_shape_analyzer
    method_alias = \
        obj_alias._hdf5_dataset_path_to_shape_map_of_ml_dataset_file
    hdf5_dataset_path_to_shape_map = \
        method_alias(path_to_ml_dataset)

    hdf5_dataset_shape = \
        hdf5_dataset_path_to_shape_map["disk_objectness_sets"]
    max_num_disks_in_any_cbed_pattern = \
        hdf5_dataset_shape[-1]

    return max_num_disks_in_any_cbed_pattern



def _check_and_convert_normalize_normalizable_elems_in_ml_data_dict_params(
        params):
    original_params = params
    params = params.copy()

    params["ml_data_shape_analyzer"] = \
        _MLDataShapeAnalyzer()
    params["ml_data_type_validator"] = \
        _MLDataTypeValidator()
    params["ml_data_normalization_weights_and_biases_loader"] = \
        _generate_default_ml_data_normalization_weights_and_biases_loader()
    params["default_normalization_weights"] = \
        _generate_default_normalization_weights()
    params["default_normalization_biases"] = \
        _generate_default_normalization_biases()

    current_func_name = ("_check_and_convert"
                         "_normalize_normalizable_elems_in_ml_data_dict_params")

    module_alias = emicroml.modelling._common
    func_alias = getattr(module_alias, current_func_name)
    params = func_alias(params)

    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]

    return params



_module_alias = \
    emicroml.modelling._common
_default_check_ml_data_dict_first = \
    _module_alias._default_check_ml_data_dict_first



def _normalize_normalizable_elems_in_ml_data_dict(ml_data_dict,
                                                  normalization_weights,
                                                  normalization_biases):
    kwargs = locals()
    module_alias = emicroml.modelling._common
    func_alias = module_alias._normalize_normalizable_elems_in_ml_data_dict
    func_alias(**kwargs)

    return None



def _check_and_convert_unnormalize_normalizable_elems_in_ml_data_dict_params(
        params):
    original_params = params
    params = params.copy()

    params["ml_data_shape_analyzer"] = \
        _MLDataShapeAnalyzer()
    params["ml_data_type_validator"] = \
        _MLDataTypeValidator()
    params["ml_data_normalization_weights_and_biases_loader"] = \
        _generate_default_ml_data_normalization_weights_and_biases_loader()
    params["default_normalization_weights"] = \
        _generate_default_normalization_weights()
    params["default_normalization_biases"] = \
        _generate_default_normalization_biases()

    current_func_name = ("_check_and_convert_unnormalize_normalizable_elems"
                         "_in_ml_data_dict_params")
    
    module_alias = emicroml.modelling._common
    func_alias = getattr(module_alias, current_func_name)
    params = func_alias(params)

    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]

    return params



def _unnormalize_normalizable_elems_in_ml_data_dict(ml_data_dict,
                                                    normalization_weights,
                                                    normalization_biases):
    kwargs = locals()
    module_alias = emicroml.modelling._common
    func_alias = module_alias._unnormalize_normalizable_elems_in_ml_data_dict
    func_alias(**kwargs)

    return None



def _check_and_convert_ml_data_dict_to_distortion_models_params(params):
    original_params = params
    params = params.copy()
    
    params["data_chunk_dims_are_to_be_expanded_temporarily"] = \
        False
    params["expected_ml_data_dict_keys"] = \
        _generate_keys_related_to_distortion_params()
    params["ml_data_dict"] = \
        _check_and_convert_ml_data_dict(params)
    params["sampling_grid_dims_in_pixels"] = \
        _check_and_convert_sampling_grid_dims_in_pixels(params)
    params["device_name"] = \
        _check_and_convert_device_name(params)
    params["least_squares_alg_params"] = \
        _check_and_convert_least_squares_alg_params(params)

    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]
    
    return params



def _check_and_convert_ml_data_dict(params):
    params = params.copy()

    params["name_of_obj_alias_of_ml_data_dict"] = "ml_data_dict"
    params["ml_data_normalizer"] = _generate_default_ml_data_normalizer()
    params["target_numerical_data_container_cls"] = None
    params["target_device"] = None
    params["variable_axis_size_dict"] = None
    params["ml_data_shape_analyzer"] = _MLDataShapeAnalyzer()
    params["ml_data_type_validator"] = _MLDataTypeValidator()
    params["normalizable_elems_are_normalized"] = False
    params["ml_data_value_validator"] = _MLDataValueValidator()

    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_ml_data_dict
    ml_data_dict = func_alias(params)

    return ml_data_dict



def _ml_data_dict_to_distortion_models(ml_data_dict,
                                       sampling_grid_dims_in_pixels,
                                       device_name,
                                       least_squares_alg_params):
    try:
        distortion_centers = \
            ml_data_dict["distortion_centers"]
        ml_data_dict_keys_related_to_distortion_params = \
            _generate_keys_related_to_distortion_params()

        distortion_models = tuple()
        for cbed_pattern_idx, _ in enumerate(distortion_centers):
            cls_alias = distoptica.StandardCoordTransformParams
            kwargs = {"skip_validation_and_conversion": True}
            for key in ml_data_dict_keys_related_to_distortion_params:
                param_name = "center" if ("center" in key) else key[:-1]
                param_val = ml_data_dict[key][cbed_pattern_idx]
                param_val = (tuple(param_val.tolist())
                             if (("center" in key) or ("vector" in key))
                             else param_val.item())
                kwargs[param_name] = param_val
            standard_coord_transform_params = cls_alias(**kwargs)

            kwargs = {"standard_coord_transform_params": \
                      standard_coord_transform_params,
                      "sampling_grid_dims_in_pixels": \
                      sampling_grid_dims_in_pixels,
                      "device_name": \
                      device_name,
                      "least_squares_alg_params": \
                      least_squares_alg_params,
                      "skip_validation_and_conversion": \
                      True}
            func_alias = distoptica.generate_standard_distortion_model
            distortion_model = func_alias(**kwargs)
            distortion_models += (distortion_model,)
    except:
        cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
        num_cbed_patterns = cbed_pattern_images.shape[0]
        distortion_models = (None,) * num_cbed_patterns

    return distortion_models



def _check_and_convert_ml_data_dict_to_signals_params(params):
    original_params = params
    params = params.copy()

    kwargs = {"obj": params["ml_data_dict"], "obj_name": "ml_data_dict"}
    ml_data_dict = czekitout.convert.to_dict(**kwargs)

    device_name = params["device_name"]

    params = {"cbed_pattern_images": \
              ml_data_dict.get("cbed_pattern_images", None),
              "name_of_obj_alias_of_cbed_pattern_images": \
              "ml_data_dict['cbed_pattern_images']",
              "target_device": \
              _get_device(device_name),
              **params}
    cbed_pattern_images = _check_and_convert_cbed_pattern_images(params)
    params["ml_data_dict"]["cbed_pattern_images"] = cbed_pattern_images

    params["data_chunk_dims_are_to_be_expanded_temporarily"] = \
        False
    params["expected_ml_data_dict_keys"] = \
        ("cbed_pattern_images",)
    params["ml_data_dict"] = \
        _check_and_convert_ml_data_dict(params)
    params["sampling_grid_dims_in_pixels"] = \
        _check_and_convert_sampling_grid_dims_in_pixels(params)
    params["device_name"] = \
        _check_and_convert_device_name(params)
    params["least_squares_alg_params"] = \
        _check_and_convert_least_squares_alg_params(params)

    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]
    
    return params



def _check_and_convert_cbed_pattern_images(params):
    obj_name = "cbed_pattern_images"
    obj = params[obj_name]

    name_of_obj_alias_of_cbed_pattern_images = \
        params.get("name_of_obj_alias_of_cbed_pattern_images", obj_name)
    target_device = \
        params.get("target_device", None)

    kwargs = {"numerical_data_container": \
              obj,
              "name_of_obj_alias_of_numerical_data_container": \
              name_of_obj_alias_of_cbed_pattern_images,
              "target_numerical_data_container_cls": \
              torch.Tensor,
              "target_device": \
              target_device}
    obj = _convert_numerical_data_container(**kwargs)

    current_func_name = "_check_and_convert_cbed_pattern_images"

    if len(obj.shape) != 3:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        args = (name_of_obj_alias_of_cbed_pattern_images,)
        err_msg = unformatted_err_msg.format(*args)
        raise ValueError(err_msg)

    kwargs = {"image_stack": obj}
    cbed_pattern_images = _min_max_normalize_image_stack(**kwargs)

    return cbed_pattern_images



def _convert_numerical_data_container(
        numerical_data_container,
        name_of_obj_alias_of_numerical_data_container,
        target_numerical_data_container_cls,
        target_device):
    kwargs = locals()
    
    module_alias = emicroml.modelling._common
    func_alias = module_alias._convert_numerical_data_container
    numerical_data_container = func_alias(**kwargs)

    return numerical_data_container



def _ml_data_dict_to_signals(ml_data_dict,
                             sampling_grid_dims_in_pixels,
                             device_name,
                             least_squares_alg_params):
    kwargs = \
        locals()
    distortion_models = \
        _ml_data_dict_to_distortion_models(**kwargs)

    kwargs = \
        {"ml_data_dict": ml_data_dict, "device_name": device_name}
    cbed_pattern_images = \
        _get_cbed_pattern_images_from_ml_data_dict(**kwargs)

    kwargs = \
        {"ml_data_dict": ml_data_dict}
    disk_overlap_maps = \
        _get_disk_overlap_maps_from_ml_data_dict(**kwargs)
    undistorted_disk_sets = \
        _generate_undistorted_disk_sets_from_ml_data_dict(**kwargs)
    mask_frames = \
        _calc_mask_frames_from_cbed_pattern_images(**kwargs)

    signals = tuple()
    global_symbol_table = globals()
    for cbed_pattern_idx, _ in enumerate(cbed_pattern_images):
        func_name = ("_construct_cbed_pattern_signal"
                     "_using_objs_extracted_from_ml_data_dict")
        func_alias = global_symbol_table[func_name]
        kwargs = {"undistorted_disk_set": \
                  undistorted_disk_sets[cbed_pattern_idx],
                  "cbed_pattern_image": \
                  cbed_pattern_images[cbed_pattern_idx],
                  "distortion_model": \
                  distortion_models[cbed_pattern_idx],
                  "mask_frame": \
                  mask_frames[cbed_pattern_idx],
                  "disk_overlap_map": \
                  disk_overlap_maps[cbed_pattern_idx]}
        cbed_pattern_signal = func_alias(**kwargs)
        signals += (cbed_pattern_signal,)

    return signals



def _get_cbed_pattern_images_from_ml_data_dict(ml_data_dict, device_name):
    key = "cbed_pattern_images"

    module_alias = \
        emicroml.modelling._common
    convert_numerical_data_container = \
        module_alias._convert_numerical_data_container

    kwargs = {"numerical_data_container": \
              ml_data_dict[key],
              "name_of_obj_alias_of_numerical_data_container": \
              "ml_data_dict['{}']".format(key),
              "target_numerical_data_container_cls": \
              torch.Tensor,
              "target_device": \
              _get_device(device_name)}
    cbed_pattern_images = convert_numerical_data_container(**kwargs)

    return cbed_pattern_images



def _get_disk_overlap_maps_from_ml_data_dict(ml_data_dict):
    key = "disk_overlap_maps"

    module_alias = \
        emicroml.modelling._common
    convert_numerical_data_container = \
        module_alias._convert_numerical_data_container

    try:
        kwargs = {"numerical_data_container": \
                  ml_data_dict[key],
                  "name_of_obj_alias_of_numerical_data_container": \
                  "ml_data_dict['{}']".format(key),
                  "target_numerical_data_container_cls": \
                  np.ndarray,
                  "target_device": \
                  None}
        disk_overlap_maps = convert_numerical_data_container(**kwargs)
    except:
        cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
        num_cbed_patterns = cbed_pattern_images.shape[0]
        disk_overlap_maps = (None,) * num_cbed_patterns

    return disk_overlap_maps



def _generate_undistorted_disk_sets_from_ml_data_dict(ml_data_dict):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    num_cbed_patterns = cbed_pattern_images.shape[0]

    try:
        undistorted_disk_sets = tuple()
        for cbed_pattern_idx in range(num_cbed_patterns):
            func_alias = _generate_undistorted_disk_set_from_ml_data_dict
            undistorted_disk_set = func_alias(ml_data_dict, cbed_pattern_idx)
            undistorted_disk_sets += (undistorted_disk_set,)
    except:
        undistorted_disk_sets = (tuple(),) * num_cbed_patterns

    return undistorted_disk_sets



def _generate_undistorted_disk_set_from_ml_data_dict(ml_data_dict,
                                                     cbed_pattern_idx):
    for key in ml_data_dict:
        module_alias = \
            emicroml.modelling._common
        convert_numerical_data_container = \
            module_alias._convert_numerical_data_container
        kwargs = \
            {"numerical_data_container": \
             ml_data_dict[key],
             "name_of_obj_alias_of_numerical_data_container": \
             "ml_data_dict['{}']".format(key),
             "target_numerical_data_container_cls": \
             np.ndarray,
             "target_device": \
             None}
        numerical_data_container = \
            convert_numerical_data_container(**kwargs)
        
        if key == "common_undistorted_disk_radii":
            u_R_support = \
                numerical_data_container[cbed_pattern_idx].item()
        elif key == "undistorted_disk_center_sets":
            undistorted_disk_center_set = \
                numerical_data_container[cbed_pattern_idx]
        elif key == "disk_objectness_sets":
            disk_objectnesss = \
                numerical_data_container[cbed_pattern_idx]

    undistorted_disk_set = tuple()
    for disk_idx, disk_objectness in enumerate(disk_objectnesss):
        if disk_objectness == 1:
            kwargs = {"center": undistorted_disk_center_set[disk_idx],
                      "radius": u_R_support,
                      "intra_shape_val": 1,
                      "skip_validation_and_conversion": True}
            undistorted_disk_support = fakecbed.shapes.Circle(**kwargs)
            
            kwargs = {"support": undistorted_disk_support,
                      "intra_support_shapes": tuple(),
                      "skip_validation_and_conversion": True}
            undistorted_disk = fakecbed.shapes.NonuniformBoundedShape(**kwargs)
            undistorted_disk_set += (undistorted_disk,)

    return undistorted_disk_set



def _calc_mask_frames_from_cbed_pattern_images(ml_data_dict):
    key = "cbed_pattern_images"
    cbed_pattern_images = ml_data_dict[key]

    mask_frames = tuple()
    for cbed_pattern_image in cbed_pattern_images:
        kwargs = {"cbed_pattern_image": cbed_pattern_image}
        mask_frame = _calc_mask_frame_from_cbed_pattern_image(**kwargs)
        mask_frames += (mask_frame,)

    return mask_frames



def _calc_mask_frame_from_cbed_pattern_image(cbed_pattern_image):
    rows_are_nonzero = cbed_pattern_image.any(1)+0
    cols_are_nonzero = cbed_pattern_image.any(0)+0

    L = cols_are_nonzero.argmax().item()
    R = torch.flip(cols_are_nonzero, dims=(0,)).argmax().item()

    T = rows_are_nonzero.argmax().item()
    B = torch.flip(rows_are_nonzero, dims=(0,)).argmax().item()

    mask_frame = (L, R, B, T)

    return mask_frame



def _construct_cbed_pattern_signal_using_objs_extracted_from_ml_data_dict(
        undistorted_disk_set,
        cbed_pattern_image,
        distortion_model,
        mask_frame,
        disk_overlap_map):
    kwargs = {"undistorted_tds_model": None,
              "undistorted_disks": undistorted_disk_set,
              "undistorted_misc_shapes": tuple(),
              "undistorted_outer_illumination_shape": None,
              "gaussian_filter_std_dev": 0,
              "num_pixels_across_pattern": cbed_pattern_image.shape[-1],
              "distortion_model": distortion_model,
              "apply_shot_noise": False,
              "detector_partition_width_in_pixels": 0,
              "mask_frame": mask_frame}
    cbed_pattern = fakecbed.discretized.CBEDPattern(**kwargs)

    kwargs = {"overriding_image": cbed_pattern_image,
              "skip_validation_and_conversion": True}
    cbed_pattern.override_image_then_reapply_mask(**kwargs)

    kwargs = {"cbed_pattern_image": cbed_pattern_image,
              "disk_overlap_map": disk_overlap_map}
    inferred_illumination_support = _infer_illumination_support(**kwargs)

    cbed_pattern_signal = cbed_pattern.get_signal(deep_copy=False)
    if disk_overlap_map is not None:
        cbed_pattern_signal.data[2] = disk_overlap_map
    cbed_pattern_signal.data[1] *= inferred_illumination_support

    return cbed_pattern_signal



def _infer_illumination_support(cbed_pattern_image, disk_overlap_map):
    inferred_illumination_support = (cbed_pattern_image != 0).numpy(force=True)
    if disk_overlap_map is not None:
        inferred_illumination_support += (disk_overlap_map > 0)

    return inferred_illumination_support



_module_alias = \
    emicroml.modelling._common
_default_entire_ml_dataset_is_to_be_cached = \
    _module_alias._default_entire_ml_dataset_is_to_be_cached
_default_ml_data_values_are_to_be_checked = \
    _module_alias._default_ml_data_values_are_to_be_checked
_default_max_num_ml_data_instances_per_chunk = \
    _default_max_num_ml_data_instances_per_file_update
_default_single_dim_slice = \
    _module_alias._default_single_dim_slice



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDataset
class _MLDataset(_cls_alias):
    def __init__(self,
                 path_to_ml_dataset,
                 entire_ml_dataset_is_to_be_cached,
                 ml_data_values_are_to_be_checked,
                 max_num_ml_data_instances_per_chunk,
                 skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDataset
        cls_alias.__init__(self, ctor_params)
        
        return None



    def execute_post_core_attrs_update_actions(self):
        super().execute_post_core_attrs_update_actions()

        self_core_attrs = self.get_core_attrs(deep_copy=False)

        func_alias = _get_num_pixels_across_each_cbed_pattern
        kwargs = {"path_to_ml_dataset": \
                  self_core_attrs["path_to_ml_dataset"],
                  "ml_data_shape_analyzer": \
                  _MLDataShapeAnalyzer()}
        self._num_pixels_across_each_cbed_pattern = func_alias(**kwargs)

        func_alias = _get_max_num_disks_in_any_cbed_pattern
        self._max_num_disks_in_any_cbed_pattern = func_alias(**kwargs)

        return None



    def _generate_ml_data_normalization_weights_and_biases_loader(self):
        super()._generate_ml_data_normalization_weights_and_biases_loader()

        self_core_attrs = self.get_core_attrs(deep_copy=False)
        
        kwargs = \
            {"max_num_ml_data_instances_per_file_update": \
             self_core_attrs["max_num_ml_data_instances_per_chunk"]}
        ml_data_normalization_weights_and_biases_loader = \
            _MLDataNormalizationWeightsAndBiasesLoader(**kwargs)

        return ml_data_normalization_weights_and_biases_loader



    def _generate_torch_ml_dataset(self):
        super()._generate_torch_ml_dataset()

        self_core_attrs = \
            self.get_core_attrs(deep_copy=False)
        ml_data_normalization_weights_and_biases_loader = \
            self._generate_ml_data_normalization_weights_and_biases_loader()

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._TorchMLDataset
        kwargs = {"path_to_ml_dataset": \
                  self_core_attrs["path_to_ml_dataset"],
                  "ml_data_normalization_weights_and_biases_loader": \
                  ml_data_normalization_weights_and_biases_loader,
                  "ml_data_type_validator": \
                  _MLDataTypeValidator(),
                  "ml_data_shape_analyzer": \
                  _MLDataShapeAnalyzer(),
                  "entire_ml_dataset_is_to_be_cached": \
                  self_core_attrs["entire_ml_dataset_is_to_be_cached"],
                  "ml_data_values_are_to_be_checked": \
                  self_core_attrs["ml_data_values_are_to_be_checked"],
                  "ml_data_dict_elem_decoders": \
                  _generate_ml_data_dict_elem_decoders(),
                  "ml_data_dict_elem_decoding_order": \
                  _generate_ml_data_dict_elem_decoding_order()}
        torch_ml_dataset = cls_alias(**kwargs)

        return torch_ml_dataset



    def get_ml_data_instances_as_signals(
            self,
            single_dim_slice=\
            _default_single_dim_slice,
            device_name=\
            _default_device_name,
            sampling_grid_dims_in_pixels=\
            _default_sampling_grid_dims_in_pixels,
            least_squares_alg_params=\
            _default_least_squares_alg_params):
        r"""Return a subset of the machine learning data instances as a sequence
        of Hyperspy signals.

        See the documentation for the classes
        :class:`fakecbed.discretized.CBEDPattern`,
        :class:`distoptica.DistortionModel`, and
        :class:`hyperspy._signals.signal2d.Signal2D` for discussions on "fake"
        CBED patterns, distortion models, and Hyperspy signals respectively.

        For each machine learning (ML) data instance in the subset, an instance
        ``distortion_model`` of the class :class:`distoptica.DistortionModel` is
        constructed according to the ML data instance's features. The object
        ``distortion_model`` is a distortion model that describes the distortion
        field of the imaged CBED pattern of the ML data instance. After
        constructing ``distortion_model``, an instance
        :class:`fakecbed.discretized.CBEDPattern` is constructed according to
        the ML data instance's features and
        ``distortion_model``. ``fake_cbed_pattern`` is a fake CBED pattern
        representation of the CBED pattern of the ML data instance. Next, a
        Hyperspy signal ``fake_cbed_pattern_signal`` is obtained from
        ``fake_cbed_pattern.signal``. The Hyperspy signal representation of the
        ML data instance is obtained by modifying in place
        ``fake_cbed_pattern_signal.data[1:3]`` according to the ML data
        instance's features. Note that the illumination support of the fake CBED
        pattern representation of the CBED pattern of the ML data instance is
        inferred from the features of the ML data instance, and is stored in
        ``fake_cbed_pattern_signal.data[1]``. Moreover, the illumination suport
        implied by the signal's metadata should be ignored.

        Parameters
        ----------
        single_dim_slice : `int` | `array_like` (`int`, ndim=1)  | `slice`, optional
            ``single_dim_slice`` specifies the subset of ML data instances to
            return as a dictionary. The ML data instances are indexed from ``0``
            to ``total_num_ml_data_instances-1``, where
            ``total_num_ml_data_instances`` is the total number of ML data
            instances in the ML dataset.
            ``tuple(range(total_num_ml_data_instances))[single_dim_slice]``
            yields the indices ``ml_data_instance_subset_indices`` of the ML 
            data instances to return.
        device_name : `str` | `None`, optional
            This parameter specifies the device to be used to perform
            computationally intensive calls to PyTorch functions and to store
            intermediate arrays of the type :class:`torch.Tensor`. If
            ``device_name`` is a string, then it is the name of the device to be
            used, e.g. ``”cuda”`` or ``”cpu”``. If ``device_name`` is set to
            ``None`` and a GPU device is available, then a GPU device is to be
            used. Otherwise, the CPU is used.
        sampling_grid_dims_in_pixels : `array_like` (`int`, shape=(2,)), optional
            The dimensions of the sampling grid, in units of pixels, used for
            all distortion models.
        least_squares_alg_params : :class:`distoptica.LeastSquaresAlgParams` | `None`, optional
            ``least_squares_alg_params`` specifies the parameters of the
            least-squares algorithm to be used to calculate the mappings of
            fractional Cartesian coordinates of distorted images to those of the
            corresponding undistorted images. ``least_squares_alg_params`` is
            used to calculate the interim distortion models mentioned above in
            the summary documentation. If ``least_squares_alg_params`` is set to
            ``None``, then the parameter will be reassigned to the value
            ``distoptica.LeastSquaresAlgParams()``. See the documentation for
            the class :class:`distoptica.LeastSquaresAlgParams` for details on
            the parameters of the least-squares algorithm.

        Returns
        -------
        ml_data_instances_as_signals : `array_like` (:class:`hyperspy._signals.signal2d.Signal2D`, ndim=1)
            The subset of ML data instances, represented as a sequence of
            Hyperspy signals. Let ``num_ml_data_instances_in_subset`` be
            ``len(ml_data_instances_as_signals)``. For every nonnegative integer
            ``n`` less than ``num_ml_data_instances_in_subset``, then
            ``ml_data_instances_as_signals[n]`` yields the Hyperspy signal 
            representation of the ML data instance with the index
            ``ml_data_instance_subset_indices[n]``.

        """
        params = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        sampling_grid_dims_in_pixels = \
            _check_and_convert_sampling_grid_dims_in_pixels(params)
        least_squares_alg_params = \
            _check_and_convert_least_squares_alg_params(params)

        kwargs = {"single_dim_slice": single_dim_slice,
                  "device_name": device_name,
                  "decode": True,
                  "unnormalize_normalizable_elems": True}
        ml_data_instances = self.get_ml_data_instances(**kwargs)

        kwargs = \
            {"ml_data_dict": ml_data_instances,
             "sampling_grid_dims_in_pixels": sampling_grid_dims_in_pixels,
             "device_name": device_name,
             "least_squares_alg_params": least_squares_alg_params}
        ml_data_instances_as_signals = \
            _ml_data_dict_to_signals(**kwargs)

        return ml_data_instances_as_signals



    @property
    def num_pixels_across_each_cbed_pattern(self):
        r"""`int`: The number of pixels across each imaged CBED pattern stored 
        in the machine learning dataset.

        Note that ``num_pixels_across_each_cbed_pattern`` should be considered
        **read-only**.

        """
        result = self._num_pixels_across_each_cbed_pattern
        
        return result



    @property
    def max_num_disks_in_any_cbed_pattern(self):
        r"""`int`: The maximum possible number of CBED disks in any imaged CBED 
        pattern stored in the machine learning dataset.

        Note that ``max_num_disks_in_any_cbed_pattern`` should be considered
        **read-only**.

        """
        result = self._max_num_disks_in_any_cbed_pattern

        return result



def _check_and_convert_ml_training_dataset(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_ml_training_dataset
    ml_training_dataset = func_alias(params)

    return ml_training_dataset



def _pre_serialize_ml_training_dataset(ml_training_dataset):
    obj_to_pre_serialize = ml_training_dataset
    module_alias = emicroml.modelling._common
    func_alias = module_alias._pre_serialize_ml_training_dataset
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



_module_alias = emicroml.modelling._common
_default_ml_training_dataset = _module_alias._default_ml_training_dataset



def _check_and_convert_ml_validation_dataset(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_ml_validation_dataset
    ml_validation_dataset = func_alias(params)

    return ml_validation_dataset



def _pre_serialize_ml_validation_dataset(ml_validation_dataset):
    obj_to_pre_serialize = ml_validation_dataset
    module_alias = emicroml.modelling._common
    func_alias = module_alias._pre_serialize_ml_validation_dataset
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



_module_alias = emicroml.modelling._common
_default_ml_validation_dataset = _module_alias._default_ml_validation_dataset



def _check_and_convert_ml_testing_dataset(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_ml_testing_dataset
    ml_testing_dataset = func_alias(params)

    return ml_testing_dataset



def _pre_serialize_ml_testing_dataset(ml_testing_dataset):
    obj_to_pre_serialize = ml_testing_dataset
    module_alias = emicroml.modelling._common
    func_alias = module_alias._pre_serialize_ml_testing_dataset
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



_module_alias = \
    emicroml.modelling._common
_default_ml_testing_dataset = \
    _module_alias._default_ml_testing_dataset
_default_mini_batch_size = \
    _module_alias._default_mini_batch_size
_default_num_data_loader_workers = \
    _module_alias._default_num_data_loader_workers



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLDatasetManager
class _MLDatasetManager(_cls_alias):
    def __init__(self,
                 ml_training_dataset,
                 ml_validation_dataset,
                 ml_testing_dataset,
                 mini_batch_size,
                 rng_seed,
                 num_data_loader_workers,
                 skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLDatasetManager
        cls_alias.__init__(self, ctor_params)

        return None



def _check_and_convert_ml_dataset_manager(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_ml_dataset_manager
    ml_dataset_manager = func_alias(params)

    return ml_dataset_manager



def _pre_serialize_ml_dataset_manager(ml_dataset_manager):
    obj_to_pre_serialize = ml_dataset_manager
    module_alias = emicroml.modelling._common
    func_alias = module_alias._pre_serialize_ml_dataset_manager
    serializable_rep = func_alias(obj_to_pre_serialize)
    
    return serializable_rep



def _min_max_normalize_image_stack(image_stack):
    maxima_over_last_two_dims = image_stack.amax(dim=(-2, -1))
    minima_over_last_two_dims = image_stack.amin(dim=(-2, -1))
    
    diff_bwtn_extrema = maxima_over_last_two_dims-minima_over_last_two_dims
    
    bool_mat_1 = (diff_bwtn_extrema == 0)
    bool_mat_2 = ~bool_mat_1

    normalization_weight = bool_mat_2 / (diff_bwtn_extrema+bool_mat_1)
    normalization_bias = -normalization_weight*minima_over_last_two_dims

    multi_dim_slice = len(image_stack.shape[:-2])*(slice(None),) + (None, None)

    normalized_image_stack = \
        (image_stack*normalization_weight[multi_dim_slice]
         + normalization_bias[multi_dim_slice]).clip(min=0, max=1)

    return normalized_image_stack



class _DistopticaNet(torch.nn.Module):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 mini_batch_norm_eps):
        super().__init__()

        self._num_pixels_across_each_cbed_pattern = \
            num_pixels_across_each_cbed_pattern
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps
        
        self._distoptica_net = self._generate_distoptica_net()

        return None



    def _generate_distoptica_net(self):
        num_filters_in_first_conv_layer = \
            64
        building_block_counts_in_stages = \
            _building_block_counts_in_stages_of_distoptica_net
        num_downsamplings = \
            len(building_block_counts_in_stages)
        num_nodes_in_second_last_layer = \
            (num_filters_in_first_conv_layer * (2**num_downsamplings))

        module_alias = emicroml.modelling._common
        kwargs = {"num_input_channels": \
                  1,
                  "num_filters_in_first_conv_layer": \
                  num_filters_in_first_conv_layer,
                  "kernel_size_of_first_conv_layer": \
                  7,
                  "max_kernel_size_of_resnet_building_blocks": \
                  3,
                  "building_block_counts_in_stages": \
                  building_block_counts_in_stages,
                  "height_of_input_tensor_in_pixels": \
                  self._num_pixels_across_each_cbed_pattern,
                  "width_of_input_tensor_in_pixels": \
                  self._num_pixels_across_each_cbed_pattern,
                  "num_nodes_in_second_last_layer": \
                  num_nodes_in_second_last_layer,
                  "num_nodes_in_last_layer": \
                  8,
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}
        distoptica_net = module_alias._DistopticaNet(**kwargs)

        return distoptica_net



    def forward(self, ml_inputs):
        enhanced_cbed_pattern_images = \
            self._get_and_enhance_cbed_pattern_images(ml_inputs)

        intermediate_tensor = enhanced_cbed_pattern_images
        intermediate_tensor, _ = self._distoptica_net(intermediate_tensor)

        ml_predictions = dict()
        keys = ("quadratic_radial_distortion_amplitudes",
                "spiral_distortion_amplitudes",
                "elliptical_distortion_vectors",
                "parabolic_distortion_vectors",
                "distortion_centers")

        stop = 0

        for key_idx, key in enumerate(keys):
            start = stop
            stop = start + 1 + ("amplitudes" not in key)

            multi_dim_slice = ((slice(None), start)
                                if ("amplitudes" in key)
                                else (slice(None), slice(start, stop)))
            
            output_tensor = intermediate_tensor[multi_dim_slice]
            ml_predictions[key] = output_tensor

        return ml_predictions



    def _get_and_enhance_cbed_pattern_images(self, ml_inputs):
        kwargs = {"image_stack": ml_inputs["cbed_pattern_images"]}
        enhanced_cbed_pattern_images = _min_max_normalize_image_stack(**kwargs)

        gamma = 0.3

        enhanced_cbed_pattern_images = \
            torch.unsqueeze(enhanced_cbed_pattern_images, dim=1)
        enhanced_cbed_pattern_images = \
            torch.pow(enhanced_cbed_pattern_images, gamma)
        enhanced_cbed_pattern_images = \
            kornia.enhance.equalize(enhanced_cbed_pattern_images)

        kwargs = {"input": enhanced_cbed_pattern_images,
                  "min": 0,
                  "max": 1}
        enhanced_cbed_pattern_images = torch.clip(**kwargs)

        return enhanced_cbed_pattern_images



def _check_and_convert_architecture(params):
    obj_name = "architecture"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    architecture = czekitout.convert.to_str_from_str_like(**kwargs)

    kwargs["accepted_strings"] = ("distoptica_net",)
    czekitout.check.if_one_of_any_accepted_strings(**kwargs)

    return architecture



def _check_and_convert_mini_batch_norm_eps(params):
    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_mini_batch_norm_eps
    mini_batch_norm_eps = func_alias(params)

    return mini_batch_norm_eps



def _check_and_convert_normalization_weights(params):
    obj_name = "normalization_weights"

    global_symbol_table = globals()

    params = params.copy()

    func_name = ("_generate_default"
                 "_ml_data_normalization_weights_and_biases_loader")
    func_alias = global_symbol_table[func_name]
    params["ml_data_normalization_weights_and_biases_loader"] = func_alias()

    func_name = "_generate_default_normalization_weights"
    func_alias = global_symbol_table[func_name]
    params["default_normalization_weights"] = func_alias()

    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_normalization_weights
    normalization_weights = func_alias(params)

    return normalization_weights



def _generate_default_normalization_weights():
    obj_name = "normalization_weights"

    ml_data_normalizer = _generate_default_ml_data_normalizer()
    extrema_cache = ml_data_normalizer._extrema_cache

    kwargs = {"extrema_cache": extrema_cache}
    _update_extrema_cache_for_default_normalization_weights_and_biases(**kwargs)

    ml_data_normalizer._update_normalization_weights_and_biases()

    attr_name = "_" + obj_name
    normalization_weights = getattr(ml_data_normalizer, attr_name)

    return normalization_weights



def _update_extrema_cache_for_default_normalization_weights_and_biases(
        extrema_cache):
    kwargs = {"reference_pt": \
              _default_reference_pt,
              "rng_seed": \
              _default_rng_seed,
              "sampling_grid_dims_in_pixels": \
              _default_sampling_grid_dims_in_pixels,
              "least_squares_alg_params": \
              _default_least_squares_alg_params,
              "device_name": \
              _default_device_name,
              "skip_validation_and_conversion": \
              True}
    distortion_model_generator = _DefaultDistortionModelGenerator(**kwargs)

    all_valid_ml_data_dict_keys = _generate_all_valid_ml_data_dict_keys()

    for key_1 in all_valid_ml_data_dict_keys:
        if key_1 not in extrema_cache:
            continue
        for key_2 in ("min", "max"):
                key_3 = "_" + key_1[:-1] + "_" + key_2
                
                obj_from_which_to_get_attr = distortion_model_generator
                attr_name = key_3
                default_value_if_attr_does_not_exist = int(key_2 == "max")
                
                args = (obj_from_which_to_get_attr,
                        attr_name,
                        default_value_if_attr_does_not_exist)
                extrema_cache[key_1][key_2] = getattr(*args)

    return None



def _check_and_convert_normalization_biases(params):
    obj_name = "normalization_biases"

    global_symbol_table = globals()

    params = params.copy()

    func_name = ("_generate_default"
                 "_ml_data_normalization_weights_and_biases_loader")
    func_alias = global_symbol_table[func_name]
    params["ml_data_normalization_weights_and_biases_loader"] = func_alias()

    func_name = "_generate_default_normalization_biases"
    func_alias = global_symbol_table[func_name]
    params["default_normalization_biases"] = func_alias()

    module_alias = emicroml.modelling._common
    func_alias = module_alias._check_and_convert_normalization_biases
    normalization_biases = func_alias(params)

    return normalization_biases



def _generate_default_normalization_biases():
    obj_name = "normalization_biases"

    ml_data_normalizer = _generate_default_ml_data_normalizer()
    extrema_cache = ml_data_normalizer._extrema_cache

    kwargs = {"extrema_cache": extrema_cache}
    _update_extrema_cache_for_default_normalization_weights_and_biases(**kwargs)

    ml_data_normalizer._update_normalization_weights_and_biases()

    attr_name = "_" + obj_name
    normalization_biases = getattr(ml_data_normalizer, attr_name)

    return normalization_biases



def _get_device_name(device):
    kwargs = locals()

    module_alias = emicroml.modelling._common
    func_alias = module_alias._get_device_name
    device_name = func_alias(**kwargs)

    return device_name



_module_alias = \
    emicroml.modelling._common
_default_architecture = \
    "distoptica_net"
_default_mini_batch_norm_eps = \
    _module_alias._default_mini_batch_norm_eps
_default_normalization_weights = \
    _module_alias._default_normalization_weights
_default_normalization_biases = \
    _module_alias._default_normalization_biases
_default_normalizable_elems_of_ml_inputs_are_normalized = \
    _module_alias._default_normalizable_elems_of_ml_inputs_are_normalized
_default_unnormalize_normalizable_elems_of_ml_predictions = \
    _module_alias._default_unnormalize_normalizable_elems_of_ml_predictions



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLModel
class _MLModel(_cls_alias):
    def __init__(self,
                 num_pixels_across_each_cbed_pattern,
                 max_num_disks_in_any_cbed_pattern,
                 architecture,
                 mini_batch_norm_eps,
                 normalization_weights,
                 normalization_biases):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}

        kwargs = \
            {"num_pixels_across_each_cbed_pattern": \
             num_pixels_across_each_cbed_pattern,
             "max_num_disks_in_any_cbed_pattern": \
             max_num_disks_in_any_cbed_pattern}
        variable_axis_size_dict = \
            self._generate_variable_axis_size_dict(**kwargs)
        
        expected_keys_of_ml_inputs = \
            self._generate_expected_keys_of_ml_inputs()

        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLModel
        kwargs = {"ml_data_normalizer": _generate_default_ml_data_normalizer(),
                  "ml_data_type_validator": _MLDataTypeValidator(),
                  "ml_data_value_validator": _MLDataValueValidator(),
                  "ml_data_shape_analyzer": _MLDataShapeAnalyzer(),
                  "variable_axis_size_dict": variable_axis_size_dict,
                  "expected_keys_of_ml_inputs": expected_keys_of_ml_inputs,
                  "subcls_ctor_params": ctor_params}
        cls_alias.__init__(self, **kwargs)

        self._initialize_ml_model_cmpnts(architecture,
                                         num_pixels_across_each_cbed_pattern,
                                         mini_batch_norm_eps)

        return None



    def _generate_variable_axis_size_dict(self,
                                          num_pixels_across_each_cbed_pattern,
                                          max_num_disks_in_any_cbed_pattern):
        variable_axis_size_dict_keys = _generate_variable_axis_size_dict_keys()
        num_keys = len(variable_axis_size_dict_keys)

        variable_axis_size_dict = dict()
        for key_idx, key in enumerate(variable_axis_size_dict_keys):
            if key_idx == 0:
                variable_size_of_axis = None
            elif key_idx == num_keys-1:
                variable_size_of_axis = max_num_disks_in_any_cbed_pattern
            else:
                variable_size_of_axis = num_pixels_across_each_cbed_pattern
                
            variable_axis_size_dict[key] = variable_size_of_axis

        return variable_axis_size_dict



    def _generate_expected_keys_of_ml_inputs(self):
        expected_keys_of_ml_inputs = ("cbed_pattern_images",)

        return expected_keys_of_ml_inputs



    def _check_and_convert_ctor_params(self, ctor_params):
        ctor_params = ctor_params.copy()

        global_symbol_table = globals()
        for ctor_param_name in ctor_params.keys():
            func_name = "_check_and_convert_" + ctor_param_name
            func_alias = global_symbol_table[func_name]
            ctor_params[ctor_param_name] = func_alias(params=ctor_params)

        return ctor_params



    def _initialize_ml_model_cmpnts(self,
                                    architecture,
                                    num_pixels_across_each_cbed_pattern,
                                    mini_batch_norm_eps):
        base_model_cls = _DistopticaNet

        self._base_model = base_model_cls(num_pixels_across_each_cbed_pattern,
                                          mini_batch_norm_eps)

        return None



    def forward(self, ml_inputs):
        ml_predictions = self._base_model(ml_inputs)

        return ml_predictions



    def make_predictions(
            self,
            ml_inputs,
            unnormalize_normalizable_elems_of_ml_predictions=\
            _default_unnormalize_normalizable_elems_of_ml_predictions):
        kwargs = {"obj": ml_inputs, "obj_name": "ml_inputs"}
        ml_inputs = czekitout.convert.to_dict(**kwargs)

        params = {"cbed_pattern_images": \
                  ml_inputs.get("cbed_pattern_images", None),
                  "name_of_obj_alias_of_cbed_pattern_images": \
                  "ml_inputs['cbed_pattern_images']",
                  "target_device": \
                  next(self.parameters()).device}
        cbed_pattern_images = _check_and_convert_cbed_pattern_images(params)
        ml_inputs["cbed_pattern_images"] = cbed_pattern_images

        kwargs = {"ml_inputs": \
                  ml_inputs,
                  "unnormalize_normalizable_elems_of_ml_predictions": \
                  unnormalize_normalizable_elems_of_ml_predictions,
                  "normalizable_elems_of_ml_inputs_are_normalized": \
                  True}
        ml_predictions = super().make_predictions(**kwargs)

        return ml_predictions



    def predict_distortion_models(self,
                                  cbed_pattern_images,
                                  sampling_grid_dims_in_pixels=\
                                  _default_sampling_grid_dims_in_pixels,
                                  least_squares_alg_params=\
                                  _default_least_squares_alg_params):
        params = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        sampling_grid_dims_in_pixels = \
            _check_and_convert_sampling_grid_dims_in_pixels(params)
        least_squares_alg_params = \
            _check_and_convert_least_squares_alg_params(params)

        kwargs ={"ml_inputs": {"cbed_pattern_images": cbed_pattern_images},
                 "unnormalize_normalizable_elems_of_ml_predictions": True}
        ml_predictions = self.make_predictions(**kwargs)

        device = next(self.parameters()).device

        kwargs = {"ml_data_dict": ml_predictions,
                  "sampling_grid_dims_in_pixels": sampling_grid_dims_in_pixels,
                  "least_squares_alg_params": least_squares_alg_params,
                  "device_name": _get_device_name(device)}
        distortion_models = _ml_data_dict_to_distortion_models(**kwargs)

        return distortion_models



def _calc_shifted_q(ml_data_dict, ml_model):
    kwargs = \
        locals()
    distortion_model_set_params = \
        _generate_distortion_model_set_params(**kwargs)

    distortion_centers = distortion_model_set_params["distortion_centers"]

    kwargs = \
        {"ml_model": ml_model, "distortion_centers": distortion_centers}
    cached_objs_of_coord_transform_set = \
        _calc_cached_objs_of_coord_transform_set(**kwargs)

    kwargs = {"cached_objs_of_coord_transform_set": \
              cached_objs_of_coord_transform_set,
              "distortion_model_set_params": \
              distortion_model_set_params}
    q = _calc_q(**kwargs)

    shifted_q = q
    shifted_q[:, :] -= q.mean(dim=(2, 3))[:, :, None, None]

    return shifted_q



def _generate_distortion_model_set_params(ml_data_dict, ml_model):
    key_subset = _generate_keys_related_to_distortion_params()

    distortion_model_set_params = {key: 1.0*ml_data_dict[key]
                                   for key
                                   in key_subset}

    kwargs = {"ml_data_dict": distortion_model_set_params,
              "normalization_weights": ml_model._normalization_weights,
              "normalization_biases": ml_model._normalization_biases}
    _unnormalize_normalizable_elems_in_ml_data_dict(**kwargs)

    return distortion_model_set_params



def _calc_cached_objs_of_coord_transform_set(ml_model, distortion_centers):
    kwargs = locals()
    u_x, u_y = _calc_u_x_and_u_y(**kwargs)

    x_c_D = distortion_centers[:, 0]
    y_c_D = distortion_centers[:, 1]

    u_r_cos_of_u_theta = u_x[:, :, :] - x_c_D[:, None, None]
    u_r_sin_of_u_theta = u_y[:, :, :] - y_c_D[:, None, None]
    
    u_r_sq = (u_r_cos_of_u_theta*u_r_cos_of_u_theta
              + u_r_sin_of_u_theta*u_r_sin_of_u_theta)

    u_r_sq_cos_of_2_u_theta = (u_r_cos_of_u_theta*u_r_cos_of_u_theta
                               - u_r_sin_of_u_theta*u_r_sin_of_u_theta)
    u_r_sq_sin_of_2_u_theta = 2*u_r_cos_of_u_theta*u_r_sin_of_u_theta

    cached_objs_of_coord_transform_set = {"u_x": \
                                          u_x,
                                          "u_y": \
                                          u_y,
                                          "u_r_cos_of_u_theta": \
                                          u_r_cos_of_u_theta,
                                          "u_r_sin_of_u_theta": \
                                          u_r_sin_of_u_theta,
                                          "u_r_sq": \
                                          u_r_sq,
                                          "u_r_sq_cos_of_2_u_theta": \
                                          u_r_sq_cos_of_2_u_theta,
                                          "u_r_sq_sin_of_2_u_theta": \
                                          u_r_sq_sin_of_2_u_theta}

    return cached_objs_of_coord_transform_set



def _calc_u_x_and_u_y(ml_model, distortion_centers):
    sampling_grid_dims_in_pixels = \
        2*(ml_model._base_model._num_pixels_across_each_cbed_pattern,)
    device = \
        distortion_centers.device
    mini_batch_size = \
        distortion_centers.shape[0]

    j_range = torch.arange(sampling_grid_dims_in_pixels[0], device=device)
    i_range = torch.arange(sampling_grid_dims_in_pixels[1], device=device)
        
    pair_of_1d_coord_arrays = ((j_range + 0.5) / j_range.numel(),
                               1 - (i_range + 0.5) / i_range.numel())
    sampling_grid = torch.meshgrid(*pair_of_1d_coord_arrays, indexing="xy")
        
    u_x_shape = (mini_batch_size,) + sampling_grid[0].shape
    u_x = torch.zeros(u_x_shape,
                      dtype=distortion_centers.dtype,
                      device=distortion_centers.device)
    
    u_y = torch.zeros_like(u_x)

    for ml_data_instance_idx in range(mini_batch_size):
        u_x[ml_data_instance_idx] = sampling_grid[0]
        u_y[ml_data_instance_idx] = sampling_grid[1]

    return u_x, u_y



def _calc_q(cached_objs_of_coord_transform_set, distortion_model_set_params):
    u_x = cached_objs_of_coord_transform_set["u_x"]
    u_y = cached_objs_of_coord_transform_set["u_y"]

    q_shape = (u_x.shape[0], 2) + u_x.shape[1:]
    q = torch.zeros(q_shape, dtype=u_x.dtype, device=u_x.device)

    q[:, 0] = u_x
    q[:, 1] = u_y

    kwargs = {"cached_objs_of_coord_transform_set": \
              cached_objs_of_coord_transform_set,
              "distortion_model_set_params": \
              distortion_model_set_params,
              "q": \
              q}
    _add_quadratic_radial_and_spiral_distortion_fields_to_q(**kwargs)
    _add_parabolic_distortion_field_to_q(**kwargs)
    _add_elliptical_distortion_field_to_q(**kwargs)
    
    return q



def _add_quadratic_radial_and_spiral_distortion_fields_to_q(
        cached_objs_of_coord_transform_set, distortion_model_set_params, q):
    u_r_sq = \
        cached_objs_of_coord_transform_set["u_r_sq"]
    u_r_cos_of_u_theta = \
        cached_objs_of_coord_transform_set["u_r_cos_of_u_theta"]
    u_r_sin_of_u_theta = \
        cached_objs_of_coord_transform_set["u_r_sin_of_u_theta"]

    A_r_0_2 = \
        distortion_model_set_params["quadratic_radial_distortion_amplitudes"]
    A_t_0_2 = \
        distortion_model_set_params["spiral_distortion_amplitudes"]

    q[:, 0] += u_r_sq * (u_r_cos_of_u_theta*A_r_0_2[:, None, None]
                         - u_r_sin_of_u_theta*A_t_0_2[:, None, None])
    q[:, 1] += u_r_sq * (u_r_sin_of_u_theta*A_r_0_2[:, None, None]
                         + u_r_cos_of_u_theta*A_t_0_2[:, None, None])

    return None



def _add_parabolic_distortion_field_to_q(cached_objs_of_coord_transform_set,
                                         distortion_model_set_params,
                                         q):
    u_r_sq = \
        cached_objs_of_coord_transform_set["u_r_sq"]
    u_r_sq_cos_of_2_u_theta = \
        cached_objs_of_coord_transform_set["u_r_sq_cos_of_2_u_theta"]
    u_r_sq_sin_of_2_u_theta = \
        cached_objs_of_coord_transform_set["u_r_sq_sin_of_2_u_theta"]

    A_r_1_1 = \
        distortion_model_set_params["parabolic_distortion_vectors"][:, 0]
    B_r_0_1 = \
        distortion_model_set_params["parabolic_distortion_vectors"][:, 1]

    q[:, 0] += ((2.0*u_r_sq + u_r_sq_cos_of_2_u_theta)*A_r_1_1[:, None, None]
                + u_r_sq_sin_of_2_u_theta*B_r_0_1[:, None, None]) / 3.0
    q[:, 1] += ((2.0*u_r_sq - u_r_sq_cos_of_2_u_theta)*B_r_0_1[:, None, None]
                + u_r_sq_sin_of_2_u_theta*A_r_1_1[:, None, None]) / 3.0

    return None



def _add_elliptical_distortion_field_to_q(cached_objs_of_coord_transform_set,
                                          distortion_model_set_params,
                                          q):
    u_r_cos_of_u_theta = \
        cached_objs_of_coord_transform_set["u_r_cos_of_u_theta"]
    u_r_sin_of_u_theta = \
        cached_objs_of_coord_transform_set["u_r_sin_of_u_theta"]

    A_r_2_0 = \
        distortion_model_set_params["elliptical_distortion_vectors"][:, 0]
    B_r_1_0 = \
        distortion_model_set_params["elliptical_distortion_vectors"][:, 1]

    q[:, 0] += (u_r_cos_of_u_theta*A_r_2_0[:, None, None]
                + u_r_sin_of_u_theta*B_r_1_0[:, None, None])
    q[:, 1] += (-u_r_sin_of_u_theta*A_r_2_0[:, None, None]
                + u_r_cos_of_u_theta*B_r_1_0[:, None, None])

    return None



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLMetricCalculator
class _MLMetricCalculator(_cls_alias):
    def __init__(self):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLMetricCalculator
        kwargs = dict()
        cls_alias.__init__(self, **kwargs)

        return None



    def _calc_metrics_of_current_mini_batch(
            self,
            ml_inputs,
            ml_predictions,
            ml_targets,
            ml_model,
            ml_dataset_manager,
            mini_batch_indices_for_entire_training_session):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        metrics_of_current_mini_batch = \
            super()._calc_metrics_of_current_mini_batch(**kwargs)

        kwargs = {"ml_data_dict": ml_targets, "ml_model": ml_model}
        target_shifted_q = _calc_shifted_q(**kwargs)

        kwargs = {"ml_data_dict": ml_predictions, "ml_model": ml_model}
        predicted_shifted_q = _calc_shifted_q(**kwargs)

        method_alias = self._calc_epes_of_adjusted_distortion_fields
        kwargs = {"target_shifted_q": target_shifted_q,
                  "predicted_shifted_q": predicted_shifted_q}
        epes_of_adjusted_distortion_fields = method_alias(**kwargs)

        metrics_of_current_mini_batch = {"epes_of_adjusted_distortion_fields": \
                                         epes_of_adjusted_distortion_fields}

        return metrics_of_current_mini_batch



    def _calc_epes_of_adjusted_distortion_fields(self,
                                                 target_shifted_q,
                                                 predicted_shifted_q):
        calc_euclidean_distances = torch.linalg.vector_norm
        kwargs = {"x": target_shifted_q-predicted_shifted_q, "dim": 1}
        euclidean_distances = calc_euclidean_distances(**kwargs)

        epes = euclidean_distances.mean(dim=(1, 2))
        epes_of_adjusted_distortion_fields = epes

        return epes_of_adjusted_distortion_fields



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLLossCalculator
class _MLLossCalculator(_cls_alias):
    def __init__(self):
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLLossCalculator
        kwargs = dict()
        cls_alias.__init__(self, **kwargs)

        return None



    def _calc_losses_of_current_mini_batch(
            self,
            ml_inputs,
            ml_predictions,
            ml_targets,
            ml_model,
            ml_dataset_manager,
            phase,
            ml_metric_manager,
            mini_batch_indices_for_entire_training_session):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        losses_of_current_mini_batch = \
            super()._calc_losses_of_current_mini_batch(**kwargs)

        metrics_of_current_mini_batch = \
            ml_metric_manager._metrics_of_current_mini_batch

        losses_of_current_mini_batch = {"total": 0.0}

        key_set_1 = ("epes_of_adjusted_distortion_fields",)

        for key_1 in key_set_1:
            key_2 = \
                "total"
            losses_of_current_mini_batch[key_1] = \
                metrics_of_current_mini_batch[key_1].mean()
            losses_of_current_mini_batch[key_2] += \
                losses_of_current_mini_batch[key_1]

        return losses_of_current_mini_batch



_module_alias = \
    emicroml.modelling._common
_default_checkpoints = \
    _module_alias._default_checkpoints
_default_lr_scheduler_manager = \
    _module_alias._default_lr_scheduler_manager
_default_output_dirname = \
    _module_alias._default_output_dirname
_default_misc_model_training_metadata = \
    _module_alias._default_misc_model_training_metadata



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLModelTrainer
class _MLModelTrainer(_cls_alias):
    def __init__(self,
                 ml_dataset_manager,
                 device_name,
                 checkpoints,
                 lr_scheduler_manager,
                 output_dirname,
                 misc_model_training_metadata,
                 skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLModelTrainer
        cls_alias.__init__(self, ctor_params)

        return None


    
    def train_ml_model(self, ml_model, ml_model_param_groups):
        self._ml_metric_calculator = _MLMetricCalculator()
        self._ml_loss_calculator = _MLLossCalculator()

        kwargs = {"ml_model": ml_model,
                  "ml_model_param_groups": ml_model_param_groups}
        super().train_ml_model(**kwargs)

        return None



_module_alias = \
    emicroml.modelling._common
_default_misc_model_testing_metadata = \
    _module_alias._default_misc_model_testing_metadata



_module_alias = emicroml.modelling._common
_cls_alias = _module_alias._MLModelTester
class _MLModelTester(_cls_alias):
    def __init__(self,
                 ml_dataset_manager,
                 device_name,
                 output_dirname,
                 misc_model_testing_metadata,
                 skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        
        module_alias = emicroml.modelling._common
        cls_alias = module_alias._MLModelTester
        cls_alias.__init__(self, ctor_params)

        return None


    
    def test_ml_model(self, ml_model):
        self._ml_metric_calculator = _MLMetricCalculator()

        kwargs = {"ml_model": ml_model}
        super().test_ml_model(**kwargs)

        return None



###########################
## Define error messages ##
###########################

_default_distortion_model_generator_err_msg_1 = \
    ("The distortion model generator has exceeded its programmed maximum "
     "number of attempts {} to generate a valid distortion model: see "
     "traceback for details.")
_default_distortion_model_generator_err_msg_2 = \
    ("The distortion model generator generated a distortion model with a "
     "flow-field of the right-inverse of its corresponding coordinate "
     "transformation that is not well-defined for pixels outside of the mask "
     "frame of the maximum permitted width, which is one sixth of the image "
     "width.")

_check_and_convert_num_pixels_across_each_cbed_pattern_err_msg_1 = \
    ("The object ``num_pixels_across_each_cbed_pattern`` must be positive "
     "integer that is divisible {}.")

_default_cbed_pattern_generator_err_msg_1 = \
    ("The CBED pattern must contain at least {} non-clipped CBED disks.")
_default_cbed_pattern_generator_err_msg_2 = \
    ("The CBED pattern generator{} has exceeded its programmed maximum number "
     "of attempts{} to generate a valid CBED pattern: see traceback for "
     "details.")

_generate_cbed_pattern_signal_err_msg_1 = \
    _default_cbed_pattern_generator_err_msg_2
_generate_cbed_pattern_signal_err_msg_2 = \
    ("The object ``cbed_pattern_generator`` did not generate a valid CBED "
     "pattern, i.e. it did not generate an object of the type "
     "``fakecbed.discretized.CBEDPattern``.")

_check_cbed_pattern_signal_err_msg_1 = \
    ("The object ``cbed_pattern_generator`` must generate a CBED pattern image "
     "that contains a number of CBED disks that does not exceed the maximum "
     "allowed number, as specified by the object "
     "``max_num_disks_in_any_cbed_pattern``.")

_extract_intra_disk_avgs_from_cbed_pattern_signal_err_msg_1 = \
    ("The object ``cbed_pattern_generator`` must generate a CBED pattern with "
     "only CBED disks of the same radius.")

_extract_distortion_param_val_set_from_cbed_pattern_signal_err_msg_1 = \
    ("The object ``cbed_pattern_generator`` must generate a CBED pattern with "
     "which the distortion model used to distort said pattern must be "
     "standard as defined in the library ``distoptica``: see the documentation "
     "of ``distoptica`` for a discussion on such models.")

_unnormalized_ml_data_instance_generator_err_msg_1 = \
    ("The object ``cbed_pattern_generator`` must generate CBED patterns of "
     "consistent dimensions.")

_custom_value_checker_for_cbed_pattern_images_err_msg_1 = \
    ("The HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the file "
     "path ``'{}'`` must contain only images that are normalized such that the "
     "minimum and maximum pixel values are equal to zero and unity "
     "respectively for each image.")
_custom_value_checker_for_cbed_pattern_images_err_msg_2 = \
    ("The object ``{}['{}']`` must contain only images that are normalized "
     "such that the minimum and maximum pixel values are equal to zero and "
     "unity respectively for each image.")

_check_and_convert_cbed_pattern_images_err_msg_1 = \
    ("The object ``{}`` must be an array of three dimensions.")
