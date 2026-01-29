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
r"""A script that is called by various other scripts used for running a single
test from the "first" set of tests of the radial gradient maximization (RGM)
approach to the distortion estimation of convergent beam electron diffraction
(CBED) patterns.

The correct form of the command to run the script is::

  python execute_main_action_steps.py \
         --disk_size=<disk_size> \
         --data_dir_1=<data_dir_1>

where ``<disk_size>`` is a string that specifies the machine learning (ML)
testing dataset against which the RGM approach is tested; and ``<data_dir_1>``
is the absolute path to the top-level data directory containing the input data
for this script.

``<data_dir_1>`` must be the absolute path to an existing directory that
contains the subdirectories located at the paths
``<data_dir_1>/ml_datasets/ml_datasets_for_ml_model_test_set_1/ml_datasets_with_cbed_patterns_of_MoS2_on_amorphous_C``
and ``<data_dir_1>/ml_models``. Let ``<path_to_ml_testing_datasets>`` be the
former subdirectory path. The directory at ``<path_to_ml_testing_datasets>``
must contain an HDF5 file that stores a ML testing dataset with the basename of
the form ``ml_dataset_with_<disk_size>_sized_disks.h5``.

At this point, it is worth noting that every ML data instance stored in every
valid ML testing dataset encodes data about a "fake" CBED pattern. See the
documentation for the class :class:`fakecbed.discretized.CBEDPattern` for a full
discussion on fake CBED patterns and context relevant to the discussion
below. In constructing a fake CBED pattern, one needs to specify a set of
circular, undistorted CBED disk supports, defined in
:math:`\left(u_{x},u_{y}\right)`-space, sharing a common disk radius, with their
centers being specified in :math:`\left(u_{x},u_{y}\right)` coordinates. One
also needs to specify a distortion field to construct a fake CBED pattern. The
supports of the distorted CBED disks that appear in the fake CBED pattern are be
obtained by distorting the aforementioned set of undistorted disk supports
according to the aforementioned distortion field. Let :math:`\left\{
\left(u_{x;c;\text{C};i},u_{y;c;\text{C};i}\right)\right\}_{i}` be the
:math:`\left(u_{x},u_{y}\right)` coordinates of the undistorted disk support
centers, and :math:`\left\{
\left(q_{x;c;\text{C};i},q_{y;c;\text{C};i}\right)\right\}_{i}` be the
corresponding coordinates in :math:`\left(q_{x},q_{y}\right)`-space according to
the distortion field. The RGM approach to estimating the distortion of the fake
CBED pattern can be described as follows:

1. Use the RGM technique, described in Ref. [Mahr1]_ to estimate the subset of
:math:`\left\{ \left(q_{x;c;\text{C};i},q_{y;c;\text{C};i}\right)\right\}_{i}`
corresponding to the distorted CBED disks in the fake CBED pattern that are not
clipped.

2. Determine iteratively via non-linear least squares the distortion field that
minimizes the mean-square error of the estimated coordinates in step 1.

Upon successful completion of the current script, the RGM approach will have
been tested against the ML testing dataset specified by ``<disk_size>``, with
the output having being saved in an HDF5 file generated at the file path
``<data_dir_1>/rgm_test_set_1_results/results_for_cbed_patterns_of_MoS2_on_amorphous_C_with_<disk_size>_sized_disks/rgm_testing_summary_output_data.h5``.
The HDF5 file is guaranteed to contain the following HDF5 objects:

* path_to_ml_testing_dataset: <HDF5 1D dataset>

* total_num_ml_testing_data_instances: <HDF5 0D dataset>

- ml_data_instance_metrics: <HDF5 group>

  - testing: <HDF5 group>

    * epes_of_adjusted_distortion_fields <HDF5 1D dataset>

      + dim_0: "ml testing data instance idx"

Note that the sub-bullet points listed immediately below a given HDF5 dataset
display the HDF5 attributes associated with said HDF5 dataset. Some HDF5
datasets have attributes with names of the form ``"dim_{}".format(i)`` with
``i`` being an integer. Attribute ``"dim_{}".format(i)`` of a given HDF5 dataset
labels the ``i`` th dimension of the underlying array of the dataset.

The HDF5 dataset at the HDF5 path ``"/path_to_ml_testing_dataset"`` stores the
path, as a string, to the ML testing dataset used for the test.

The HDF5 dataset at the HDF5 path
``"/ml_data_instance_metrics/testing/epes_of_adjusted_distortion_fields"`` stores the
end-point errors (EPEs) of the "adjusted" standard distortion fields specified
by the predicted standard coordinate transformation parameter sets, during
testing. For every nonnegative integer ``m`` less than the the total number of
ML testing data instances, the ``m`` th element of the aforementioned HDF5
dataset is the EPE of the adjusted standard distortion field specified by the
``m`` th predicted standard standard coordinate transformation set, during
testing. See the summary documentation of the class
:class:`emicroml.modelling.cbed.distortion.estimation.MLModelTrainer` for a
definition of an adjusted standard distortion field, and how the EPE is
calculated exactly.

This script uses the module
:mod:`emicroml.modelling.cbed.distortion.estimation`. It is recommended that you
consult the documentation of said module as you explore the remainder of this
script.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For parsing command line arguments.
import argparse

# For listing files and subdirectories in a given directory, and for renaming
# directories.
import os

# For setting Python's seed.
import random

# For checking whether certain submodules exists and for importing said
# submodules should they exist.
import importlib



# For general array handling. Note that ``numpy`` needs to be imported before
# ``torch``.
import numpy as np
import torch

# For solving least-squares problems.
import scipy.optimize

# For generating distortion models.
import distoptica

# For moving data from one device to another.
import pyopencl.array

# For listing OpenCL platforms and devices.
import silx.opencl

# For averaging azimuthally images.
detectors = importlib.import_module("pyFAI.detectors")
integrators = (importlib.import_module("pyFAI.integrator.azimuthal")
               if importlib.util.find_spec("pyFAI.integrator")
               else importlib.import_module("pyFAI.azimuthalIntegrator"))

# For creating hyperspy signals and axes.
import hyperspy.signals
import hyperspy.axes

# For loading objects from and saving objects to HDF5 files.
import h5pywrappers

# For cropping 2D hyperspy signals.
import empix

# For timing sections of code.
import time



# For testing ML models.
import emicroml.modelling.cbed.distortion.estimation



##############################################
## Define classes, functions, and constants ##
##############################################

class _CoefficientMatrix():
    def __init__(self,
                 distortion_model_params,
                 distortion_model_param_name_to_row_col_pair_map,
                 pre_factor_matrix):
        self._distortion_model_params = \
            distortion_model_params
        self._distortion_model_param_name_to_row_col_pair_map = \
            distortion_model_param_name_to_row_col_pair_map
        self._pre_factor_matrix = \
            pre_factor_matrix

        self._M = self._pre_factor_matrix.shape[1]

        self._forward_output = None
        self._derivatives = dict()

        return None



    def _eval_forward_output(self, inputs):
        distortion_model_params = \
            self._distortion_model_params
        distortion_model_param_name_to_row_col_pair_map = \
            self._distortion_model_param_name_to_row_col_pair_map
        pre_factor_matrix = \
            self._pre_factor_matrix

        output_tensor = torch.zeros_like(pre_factor_matrix)

        for distortion_model_param_name in distortion_model_params:
            param_name = \
                distortion_model_param_name
            distortion_model_param_val = \
                distortion_model_params[param_name]
            row, col = \
                distortion_model_param_name_to_row_col_pair_map[param_name]

            output_tensor[row, col] = (distortion_model_param_val
                                       * pre_factor_matrix[row, col])

        return output_tensor



    def _eval_derivative(self,
                         name_of_variable_wrt_which_to_perform_derivative,
                         inputs):
        distortion_model_param_name_to_row_col_pair_map = \
            self._distortion_model_param_name_to_row_col_pair_map
        pre_factor_matrix = \
            self._pre_factor_matrix

        param_name = name_of_variable_wrt_which_to_perform_derivative
        map_alias = distortion_model_param_name_to_row_col_pair_map

        output_tensor = torch.zeros_like(pre_factor_matrix)
        if param_name in map_alias:
            row, col = map_alias[param_name]
            output_tensor[row, col] = pre_factor_matrix[row, col]

        return output_tensor



class _Polynomials():
    def __init__(self, coefficient_matrix):
        self._coefficient_matrix = coefficient_matrix

        self._M = self._coefficient_matrix._M
        self._pre_factor_matrix = self._coefficient_matrix._pre_factor_matrix

        self._forward_output = None
        self._derivatives = dict()

        return None


    
    def _eval_forward_output(self, inputs):
        M = self._M
        coefficient_matrix = self._coefficient_matrix
        
        powers_of_u_r = inputs["powers_of_u_r"]

        output_tensor = torch.einsum("nm, mij -> nij",
                                     coefficient_matrix._forward_output,
                                     powers_of_u_r[1:M+1])

        return output_tensor



    def _eval_derivative(self,
                         name_of_variable_wrt_which_to_perform_derivative,
                         inputs):
        M = self._M
        coefficient_matrix = self._coefficient_matrix
        
        variable_name = name_of_variable_wrt_which_to_perform_derivative

        if variable_name == "u_r":
            operand_1 = coefficient_matrix._forward_output
            operand_2 = inputs["derivative_of_powers_of_u_r_wrt_u_r"][0:M]
        else:
            operand_1 = coefficient_matrix._derivatives[variable_name]
            operand_2 = inputs["powers_of_u_r"][0:M]

        operands = (operand_1, operand_2)

        output_tensor = torch.einsum("nm, mij -> nij", *operands)
            
        return output_tensor



class _FourierSeries():
    def __init__(self, cosine_amplitudes, sine_amplitudes):
        self._cosine_amplitudes = cosine_amplitudes
        self._sine_amplitudes = sine_amplitudes

        self._N_cos = cosine_amplitudes._pre_factor_matrix.shape[0]-1
        self._N_sin = sine_amplitudes._pre_factor_matrix.shape[0]
        self._num_azimuthal_orders = max(self._N_cos+1, self._N_sin+1)

        self._M = max(cosine_amplitudes._M, sine_amplitudes._M)

        self._forward_output = None
        self._derivatives = dict()

        return None



    def _eval_forward_output(self, inputs):
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        N_cos = self._N_cos
        N_sin = self._N_sin

        intermediate_tensor_1 = (self._cosine_amplitudes._forward_output
                                 * cosines_of_scaled_u_thetas[0:N_cos+1])
        intermediate_tensor_1 = intermediate_tensor_1.sum(dim=0)

        intermediate_tensor_2 = (self._sine_amplitudes._forward_output
                                 * sines_of_scaled_u_thetas[0:N_sin])
        intermediate_tensor_2 = intermediate_tensor_2.sum(dim=0)

        output_tensor = intermediate_tensor_1+intermediate_tensor_2

        return output_tensor



    def _eval_derivative_wrt_u_r(self, inputs):
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        N_cos = self._N_cos
        N_sin = self._N_sin

        intermediate_tensor_1 = (self._cosine_amplitudes._derivatives["u_r"]
                                 * cosines_of_scaled_u_thetas[0:N_cos+1])
        intermediate_tensor_1 = intermediate_tensor_1.sum(dim=0)

        intermediate_tensor_2 = (self._sine_amplitudes._derivatives["u_r"]
                                 * sines_of_scaled_u_thetas[0:N_sin])
        intermediate_tensor_2 = intermediate_tensor_2.sum(dim=0)

        output_tensor = intermediate_tensor_1+intermediate_tensor_2

        return output_tensor



    def _eval_derivative_wrt_u_theta(self, inputs):
        derivative_of_cosines_of_scaled_u_thetas_wrt_u_theta = \
            inputs["derivative_of_cosines_of_scaled_u_thetas_wrt_u_theta"]
        derivative_of_sines_of_scaled_u_thetas_wrt_u_theta = \
            inputs["derivative_of_sines_of_scaled_u_thetas_wrt_u_theta"]

        N_cos = self._N_cos
        N_sin = self._N_sin

        intermediate_tensor_1 = \
            (self._cosine_amplitudes._forward_output[1:N_cos+1]
             * derivative_of_cosines_of_scaled_u_thetas_wrt_u_theta[0:N_cos])
        intermediate_tensor_1 = \
            intermediate_tensor_1.sum(dim=0)

        intermediate_tensor_2 = \
            (self._sine_amplitudes._forward_output
             * derivative_of_sines_of_scaled_u_thetas_wrt_u_theta[0:N_sin])
        intermediate_tensor_2 = \
            intermediate_tensor_2.sum(dim=0)

        output_tensor = intermediate_tensor_1+intermediate_tensor_2

        return output_tensor



    def _eval_derivative(self,
                         name_of_variable_wrt_which_to_perform_derivative,
                         inputs):
        variable_name = name_of_variable_wrt_which_to_perform_derivative

        if variable_name == "u_r":
            output_tensor = self._eval_derivative_wrt_u_r(inputs)
        elif variable_name == "u_theta":
            output_tensor = self._eval_derivative_wrt_u_theta(inputs)
        else:
            cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
            sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

            N_cos = self._N_cos
            N_sin = self._N_sin

            intermediate_tensor_1 = \
                (self._cosine_amplitudes._derivatives[variable_name]
                 * cosines_of_scaled_u_thetas[0:N_cos+1])
            intermediate_tensor_1 = \
                intermediate_tensor_1.sum(dim=0)

            intermediate_tensor_2 = \
                (self._sine_amplitudes._derivatives[variable_name]
                 * sines_of_scaled_u_thetas[0:N_sin])
            intermediate_tensor_2 = \
                intermediate_tensor_2.sum(dim=0)

            output_tensor = intermediate_tensor_1+intermediate_tensor_2
            
        return output_tensor



def _generate_radial_fourier_series(standard_coord_transform_params, device):
    kwargs = \
        locals()
    radial_cosine_coefficient_matrix = \
        _generate_radial_cosine_coefficient_matrix(**kwargs)
    radial_sine_coefficient_matrix = \
        _generate_radial_sine_coefficient_matrix(**kwargs)

    kwargs = {"coefficient_matrix": radial_cosine_coefficient_matrix}
    radial_cosine_amplitudes = _Polynomials(**kwargs)

    kwargs = {"coefficient_matrix": radial_sine_coefficient_matrix}
    radial_sine_amplitudes = _Polynomials(**kwargs)

    kwargs = {"cosine_amplitudes": radial_cosine_amplitudes,
              "sine_amplitudes": radial_sine_amplitudes}
    radial_fourier_series = _FourierSeries(**kwargs)

    return radial_fourier_series



def _generate_radial_cosine_coefficient_matrix(standard_coord_transform_params,
                                               device):
    standard_coord_transform_params_core_attrs = \
        standard_coord_transform_params.get_core_attrs(deep_copy=False)

    attr_name = \
        "quadratic_radial_distortion_amplitude"
    quadratic_radial_distortion_amplitude = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "elliptical_distortion_vector"
    elliptical_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "parabolic_distortion_vector"
    parabolic_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    distortion_model_params = {"A_r_0_2": quadratic_radial_distortion_amplitude,
                               "A_r_2_0": elliptical_distortion_vector[0],
                               "A_r_1_1": parabolic_distortion_vector[0]}

    distortion_model_param_name_to_row_col_pair_map = {"A_r_0_2": (0, 2),
                                                       "A_r_2_0": (2, 0),
                                                       "A_r_1_1": (1, 1)}

    pre_factor_matrix = torch.tensor(((0.0, 0.0, 1.0),
                                      (0.0, 1.0, 0.0), 
                                      (1.0, 0.0, 0.0)), device=device)

    kwargs = {"distortion_model_params": \
              distortion_model_params,
              "distortion_model_param_name_to_row_col_pair_map": \
              distortion_model_param_name_to_row_col_pair_map,
              "pre_factor_matrix": \
              pre_factor_matrix}
    radial_cosine_coefficient_matrix = _CoefficientMatrix(**kwargs)

    return radial_cosine_coefficient_matrix



def _generate_radial_sine_coefficient_matrix(standard_coord_transform_params,
                                             device):
    standard_coord_transform_params_core_attrs = \
        standard_coord_transform_params.get_core_attrs(deep_copy=False)

    attr_name = \
        "elliptical_distortion_vector"
    elliptical_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "parabolic_distortion_vector"
    parabolic_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    distortion_model_params = {"B_r_1_0": elliptical_distortion_vector[1],
                               "B_r_0_1": parabolic_distortion_vector[1]}

    distortion_model_param_name_to_row_col_pair_map = {"B_r_1_0": (1, 0),
                                                       "B_r_0_1": (0, 1)}

    pre_factor_matrix = torch.tensor(((0.0, 1.0),
                                      (1.0, 0.0)), device=device)

    kwargs = {"distortion_model_params": \
              distortion_model_params,
              "distortion_model_param_name_to_row_col_pair_map": \
              distortion_model_param_name_to_row_col_pair_map,
              "pre_factor_matrix": \
              pre_factor_matrix}
    radial_sine_coefficient_matrix = _CoefficientMatrix(**kwargs)

    return radial_sine_coefficient_matrix



def _generate_tangential_fourier_series(standard_coord_transform_params,
                                        device):
    kwargs = \
        locals()
    tangential_cosine_coefficient_matrix = \
        _generate_tangential_cosine_coefficient_matrix(**kwargs)
    tangential_sine_coefficient_matrix = \
        _generate_tangential_sine_coefficient_matrix(**kwargs)

    kwargs = {"coefficient_matrix": tangential_cosine_coefficient_matrix}
    tangential_cosine_amplitudes = _Polynomials(**kwargs)

    kwargs = {"coefficient_matrix": tangential_sine_coefficient_matrix}
    tangential_sine_amplitudes = _Polynomials(**kwargs)

    kwargs = {"cosine_amplitudes": tangential_cosine_amplitudes,
              "sine_amplitudes": tangential_sine_amplitudes}
    tangential_fourier_series = _FourierSeries(**kwargs)

    return tangential_fourier_series



def _generate_tangential_cosine_coefficient_matrix(
        standard_coord_transform_params, device):
    standard_coord_transform_params_core_attrs = \
        standard_coord_transform_params.get_core_attrs(deep_copy=False)
    
    attr_name = \
        "spiral_distortion_amplitude"
    spiral_distortion_amplitude = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "elliptical_distortion_vector"
    elliptical_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "parabolic_distortion_vector"
    parabolic_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    distortion_model_params = {"A_t_0_2": spiral_distortion_amplitude,
                               "B_r_1_0": elliptical_distortion_vector[1],
                               "B_r_0_1": parabolic_distortion_vector[1]}

    distortion_model_param_name_to_row_col_pair_map = {"A_t_0_2": (0, 2),
                                                       "B_r_1_0": (2, 0),
                                                       "B_r_0_1": (1, 1)}

    pre_factor_matrix = torch.tensor(((0.0, 0.0, 1.0),
                                      (0.0, 1/3, 0.0), 
                                      (1.0, 0.0, 0.0)), device=device)

    kwargs = {"distortion_model_params": \
              distortion_model_params,
              "distortion_model_param_name_to_row_col_pair_map": \
              distortion_model_param_name_to_row_col_pair_map,
              "pre_factor_matrix": \
              pre_factor_matrix}
    tangential_cosine_coefficient_matrix = _CoefficientMatrix(**kwargs)

    return tangential_cosine_coefficient_matrix



def _generate_tangential_sine_coefficient_matrix(
        standard_coord_transform_params, device):
    standard_coord_transform_params_core_attrs = \
        standard_coord_transform_params.get_core_attrs(deep_copy=False)
    
    attr_name = \
        "elliptical_distortion_vector"
    elliptical_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    attr_name = \
        "parabolic_distortion_vector"
    parabolic_distortion_vector = \
        standard_coord_transform_params_core_attrs[attr_name]

    distortion_model_params = {"A_r_2_0": elliptical_distortion_vector[0],
                               "A_r_1_1": parabolic_distortion_vector[0]}

    distortion_model_param_name_to_row_col_pair_map = {"A_r_2_0": (1, 0),
                                                       "A_r_1_1": (0, 1)}

    pre_factor_matrix = torch.tensor(((0.00, -1/3),
                                      (-1.0, 0.00)), device=device)

    kwargs = {"distortion_model_params": \
              distortion_model_params,
              "distortion_model_param_name_to_row_col_pair_map": \
              distortion_model_param_name_to_row_col_pair_map,
              "pre_factor_matrix": \
              pre_factor_matrix}
    tangential_sine_coefficient_matrix = _CoefficientMatrix(**kwargs)

    return tangential_sine_coefficient_matrix



class _CoordTransform():
    def __init__(self, device):
        kwargs = {"standard_coord_transform_params": \
                  distoptica.StandardCoordTransformParams(),
                  "device": \
                  device}
        self._update(**kwargs)

        return None



    def _update(self, standard_coord_transform_params, device):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        self._radial_fourier_series = \
            _generate_radial_fourier_series(**kwargs)
        self._tangential_fourier_series = \
            _generate_tangential_fourier_series(**kwargs)

        standard_coord_transform_params_core_attrs = \
            standard_coord_transform_params.get_core_attrs(deep_copy=False)

        self._device = device
        self._center = standard_coord_transform_params_core_attrs["center"]
        
        args = (self._radial_fourier_series._num_azimuthal_orders,
                self._tangential_fourier_series._num_azimuthal_orders)
        num_azimuthal_orders = max(*args)
        self._azimuthal_orders = torch.arange(0,
                                              num_azimuthal_orders,
                                              device=device)

        self._M = max(self._radial_fourier_series._M,
                      self._tangential_fourier_series._M)
        self._exponents = torch.arange(0, self._M+1, device=device)

        self._forward_output = None
        self._derivatives = dict()

        return None



    def _eval_forward_output(self, inputs):
        u_x = inputs["u_x"]
        u_y = inputs["u_y"]
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        cos_u_theta = cosines_of_scaled_u_thetas[1]
        sin_u_theta = sines_of_scaled_u_thetas[0]

        output_tensor_shape = (2,) + cos_u_theta.shape
        output_tensor = torch.zeros(output_tensor_shape,
                                    dtype=cos_u_theta.dtype,
                                    device=cos_u_theta.device)

        output_tensor[0] = (u_x
                            + (self._radial_fourier_series._forward_output
                               * cos_u_theta)
                            - (self._tangential_fourier_series._forward_output
                               * sin_u_theta))
        output_tensor[1] = (u_y
                            + (self._radial_fourier_series._forward_output
                               * sin_u_theta)
                            + (self._tangential_fourier_series._forward_output
                               * cos_u_theta))

        return output_tensor



    def _eval_derivative_wrt_u_r(self, inputs):
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        cos_u_theta = cosines_of_scaled_u_thetas[1]
        sin_u_theta = sines_of_scaled_u_thetas[0]

        output_tensor_shape = (2,) + cos_u_theta.shape
        output_tensor = torch.zeros(output_tensor_shape,
                                    dtype=cos_u_theta.dtype,
                                    device=cos_u_theta.device)

        intermediate_tensor = 1+self.radial_fourier_series._derivatives["u_r"]

        output_tensor[0] = \
            ((intermediate_tensor
              * cos_u_theta)
             - (self.tangential_fourier_series._derivatives["u_r"]
                * sin_u_theta))
        output_tensor[1] = \
            ((intermediate_tensor
              * sin_u_theta)
             + (self.tangential_fourier_series._derivatives["u_r"]
                * cos_u_theta))

        return output_tensor



    def _eval_derivative_wrt_u_theta(self, inputs):
        powers_of_u_r = inputs["powers_of_u_r"]
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        u_r = powers_of_u_r[1]
        cos_u_theta = cosines_of_scaled_u_thetas[1]
        sin_u_theta = sines_of_scaled_u_thetas[0]

        output_tensor_shape = (2,) + cos_u_theta.shape
        output_tensor = torch.zeros(output_tensor_shape,
                                    dtype=cos_u_theta.dtype,
                                    device=cos_u_theta.device)

        output_tensor[0] = \
            (-u_r*sin_u_theta
             + ((self.radial_fourier_series._derivatives["u_theta"]
                 * cos_u_theta)
                - (self.radial_fourier_series.forward_output
                   * sin_u_theta))
             - ((self.tangential_fourier_series._derivatives["u_theta"]
                 * sin_u_theta)
                + (self.tangential_fourier_series.forward_output
                   * cos_u_theta)))
        output_tensor[1] = \
            (u_r*cos_u_theta
             + ((self.radial_fourier_series._derivatives["u_theta"]
                 * sin_u_theta)
                + (self.radial_fourier_series.forward_output
                   * cos_u_theta))
             + ((self.tangential_fourier_series._derivatives["u_theta"]
                 * cos_u_theta)
                - (self.tangential_fourier_series.forward_output
                   * sin_u_theta)))

        return output_tensor



    def _eval_derivative_wrt_x_c_D(self, inputs):
        derivative_of_u_theta_wrt_u_x = inputs["derivative_of_u_theta_wrt_u_x"]
        cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]

        derivative_of_self_wrt_u_r = self._derivatives["u_r"]
        derivative_of_self_wrt_u_theta = self._derivatives["u_theta"]
        
        cos_u_theta = cosines_of_scaled_u_thetas[1]

        output_tensor_shape = (2,) + cos_u_theta.shape
        output_tensor = torch.zeros(output_tensor_shape,
                                    dtype=cos_u_theta.dtype,
                                    device=cos_u_theta.device)

        output_tensor[0] = \
            (-cos_u_theta*derivative_of_self_wrt_u_r[0]
             - derivative_of_u_theta_wrt_u_x*derivative_of_self_wrt_u_theta[0])
        output_tensor[1] = \
            (-cos_u_theta*derivative_of_self_wrt_u_r[1]
             - derivative_of_u_theta_wrt_u_x*derivative_of_self_wrt_u_theta[1])

        return output_tensor



    def _eval_derivative_wrt_y_c_D(self, inputs):
        derivative_of_u_theta_wrt_u_y = inputs["derivative_of_u_theta_wrt_u_y"]
        sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

        derivative_of_self_wrt_u_r = self._derivatives["u_r"]
        derivative_of_self_wrt_u_theta = self._derivatives["u_theta"]

        sin_u_theta = sines_of_scaled_u_thetas[0]

        output_tensor_shape = (2,) + sin_u_theta.shape
        output_tensor = torch.zeros(output_tensor_shape,
                                    dtype=sin_u_theta.dtype,
                                    device=sin_u_theta.device)

        output_tensor[0] = \
            (-sin_u_theta*derivative_of_self_wrt_u_r[0]
             - derivative_of_u_theta_wrt_u_y*derivative_of_self_wrt_u_theta[0])
        output_tensor[1] = \
            (-sin_u_theta*derivative_of_self_wrt_u_r[1]
             - derivative_of_u_theta_wrt_u_y*derivative_of_self_wrt_u_theta[1])

        return output_tensor



    def _eval_derivative(self,
                         name_of_variable_wrt_which_to_perform_derivative,
                         inputs):
        variable_name = name_of_variable_wrt_which_to_perform_derivative

        if variable_name == "x_c_D":
            output_tensor = self._eval_derivative_wrt_x_c_D(inputs)
        elif variable_name == "y_c_D":
            output_tensor = self._eval_derivative_wrt_y_c_D(inputs)
        else:
            cosines_of_scaled_u_thetas = inputs["cosines_of_scaled_u_thetas"]
            sines_of_scaled_u_thetas = inputs["sines_of_scaled_u_thetas"]

            cos_u_theta = cosines_of_scaled_u_thetas[1]
            sin_u_theta = sines_of_scaled_u_thetas[0]

            output_tensor_shape = (2,) + cos_u_theta.shape
            output_tensor = torch.zeros(output_tensor_shape,
                                        dtype=cos_u_theta.dtype,
                                        device=cos_u_theta.device)

            output_tensor[0] = \
                ((self._radial_fourier_series._derivatives[variable_name]
                  * cos_u_theta)
                 - (self._tangential_fourier_series._derivatives[variable_name]
                    * sin_u_theta))
            output_tensor[1] = \
                ((self._radial_fourier_series._derivatives[variable_name]
                  * sin_u_theta)
                 + (self._tangential_fourier_series._derivatives[variable_name]
                    * cos_u_theta))
            
        return output_tensor



def _x_to_standard_coord_transform_params(x):
    kwargs = \
        {"center": x[0:2],
         "quadratic_radial_distortion_amplitude": x[2],
         "elliptical_distortion_vector": x[3:5],
         "spiral_distortion_amplitude": x[5],
         "parabolic_distortion_vector": x[6:8]}
    standard_coord_transform_params = \
        distoptica.StandardCoordTransformParams(**kwargs)

    return standard_coord_transform_params



def _standard_coord_transform_params_to_x(standard_coord_transform_params):
    standard_coord_transform_params_core_attrs = \
        standard_coord_transform_params.get_core_attrs(deep_copy=False)

    key = "center"
    x_c_D, y_c_D = standard_coord_transform_params_core_attrs[key]

    key = "quadratic_radial_distortion_amplitude"
    A_r_0_2 = standard_coord_transform_params_core_attrs[key]

    key = "elliptical_distortion_vector"
    A_r_2_0, B_r_1_0 = standard_coord_transform_params_core_attrs[key]

    key = "spiral_distortion_amplitude"
    A_t_0_2 = standard_coord_transform_params_core_attrs[key]

    key = "parabolic_distortion_vector"
    A_r_1_1, B_r_0_1 = standard_coord_transform_params_core_attrs[key]

    x = np.array((x_c_D,
                  y_c_D,
                  A_r_0_2,
                  A_r_2_0,
                  B_r_1_0,
                  A_t_0_2,
                  A_r_1_1,
                  B_r_0_1))

    return x



def _update_coord_transform_input_subset_1(coord_transform_inputs,
                                           coord_transform,
                                           u_x,
                                           u_y):
    x_c_D, y_c_D = coord_transform._center
    delta_u_x = u_x - x_c_D
    delta_u_y = u_y - y_c_D
    u_r = torch.sqrt(delta_u_x*delta_u_x + delta_u_y*delta_u_y)
    exponents = coord_transform._exponents
    powers_of_u_r = torch.pow(u_r[None, :, :], exponents[:, None, None])
    
    u_theta = torch.atan2(delta_u_y, delta_u_x)
    azimuthal_orders = coord_transform._azimuthal_orders
    scaled_u_thetas = torch.einsum("i, jk -> ijk", azimuthal_orders, u_theta)
    cosines_of_scaled_u_thetas = torch.cos(scaled_u_thetas)
    sines_of_scaled_u_thetas = torch.sin(scaled_u_thetas[1:])

    local_obj_subset = locals()
    
    coord_transform_input_key_subset_1 = \
        _generate_coord_transform_input_key_subset_1()

    for key in coord_transform_input_key_subset_1:
        elem = local_obj_subset[key]
        _set_coord_transform_inputs_elem(coord_transform_inputs, key, elem)

    return None



def _generate_coord_transform_input_key_subset_1():
    coord_transform_input_key_subset_1 = \
        ("u_x",
         "u_y",
         "delta_u_x",
         "delta_u_y",
         "powers_of_u_r",
         "cosines_of_scaled_u_thetas",
         "sines_of_scaled_u_thetas")

    return coord_transform_input_key_subset_1



def _set_coord_transform_inputs_elem(coord_transform_inputs, key, elem):
    if key in coord_transform_inputs:
        coord_transform_inputs[key][:] = elem[:]
    else:
        coord_transform_inputs[key] = elem

    return None



def _update_coord_transform_input_subset_2(coord_transform_inputs,
                                           coord_transform):
    exponents = coord_transform._exponents
    M = coord_transform._M
    powers_of_u_r = coord_transform_inputs["powers_of_u_r"]
    derivative_of_powers_of_u_r_wrt_u_r = torch.einsum("i, ijk -> ijk",
                                                       exponents[1:M+1],
                                                       powers_of_u_r[0:M])

    azimuthal_orders = \
        coord_transform._azimuthal_orders
    sines_of_scaled_u_thetas = \
        coord_transform_inputs["sines_of_scaled_u_thetas"]
    cosines_of_scaled_u_thetas = \
        coord_transform_inputs["cosines_of_scaled_u_thetas"]

    derivative_of_cosines_of_scaled_u_thetas_wrt_u_theta = \
        torch.einsum("i, ijk -> ijk",
                     azimuthal_orders[1:],
                     -sines_of_scaled_u_thetas)
    derivative_of_sines_of_scaled_u_thetas_wrt_u_theta = \
        torch.einsum("i, ijk -> ijk",
                     azimuthal_orders[1:],
                     cosines_of_scaled_u_thetas[1:])

    bool_mat_1 = (powers_of_u_r[1] == 0)
    bool_mat_2 = ~bool_mat_1
    divisor = powers_of_u_r[1]*powers_of_u_r[1] + bool_mat_1
    delta_u_x = coord_transform_inputs["delta_u_x"]
    delta_u_y = coord_transform_inputs["delta_u_y"]
    derivative_of_u_theta_wrt_u_x = (-delta_u_y/divisor) * bool_mat_2
    derivative_of_u_theta_wrt_u_y = (delta_u_x/divisor) * bool_mat_2

    local_obj_subset = locals()

    coord_transform_input_key_subset_2 = \
        _generate_coord_transform_input_key_subset_2()

    for key in coord_transform_input_key_subset_2:
        elem = local_obj_subset[key]
        _set_coord_transform_inputs_elem(coord_transform_inputs, key, elem)

    return None



def _generate_coord_transform_input_key_subset_2():
    coord_transform_input_key_subset_2 = \
        ("derivative_of_powers_of_u_r_wrt_u_r",
         "derivative_of_cosines_of_scaled_u_thetas_wrt_u_theta",
         "derivative_of_sines_of_scaled_u_thetas_wrt_u_theta",
         "derivative_of_u_theta_wrt_u_x",
         "derivative_of_u_theta_wrt_u_y")

    return coord_transform_input_key_subset_2



def _get_device(device_name):
    if device_name is None:
        cuda_is_available = torch.cuda.is_available()
        device_name = "cuda"*cuda_is_available + "cpu"*(1-cuda_is_available)

    device = torch.device(device_name)

    return device



def _get_device_name(device):
    device_name = (device.type
                   + (device.index != None)*(":{}".format(device.index)))

    return device_name



class _LeastSquaresProblemSolver():
    def __init__(self,
                 u_sample,
                 q_sample,
                 max_num_iterations,
                 sampling_grid_dims_in_pixels,
                 device_name):
        self._u_sample = u_sample
        self._q_sample = q_sample
        self._max_num_iterations = max_num_iterations
        self._sampling_grid_dims_in_pixels = sampling_grid_dims_in_pixels
        self._device_name = device_name

        self._num_residuals = u_sample.numel()
        self._device = _get_device(device_name)

        self._coord_transform = _CoordTransform(device=self._device)
        self._coord_transform_inputs = dict()

        return None



    def _solve(self):
        kwargs = {"fun": self._objective_func,
                  "x0": 2*(0.5,) + 6*(0.0,),
                  "jac": self._jacobian,
                  "method": "lm",
                  "max_nfev": self._max_num_iterations}
        minimization_result = scipy.optimize.least_squares(**kwargs)

        kwargs = \
            {"x": minimization_result.x}
        standard_coord_transform_params = \
            _x_to_standard_coord_transform_params(**kwargs)

        kwargs = \
            {"standard_coord_transform_params": \
             standard_coord_transform_params,
             "sampling_grid_dims_in_pixels": \
             self._sampling_grid_dims_in_pixels,
             "device_name": \
             self._device_name}
        distortion_model = \
            distoptica.generate_standard_distortion_model(**kwargs)

        final_val_of_cost_function = minimization_result.cost

        return distortion_model, final_val_of_cost_function



    def _objective_func(self, x):
        kwargs = {"standard_coord_transform_params": \
                  _x_to_standard_coord_transform_params(x),
                  "device": \
                  self._device}
        self._coord_transform._update(**kwargs)

        kwargs = {"coord_transform": self._coord_transform,
                  "u_x": self._u_sample[0],
                  "u_y": self._u_sample[1],
                  "coord_transform_inputs": self._coord_transform_inputs}
        _update_coord_transform_input_subset_1(**kwargs)

        obj_subset_3 = self._generate_obj_subset_3()
        
        for obj in obj_subset_3:
            kwargs = {"inputs": self._coord_transform_inputs}
            obj._forward_output = obj._eval_forward_output(**kwargs)

        residuals = self._q_sample-self._coord_transform._forward_output
        result = np.array(torch.flatten(residuals).tolist())

        return result



    def _generate_obj_subset_1(self):
        radial_fourier_series = \
            self._coord_transform._radial_fourier_series
        tangential_fourier_series = \
            self._coord_transform._tangential_fourier_series

        obj_subset_1 = \
            (radial_fourier_series._cosine_amplitudes._coefficient_matrix,
             radial_fourier_series._sine_amplitudes._coefficient_matrix,
             tangential_fourier_series._cosine_amplitudes._coefficient_matrix,
             tangential_fourier_series._sine_amplitudes._coefficient_matrix,
             radial_fourier_series._cosine_amplitudes,
             radial_fourier_series._sine_amplitudes,
             tangential_fourier_series._cosine_amplitudes,
             tangential_fourier_series._sine_amplitudes)

        return obj_subset_1



    def _generate_obj_subset_2(self):
        radial_fourier_series = \
            self._coord_transform._radial_fourier_series
        tangential_fourier_series = \
            self._coord_transform._tangential_fourier_series

        obj_subset_2 = self._generate_obj_subset_1()
        obj_subset_2 += (radial_fourier_series,
                         tangential_fourier_series)

        return obj_subset_2



    def _generate_obj_subset_3(self):
        obj_subset_3 = self._generate_obj_subset_2()
        obj_subset_3 += (self._coord_transform,)

        return obj_subset_3



    def _generate_obj_subsets(self):
        obj_subset_1 = self._generate_obj_subset_1()
        obj_subset_2 = self._generate_obj_subset_2()
        obj_subset_3 = self._generate_obj_subset_3()
        
        obj_subsets = (obj_subset_1, obj_subset_2, obj_subset_3)

        return obj_subsets



    def _jacobian(self, x):
        kwargs = {"coord_transform": self._coord_transform,
                  "coord_transform_inputs": self._coord_transform_inputs}
        _update_coord_transform_input_subset_2(**kwargs)

        obj_subsets = self._generate_obj_subsets()
        variable_name_subsets = self._generate_variable_name_subsets()
        zip_obj = zip(obj_subsets, variable_name_subsets[:-1])
        
        for obj_subset, variable_name_subset in zip_obj:
            for obj in obj_subset:
                for variable_name in variable_name_subset:
                    kwargs = \
                        {"inputs": \
                         self._coord_transform_inputs,
                         "name_of_variable_wrt_which_to_perform_derivative": \
                         variable_name}
                    obj._derivatives[variable_name] = \
                        obj._eval_derivative(**kwargs)

        variable_name_subset = variable_name_subsets[-1]

        result = np.zeros((self._num_residuals, x.size))
        for col, variable_name in enumerate(variable_name_subset):
            derivative = self._coord_transform._derivatives[variable_name]
            result[:, col] = -np.array(torch.flatten(derivative).tolist())

        return result



    def _generate_variable_name_subset_1(self):
        variable_name_subset_1 = ("A_r_0_2",
                                  "A_r_2_0",
                                  "B_r_1_0",
                                  "A_t_0_2",
                                  "A_r_1_1",
                                  "B_r_0_1",
                                  "u_r")

        return variable_name_subset_1



    def _generate_variable_name_subset_2(self):
        variable_name_subset_2 = self._generate_variable_name_subset_1()
        variable_name_subset_2 += ("u_theta",)

        return variable_name_subset_2



    def _generate_variable_name_subset_3(self):
        variable_name_subset_3 = self._generate_variable_name_subset_2()
        variable_name_subset_3 += ("x_c_D", "y_c_D")

        return variable_name_subset_3



    def _generate_variable_name_subset_4(self):
        variable_name_subset_4 = self._generate_variable_name_subset_1()
        variable_name_subset_4 = (("x_c_D", "y_c_D")
                                  + variable_name_subset_4[:-1])

        return variable_name_subset_4



    def _generate_variable_name_subsets(self):
        variable_name_subset_1 = self._generate_variable_name_subset_1()
        variable_name_subset_2 = self._generate_variable_name_subset_2()
        variable_name_subset_3 = self._generate_variable_name_subset_3()
        variable_name_subset_4 = self._generate_variable_name_subset_4()
        
        variable_name_subsets = (variable_name_subset_1,
                                 variable_name_subset_2,
                                 variable_name_subset_3,
                                 variable_name_subset_4)

        return variable_name_subsets



def test_rgm_approach_against_ml_data_dict(ml_data_dict):
    target_distortion_model = \
        _extract_target_distortion_model_from_ml_data_dict(ml_data_dict)
    predicted_distortion_model = \
        _predict_distortion_model_from_ml_data_dict(ml_data_dict)

    target_flow_field_of_coord_transform = \
        target_distortion_model.flow_field_of_coord_transform
    predicted_flow_field_of_coord_transform = \
        predicted_distortion_model.flow_field_of_coord_transform

    kwargs = {"distortion_model": target_distortion_model,
              "flow_field": target_flow_field_of_coord_transform}
    _add_flow_field_offset(**kwargs)

    kwargs = {"distortion_model": predicted_distortion_model,
              "flow_field": predicted_flow_field_of_coord_transform}
    _add_flow_field_offset(**kwargs)

    diff_shape = (2,) + target_flow_field_of_coord_transform[0].shape
    diff = torch.zeros(diff_shape, device=target_distortion_model.device)
    diff[0] = (target_flow_field_of_coord_transform[0]
               - predicted_flow_field_of_coord_transform[0])
    diff[1] = (target_flow_field_of_coord_transform[1]
               - predicted_flow_field_of_coord_transform[1])

    calc_euclidean_distances = torch.linalg.vector_norm
    kwargs = {"x": diff, "dim": 0}
    euclidean_distances = calc_euclidean_distances(**kwargs)

    epe_of_adjusted_distortion_field = \
        euclidean_distances.mean(dim=(0, 1)).item()

    return epe_of_adjusted_distortion_field



def _extract_target_distortion_model_from_ml_data_dict(ml_data_dict):
    func_name = ("_extract_target_standard_coord_transform_params"
                 "_from_ml_data_dict")
    func_alias = globals()[func_name]
    target_standard_coord_transform_params = func_alias(ml_data_dict)

    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    device_name = _get_device_name_from_ml_data_dict(ml_data_dict)

    kwargs = \
        {"standard_coord_transform_params": \
         target_standard_coord_transform_params,
         "sampling_grid_dims_in_pixels": \
         sampling_grid_dims_in_pixels,
         "device_name": \
         device_name}
    target_distortion_model = \
        distoptica.generate_standard_distortion_model(**kwargs)

    return target_distortion_model



def _extract_target_standard_coord_transform_params_from_ml_data_dict(
        ml_data_dict):
    kwargs = \
        {"center": \
         ml_data_dict["distortion_centers"][0].tolist(),
         "quadratic_radial_distortion_amplitude": \
         ml_data_dict["quadratic_radial_distortion_amplitudes"][0].item(),
         "elliptical_distortion_vector": \
         ml_data_dict["elliptical_distortion_vectors"][0].tolist(),
         "spiral_distortion_amplitude": \
         ml_data_dict["spiral_distortion_amplitudes"][0].item(),
         "parabolic_distortion_vector": \
         ml_data_dict["parabolic_distortion_vectors"][0].tolist()}
    target_standard_coord_transform_params = \
        distoptica.StandardCoordTransformParams(**kwargs)

    return target_standard_coord_transform_params



def _get_device_name_from_ml_data_dict(ml_data_dict):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]

    device = cbed_pattern_images.device

    device_name = _get_device_name(device)

    return device_name



def _predict_distortion_model_from_ml_data_dict(ml_data_dict):
    kwargs = locals()
    target_u_sample = _extract_target_u_sample_from_ml_data_dict(**kwargs)
    target_q_sample = _extract_target_q_sample_from_ml_data_dict(**kwargs)

    kwargs["target_q_sample"] = target_q_sample
    predicted_q_sample = _predict_q_sample_from_ml_data_dict(**kwargs)

    kwargs = {"predicted_q_sample": predicted_q_sample,
              "target_q_sample": target_q_sample}
    outlier_registry = _identify_outliers_of_predicted_q_sample(**kwargs)

    target_u_sample = target_u_sample[:, ~outlier_registry][:, None, :]
    predicted_q_sample = predicted_q_sample[:, ~outlier_registry][:, None, :]

    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    kwargs = {"u_sample": target_u_sample,
              "q_sample": predicted_q_sample,
              "max_num_iterations": 100,
              "sampling_grid_dims_in_pixels": sampling_grid_dims_in_pixels,
              "device_name": _get_device_name_from_ml_data_dict(ml_data_dict)}
    least_squares_problem_solver = _LeastSquaresProblemSolver(**kwargs)

    predicted_distortion_model, _ = least_squares_problem_solver._solve()

    return predicted_distortion_model



def _extract_target_u_sample_from_ml_data_dict(ml_data_dict):
    max_num_disks_to_consider = 13
    single_dim_slice = slice(0, max_num_disks_to_consider)

    disk_clipping_registry = \
        ml_data_dict["disk_clipping_registries"][0][single_dim_slice]
    undistorted_disk_center_subset = \
        ml_data_dict["undistorted_disk_center_sets"][0][single_dim_slice]

    device = disk_clipping_registry.device

    target_u_sample_shape = (2, 1, torch.sum(~disk_clipping_registry).item())
    target_u_sample = torch.zeros(target_u_sample_shape, device=device)

    undistorted_disk_center_idx = 0
    unclipped_disk_count = 0
    
    for undistorted_disk_center in undistorted_disk_center_subset:
        if not disk_clipping_registry[undistorted_disk_center_idx].item():
            target_u_sample[0, 0, unclipped_disk_count] = \
                undistorted_disk_center[0]
            target_u_sample[1, 0, unclipped_disk_count] = \
                undistorted_disk_center[1]
            
            unclipped_disk_count += 1
            
        undistorted_disk_center_idx += 1

    return target_u_sample



def _extract_target_q_sample_from_ml_data_dict(ml_data_dict):
    target_u_sample = _extract_target_u_sample_from_ml_data_dict(ml_data_dict)

    func_name = ("_extract_target_standard_coord_transform_params"
                 "_from_ml_data_dict")
    func_alias = globals()[func_name]
    target_standard_coord_transform_params = func_alias(ml_data_dict)

    kwargs = {"u_sample": target_u_sample,
              "q_sample": target_u_sample,  # Tensor doesn't matter here.
              "max_num_iterations": None,
              "sampling_grid_dims_in_pixels": None,
              "device_name": _get_device_name_from_ml_data_dict(ml_data_dict)}
    least_squares_problem_solver = _LeastSquaresProblemSolver(**kwargs)

    kwargs = {"standard_coord_transform_params": \
              target_standard_coord_transform_params}
    x = _standard_coord_transform_params_to_x(**kwargs)

    least_squares_problem_solver._objective_func(x)

    target_q_sample = \
        least_squares_problem_solver._coord_transform._forward_output

    return target_q_sample



def _predict_q_sample_from_ml_data_dict(ml_data_dict, target_q_sample):
    kwargs = {"ml_data_dict": ml_data_dict}
    rebinning_engine = _generate_rebinning_engine_from_ml_data_dict(**kwargs)

    num_target_q_pts = target_q_sample.shape[-1]

    predicted_q_sample = torch.zeros_like(target_q_sample)
    
    for target_q_pt_idx in range(num_target_q_pts):
        target_q_pt = np.array(target_q_sample[:, 0, target_q_pt_idx].tolist())

        kwargs = {"ml_data_dict": ml_data_dict,
                  "target_q_pt": target_q_pt,
                  "rebinning_engine": rebinning_engine}
        predicted_q_pt = _predict_q_pt_from_ml_data_dict(**kwargs)

        predicted_q_sample[0, 0, target_q_pt_idx] = predicted_q_pt[0]
        predicted_q_sample[1, 0, target_q_pt_idx] = predicted_q_pt[1]

    return predicted_q_sample



def _generate_rebinning_engine_from_ml_data_dict(ml_data_dict):
    kwargs = \
        locals()
    azimuthal_integrator = \
        _generate_azimuthal_integrator_from_ml_data_dict(**kwargs)
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)
    radial_range = \
        _calc_radial_range_from_ml_data_dict(**kwargs)
    num_bins = \
        _calc_num_bins_from_ml_data_dict(**kwargs)

    blank_image = np.zeros(crop_window_1_dims_in_pixels)

    opencl_device_id = _get_opencl_device_id()

    kwargs = {"data": blank_image,
              "npt": num_bins,
              "radial_range": (radial_range[0]*1000, radial_range[1]*1000),
              "unit": "r_mm",
              "correctSolidAngle": False,
              "method": ("full", "csr", "opencl", opencl_device_id)}
    integration_result = azimuthal_integrator.integrate1d(**kwargs)

    integration_method = integration_result.method

    rebinning_engines = azimuthal_integrator.engines
    rebinning_engine = rebinning_engines[integration_method].engine

    return rebinning_engine



def _generate_azimuthal_integrator_from_ml_data_dict(ml_data_dict):
    kwargs = \
        locals()
    detector = \
        _generate_detector_from_ml_data_dict(**kwargs)
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)

    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    # We require ``L >> max(v_pixel_size, h_pixel_size)``.
    h_pixel_size = abs(1/sampling_grid_dims_in_pixels[0])
    v_pixel_size = h_pixel_size
    L = 10000 * max(v_pixel_size, h_pixel_size)

    # ``pone_1`` and ``poni_2`` are the vertical and horizontal displacements
    # of the reference point, from which to perform the azimuthal integration,
    # from the top left corner of the input signal.
    poni_1 = ((crop_window_1_dims_in_pixels[1]-1)/2)*v_pixel_size
    poni_2 = ((crop_window_1_dims_in_pixels[0]-1)/2)*h_pixel_size

    # ``integrators`` is an alias to a pyFAI submodule that was imported near
    # the top of the current file using the ``importlib.import_module``
    # function.
    AzimuthalIntegrator = integrators.AzimuthalIntegrator
    
    kwargs = {"dist": L,
              "poni1": poni_1,
              "poni2": poni_2,
              "detector": detector}
    azimuthal_integrator = AzimuthalIntegrator(**kwargs)

    return azimuthal_integrator



def _generate_detector_from_ml_data_dict(ml_data_dict):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    h_pixel_size = abs(1/sampling_grid_dims_in_pixels[0])
    v_pixel_size = h_pixel_size

    # ``detectors`` is an alias to a pyFAI submodule that was imported near the
    # top of the current file using the ``importlib.import_module`` function.
    Detector = detectors.Detector

    kwargs = {"pixel1": v_pixel_size, "pixel2": h_pixel_size}
    detector = Detector(**kwargs)

    return detector



def _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(ml_data_dict):
    kwargs = locals()
    radial_range = _calc_radial_range_from_ml_data_dict(**kwargs)

    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    h_pixel_size = abs(1/sampling_grid_dims_in_pixels[0])
    v_pixel_size = h_pixel_size

    crop_window_1_dims_in_pixels = \
        2*(2*int(np.ceil(radial_range[1]/min(h_pixel_size, v_pixel_size)))+1,)

    return crop_window_1_dims_in_pixels



def _calc_radial_range_from_ml_data_dict(ml_data_dict):
    common_undistorted_disk_radius = \
        ml_data_dict["common_undistorted_disk_radii"][0].item()

    radial_range = common_undistorted_disk_radius*np.array((0.0, 2.0))

    return radial_range



def _get_opencl_device_id():
    opencl_device_id = (silx.opencl.ocl.select_device(dtype="cpu")
                        if (silx.opencl.ocl.select_device(dtype="gpu") is None)
                        else silx.opencl.ocl.select_device(dtype="gpu"))

    return opencl_device_id



def _predict_q_pt_from_ml_data_dict(ml_data_dict,
                                    target_q_pt,
                                    rebinning_engine):
    kwargs = \
        locals()
    cropped_image_stack = \
        _extract_cropped_image_stack_from_ml_data_dict(**kwargs)

    kwargs = {"ml_data_dict": ml_data_dict}
    num_bins = _calc_num_bins_from_ml_data_dict(**kwargs)

    func_alias = \
        _calc_bin_coords_and_intensity_profiles_from_cropped_image_stack
    kwargs = \
        {"cropped_image_stack": cropped_image_stack,
         "num_bins": num_bins,
         "rebinning_engine": rebinning_engine}
    bin_coords, intensity_profiles = \
        func_alias(**kwargs)

    kwargs = {"ml_data_dict": ml_data_dict, "target_q_pt": target_q_pt}
    q_shifts = _generate_q_shifts_from_ml_data_dict(**kwargs)

    common_undistorted_disk_radius = \
        ml_data_dict["common_undistorted_disk_radii"][0].item()

    kwargs = \
        {"bin_coords": bin_coords,
         "common_undistorted_disk_radius": common_undistorted_disk_radius,
         "intensity_profiles": intensity_profiles,
         "q_shifts": q_shifts}
    q_shift_corresponding_to_max_rgm_metric = \
        _select_q_shift_corresponding_to_max_rgm_metric(**kwargs)

    predicted_q_pt = target_q_pt + q_shift_corresponding_to_max_rgm_metric

    return predicted_q_pt



def _extract_cropped_image_stack_from_ml_data_dict(ml_data_dict,
                                                   target_q_pt,
                                                   rebinning_engine):
    kwargs = \
        {"ml_data_dict": ml_data_dict}
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)
    row_col_offset_pairs = \
        _generate_row_col_offset_pairs_from_ml_data_dict(**kwargs)

    kwargs["target_q_pt"] = target_q_pt
    signal = _generate_signal_from_ml_data_dict(**kwargs)

    num_cropped_images_in_stack = len(row_col_offset_pairs)
    cropped_image_stack_shape = ((num_cropped_images_in_stack,)
                                 + crop_window_1_dims_in_pixels)
    cropped_image_stack = np.zeros(cropped_image_stack_shape)

    for cropped_image_idx in range(num_cropped_images_in_stack):
        row_offset, col_offset = row_col_offset_pairs[cropped_image_idx]

        start = row_offset
        stop = start+crop_window_1_dims_in_pixels[1]
        single_dim_slice_1 = slice(start, stop)
        
        start = col_offset
        stop = start+crop_window_1_dims_in_pixels[0]
        single_dim_slice_2 = slice(start, stop)
        
        multi_dim_slice = (single_dim_slice_1, single_dim_slice_2)
        
        cropped_image = signal.data[multi_dim_slice]
        cropped_image_stack[cropped_image_idx] = cropped_image

    kwargs = {"queue": rebinning_engine.queue, "ary": cropped_image_stack}
    cropped_image_stack = pyopencl.array.to_device(**kwargs)

    return cropped_image_stack



def _generate_row_col_offset_pairs_from_ml_data_dict(ml_data_dict):
    common_undistorted_disk_radius = \
        ml_data_dict["common_undistorted_disk_radii"][0].item()

    kwargs = {"ml_data_dict": ml_data_dict}
    q_x_shift_step = _calc_q_x_shift_step_from_ml_data_dict(**kwargs)

    max_q_x_shift = 0.4*common_undistorted_disk_radius
    
    num_nonnegative_q_x_shifts = int(max_q_x_shift/q_x_shift_step)

    num_row_col_offset_pairs = (2*num_nonnegative_q_x_shifts+1)**2

    row_col_offset_pairs = tuple()
    for row_col_offset_pair_idx in range(num_row_col_offset_pairs):
        row_offset = (row_col_offset_pair_idx
                      // (2*num_nonnegative_q_x_shifts+1))
        col_offset = (row_col_offset_pair_idx
                      % (2*num_nonnegative_q_x_shifts+1))
        row_col_offset_pair = (row_offset, col_offset)
        row_col_offset_pairs += (row_col_offset_pair,)

    return row_col_offset_pairs



def _calc_q_x_shift_step_from_ml_data_dict(ml_data_dict):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    q_x_shift_step = 1/sampling_grid_dims_in_pixels[0]

    return q_x_shift_step



def _calc_q_y_shift_step_from_ml_data_dict(ml_data_dict):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]
    
    q_y_shift_step = -1/sampling_grid_dims_in_pixels[1]

    return q_y_shift_step



def _generate_signal_from_ml_data_dict(ml_data_dict, target_q_pt):
    crop_window_2_dims_in_pixels = \
        _calc_crop_window_2_dims_in_pixels_from_ml_data_dict(ml_data_dict)

    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    cbed_pattern_image = cbed_pattern_images[0].numpy(force=True)

    V = 1000
    cbed_pattern_image_rescaled = np.log(cbed_pattern_image*V+1)

    signal = hyperspy.signals.Signal2D(data=cbed_pattern_image)

    sizes = signal.axes_manager.signal_shape
    scales = (1/sizes[0], -1/sizes[1])
    offsets = (0.5*scales[0], 1+0.5*scales[1])
    num_axes = len(sizes)

    for axis_idx in range(num_axes):
        axis = hyperspy.axes.UniformDataAxis(size=sizes[axis_idx],
                                             scale=scales[axis_idx],
                                             offset=offsets[axis_idx])
        signal.axes_manager[axis_idx].update_from(axis)
        signal.axes_manager[axis_idx].name = axis.name

    kwargs = {"center": target_q_pt,
              "window_dims": crop_window_2_dims_in_pixels,
              "pad_mode": "zeros",
              "apply_symmetric_mask": False}
    optional_params = empix.OptionalCroppingParams(**kwargs)

    kwargs = {"input_signal": signal, "optional_params": optional_params}
    signal = empix.crop(**kwargs)

    return signal



def _calc_crop_window_2_dims_in_pixels_from_ml_data_dict(ml_data_dict):
    kwargs = \
        locals()
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)
    row_col_offset_pairs = \
        _generate_row_col_offset_pairs_from_ml_data_dict(**kwargs)

    num_row_col_offset_pairs = len(row_col_offset_pairs)
    num_nonnegative_q_x_shifts = round((np.sqrt(num_row_col_offset_pairs)-1)/2)

    crop_window_2_dims_in_pixels = \
        (crop_window_1_dims_in_pixels[0] + 2*num_nonnegative_q_x_shifts,
         crop_window_1_dims_in_pixels[1] + 2*num_nonnegative_q_x_shifts)

    return crop_window_2_dims_in_pixels



def _calc_num_bins_from_ml_data_dict(ml_data_dict):
    kwargs = \
        locals()
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)

    num_bins = crop_window_1_dims_in_pixels[0]

    return num_bins



def _calc_bin_coords_and_intensity_profiles_from_cropped_image_stack(
        cropped_image_stack,
        num_bins,
        rebinning_engine):
    num_cropped_images_in_stack = len(cropped_image_stack)

    intensity_profiles_shape = (num_cropped_images_in_stack, num_bins)
    intensity_profiles = np.zeros(intensity_profiles_shape)

    rgm_metrics = tuple()

    for cropped_image_idx in range(num_cropped_images_in_stack):
        cropped_image = cropped_image_stack[cropped_image_idx]
        integration_result = rebinning_engine.integrate_ng(cropped_image)
        bin_coords = integration_result.position
        intensity_profiles[cropped_image_idx] = integration_result.intensity

    return bin_coords, intensity_profiles



def _generate_q_shifts_from_ml_data_dict(ml_data_dict, target_q_pt):
    kwargs = \
        {"ml_data_dict": ml_data_dict}
    crop_window_1_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)
    crop_window_2_dims_in_pixels = \
        _calc_crop_window_1_dims_in_pixels_from_ml_data_dict(**kwargs)
    row_col_offset_pairs = \
        _generate_row_col_offset_pairs_from_ml_data_dict(**kwargs)
    q_x_shift_step = \
        _calc_q_x_shift_step_from_ml_data_dict(**kwargs)
    q_y_shift_step = \
        _calc_q_y_shift_step_from_ml_data_dict(**kwargs)

    kwargs = \
        {"ml_data_dict": ml_data_dict, "target_q_pt": target_q_pt}
    q_pt_of_pixel_nearest_to_target_q_pt = \
        _calc_q_pt_of_pixel_nearest_to_target_q_pt(**kwargs)

    num_q_shifts = len(row_col_offset_pairs)
    num_nonnegative_q_x_shifts = round((np.sqrt(num_q_shifts)-1)/2)
    num_nonnegative_q_y_shifts = num_nonnegative_q_x_shifts

    q_shifts = tuple()

    for q_shift_idx in range(num_q_shifts):
        row_offset, col_offset = row_col_offset_pairs[q_shift_idx]

        q_x_shift = ((col_offset-num_nonnegative_q_x_shifts)*q_x_shift_step
                     + (q_pt_of_pixel_nearest_to_target_q_pt-target_q_pt)[0])
        q_y_shift = ((row_offset-num_nonnegative_q_y_shifts)*q_y_shift_step
                     + (q_pt_of_pixel_nearest_to_target_q_pt-target_q_pt)[1])
        
        q_shift = np.array((q_x_shift, q_y_shift))
        q_shifts += (q_shift,)

    return q_shifts



def _calc_q_pt_of_pixel_nearest_to_target_q_pt(ml_data_dict, target_q_pt):
    cbed_pattern_images = ml_data_dict["cbed_pattern_images"]
    sampling_grid_dims_in_pixels = cbed_pattern_images.shape[-2:]

    h_scale = 1/sampling_grid_dims_in_pixels[0]
    v_scale = -1/sampling_grid_dims_in_pixels[1]

    h_offset = 0.5*h_scale
    v_offset = 1+0.5*v_scale

    q_x_coord_of_pixel_nearest_to_target_q_pt = \
        round((target_q_pt[0]-h_offset)/h_scale)*h_scale + h_offset
    q_y_coord_of_pixel_nearest_to_target_q_pt = \
        round((target_q_pt[1]-v_offset)/v_scale)*v_scale + v_offset

    q_pt_of_pixel_nearest_to_target_q_pt = \
        np.array((q_x_coord_of_pixel_nearest_to_target_q_pt,
                  q_y_coord_of_pixel_nearest_to_target_q_pt))

    return q_pt_of_pixel_nearest_to_target_q_pt



def _select_q_shift_corresponding_to_max_rgm_metric(
        bin_coords,
        common_undistorted_disk_radius,
        intensity_profiles,
        q_shifts):
    q_xy_offset = bin_coords[0]
    q_xy_scale = bin_coords[1]-bin_coords[0]

    min_rgm_ref_disk_radius = 0.5*common_undistorted_disk_radius
    max_rgm_ref_disk_radius = 1.5*common_undistorted_disk_radius

    min_q_xy_idx_1 = int(np.floor((min_rgm_ref_disk_radius-q_xy_offset)
                                  / q_xy_scale))
    max_q_xy_idx_1 = int(np.ceil((max_rgm_ref_disk_radius-q_xy_offset)
                                 / q_xy_scale))

    rgm_metric = -float("inf")
    q_shift_idx = 0

    for q_xy_idx_1 in range(min_q_xy_idx_1, max_q_xy_idx_1):
        rgm_ref_disk_radius = q_xy_offset + q_xy_scale*q_xy_idx_1
        q_xy_idx_2 = int(np.floor((0.8*rgm_ref_disk_radius-q_xy_offset)
                                  / q_xy_scale))
        q_xy_idx_3 = int(np.ceil((1.3*rgm_ref_disk_radius-q_xy_offset)
                                 / q_xy_scale))

        candidate_rgm_metrics = \
            (intensity_profiles[:, q_xy_idx_2:q_xy_idx_1+1].sum(axis=1)
             - intensity_profiles[:, q_xy_idx_1+1:q_xy_idx_3+1].sum(axis=1))
        
        candidate_rgm_metric = candidate_rgm_metrics.max().item()
        candidate_q_shift_idx = candidate_rgm_metrics.argmax()
        max_rgm_metric_is_to_be_updated = (candidate_rgm_metric > rgm_metric)

        q_shift_idx = ((max_rgm_metric_is_to_be_updated)*candidate_q_shift_idx
                       + (not max_rgm_metric_is_to_be_updated)*q_shift_idx)
        rgm_metric = max(candidate_rgm_metric, rgm_metric)

    q_shift_corresponding_to_max_rgm_metric = q_shifts[q_shift_idx]

    return q_shift_corresponding_to_max_rgm_metric



def _identify_outliers_of_predicted_q_sample(predicted_q_sample,
                                             target_q_sample):
    euclidean_distances = torch.linalg.norm(target_q_sample-predicted_q_sample,
                                            dim=0)

    threshold = 2

    outlier_registry = \
        (torch.abs(euclidean_distances-euclidean_distances.mean())
         > threshold*euclidean_distances.std())

    return outlier_registry



def _add_flow_field_offset(distortion_model, flow_field):
    flow_field[0][:, :] -= flow_field[0].mean()
    flow_field[1][:, :] -= flow_field[1].mean()

    return None



def generate_output_filename(path_to_data_dir_1, disk_size):
    unformatted_filename = \
        ("{}/rgm_test_set_1_results"
         "/results_for_cbed_patterns_of_MoS2_on_amorphous_C_with_{}_sized_disks"
         "/rgm_testing_summary_output_data.h5")
    output_filename = \
        unformatted_filename.format(path_to_data_dir_1, disk_size)

    return output_filename



def initialize_rgm_testing_summary_output_data_file(output_filename,
                                                    ml_testing_dataset):
    kwargs = {"filename": output_filename,
              "path_in_file": "path_to_ml_testing_dataset"}
    hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

    kwargs = {"dataset": ml_testing_dataset.core_attrs["path_to_ml_dataset"],
              "dataset_id": hdf5_dataset_id,
              "write_mode": "w"}
    h5pywrappers.dataset.save(**kwargs)

    total_num_ml_testing_data_instances = len(ml_testing_dataset)

    kwargs = {"filename": output_filename,
              "path_in_file": "total_num_ml_testing_data_instances"}
    hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

    kwargs = {"dataset": np.array(total_num_ml_testing_data_instances),
              "dataset_id": hdf5_dataset_id,
              "write_mode": "a"}
    h5pywrappers.dataset.save(**kwargs)

    return None



def save_ml_data_instance_metrics(output_filename,
                                  epes_of_adjusted_distortion_fields):
    path_in_file = ("ml_data_instance_metrics"
                    "/testing/epes_of_adjusted_distortion_fields")

    kwargs = {"filename": output_filename,
              "path_in_file": path_in_file}
    hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

    kwargs = {"dataset": epes_of_adjusted_distortion_fields,
              "dataset_id": hdf5_dataset_id,
              "write_mode": "a"}
    h5pywrappers.dataset.save(**kwargs)

    kwargs = {"obj_id": hdf5_dataset_id, "attr_name": "dim_0"}
    attr_id = h5pywrappers.attr.ID(**kwargs)

    attr = "ml testing data instance idx"
    kwargs = {"attr": attr, "attr_id": attr_id, "write_mode": "a"}
    h5pywrappers.attr.save(**kwargs)

    return None



###########################
## Define error messages ##
###########################



#########################
## Main body of script ##
#########################

# Parse the command line arguments.
parser = argparse.ArgumentParser()
argument_names = ("disk_size", "data_dir_1")
for argument_name in argument_names:
    parser.add_argument("--"+argument_name)
args = parser.parse_args()
disk_size = args.disk_size
path_to_data_dir_1 = args.data_dir_1



# Select the ``emicroml`` submodule that is appropriate to the specified ML
# model task.
ml_model_task_module = emicroml.modelling.cbed.distortion.estimation



# Set a RNG seed for reproducibility.
rng_seed = 4321

torch.manual_seed(seed=rng_seed)
torch.cuda.manual_seed_all(seed=rng_seed)
random.seed(a=rng_seed)
np.random.seed(seed=rng_seed)

torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False



# Specify by name the device to use for PyTorch operations.
device_name = None



# Load ML dataset.
sample_name = "MoS2_on_amorphous_C"

unformatted_path = (path_to_data_dir_1
                    + "/ml_datasets"
                    + "/ml_datasets_for_ml_model_test_set_1"
                    + "/ml_datasets_with_cbed_patterns_of_{}"
                    + "/ml_dataset_with_{}_sized_disks.h5")
path_to_ml_dataset = unformatted_path.format(sample_name, disk_size)

kwargs = {"path_to_ml_dataset": path_to_ml_dataset,
          "entire_ml_dataset_is_to_be_cached": True,
          "ml_data_values_are_to_be_checked": True,
          "max_num_ml_data_instances_per_chunk": 32}
ml_testing_dataset = ml_model_task_module.MLDataset(**kwargs)



# Initialize the summary output data file.
output_filename = generate_output_filename(path_to_data_dir_1, disk_size)

initialize_rgm_testing_summary_output_data_file(output_filename,
                                                ml_testing_dataset)



# Process all the ML testing data instances of the ML testing dataset.
start_time_1 = time.time()

unformatted_msg = ("Testing the radial gradient maximization (RGM) approach "
                   "to the distortion estimation of convergent beam electron "
                   "diffraction (CBED) patterns using the ML dataset "
                   "stored in the file ``'{}'``...\n\n\n")
msg = unformatted_msg.format(path_to_ml_dataset)
print(msg)

total_num_ml_testing_data_instances = len(ml_testing_dataset)

epes_of_adjusted_distortion_fields = tuple()

for ml_testing_data_instance_idx in range(total_num_ml_testing_data_instances):
    start_time_2 = time.time()

    single_dim_slice = slice(ml_testing_data_instance_idx,
                             ml_testing_data_instance_idx+1)

    kwargs = {"single_dim_slice": single_dim_slice,
              "device_name": device_name,
              "decode": True,
              "unnormalize_normalizable_elems": True}
    ml_data_dict = ml_testing_dataset.get_ml_data_instances(**kwargs)

    kwargs = \
        {"ml_data_dict": ml_data_dict}
    epe_of_adjusted_distortion_field = \
        test_rgm_approach_against_ml_data_dict(**kwargs)
    
    epes_of_adjusted_distortion_fields += (epe_of_adjusted_distortion_field,)

    elapsed_time = time.time() - start_time_2
    unformatted_msg = ("Machine learning (ML) testing data instance #{} has "
                       "been processed; End-point error = {}; "
                       "Processing time for ML data instance = {} s.")
    msg = unformatted_msg.format(ml_testing_data_instance_idx,
                                 epe_of_adjusted_distortion_field,
                                 elapsed_time)
    print(msg)

save_ml_data_instance_metrics(output_filename,
                              epes_of_adjusted_distortion_fields)

print("\n\n")

elapsed_time = time.time() - start_time_1

unformatted_msg = ("Finished testing the radial gradient maximization (RGM) "
                   "approach to the distortion estimation of convergent beam "
                   "electron diffraction (CBED) patterns using the ML dataset "
                   "stored in the file ``'{}'``. The testing results have been "
                   "saved to the file ``'{}'``. Time taken to test "
                   "the RGM approach and to save the results: {} s.\n\n\n")
msg = unformatted_msg.format(path_to_ml_dataset,
                             output_filename,
                             elapsed_time)
print(msg)
