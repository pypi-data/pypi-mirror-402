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
:mod:`emicroml.modelling`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For timing the execution of different segments of code.
import time

# For performing deep copies.
import copy

# For creating path objects, checking whether certain directories exists, and
# making directories.
import pathlib

# For checking for instances of the class ``collections.OrderedDict``.
import collections

# For deserializing JSON documents.
import json

# For setting Python's seed.
import random



# For general array handling.
import numpy as np

# For validating and converting objects, and determining fully qualified class
# names of objects.
import czekitout.check
import czekitout.convert
import czekitout.name

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes

# For validating objects intended to be used as seeds to random number
# generators.
import fakecbed

# For loading objects from and saving objects to HDF5 files.
import h5py
import h5pywrappers

# For building neural network models.
import torch



# For validating, pre-serializing, and de-pre-serializing instances of the
# class :class:`emicroml.modelling.lr.LRSchedulerManager`.
import emicroml.modelling.lr



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = []



default_num_ml_data_instances = 1



def _check_and_convert_num_ml_data_instances(params):
    obj_name = "num_ml_data_instances"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    num_ml_data_instances = czekitout.convert.to_positive_int(**kwargs)

    return num_ml_data_instances



class _UnnormalizedMLDataInstanceGenerator():
    def __init__(self, cached_ml_data_instances):
        self._cached_ml_data_instances = cached_ml_data_instances

        return None



    def _generate(self, num_ml_data_instances=default_num_ml_data_instances):
        params = {"num_ml_data_instances": num_ml_data_instances}
        num_ml_data_instances = _check_and_convert_num_ml_data_instances(params)

        ml_data_dict_1 = dict()

        method_name = ("_generate_ml_data_dict"
                       "_containing_only_one_ml_data_instance")
        method_alias = getattr(self, method_name)
        ml_data_dict_2 = method_alias()

        for key, ml_data_dict_2_elem in ml_data_dict_2.items():
            ml_data_dict_2_elem = np.array(ml_data_dict_2_elem)
                
            empty_array_shape = ((num_ml_data_instances,)
                                 + ml_data_dict_2_elem.shape[1:])
                
            kwargs = {"shape": empty_array_shape,
                      "dtype": ml_data_dict_2_elem.dtype}
            empty_array = np.empty(**kwargs)

            ml_data_dict_1[key] = (ml_data_dict_2_elem
                                   if (ml_data_dict_2_elem.tolist() is None)
                                   else empty_array)
        
        for ml_data_instance_idx in range(num_ml_data_instances):
            ml_data_dict_2 = (method_alias()
                              if (ml_data_instance_idx > 0)
                              else ml_data_dict_2)
            
            for key, ml_data_dict_2_elem in ml_data_dict_2.items():
                ml_data_dict_1_elem = ml_data_dict_1[key]

                single_dim_slice = (tuple()
                                    if (ml_data_dict_1_elem.tolist() is None)
                                    else (ml_data_instance_idx,))
                
                ml_data_dict_1_elem[single_dim_slice] = \
                    (ml_data_dict_1_elem[single_dim_slice]
                     if (ml_data_dict_1_elem.tolist() is None)
                     else ml_data_dict_2_elem[0])

        for key in ml_data_dict_1:
            ml_data_dict_1[key] = (None
                                   if (ml_data_dict_1[key].tolist() is None)
                                   else ml_data_dict_1[key])

        ml_data_instances = ml_data_dict_1
        
        return ml_data_instances



    def _generate_ml_data_dict_containing_only_one_ml_data_instance(self):
        ml_data_dict = dict()

        return ml_data_dict



def _load_contiguous_data_chunk(chunk_idx,
                                max_num_ml_data_instances_per_chunk,
                                input_hdf5_dataset):
    num_ml_data_instances_in_input_ml_dataset = input_hdf5_dataset.shape[0]

    start = chunk_idx*max_num_ml_data_instances_per_chunk
    stop_candidate_1 = num_ml_data_instances_in_input_ml_dataset
    stop_candidate_2 = start + max_num_ml_data_instances_per_chunk
    stop = min(stop_candidate_1, stop_candidate_2)
    single_dim_slice = slice(start, stop)
    data_chunk = input_hdf5_dataset[single_dim_slice]

    return data_chunk



def _save_data_chunk(starting_idx_offset,
                     chunk_idx,
                     max_num_ml_data_instances_per_chunk,
                     data_chunk,
                     output_hdf5_dataset):
    start = starting_idx_offset + chunk_idx*max_num_ml_data_instances_per_chunk
    stop = start + data_chunk.shape[0]
    single_dim_slice = slice(start, stop)
    output_hdf5_dataset[single_dim_slice] = data_chunk
    
    return None



def _save_normalization_weight_and_bias(hdf5_dataset_path,
                                        output_ml_dataset_filename,
                                        normalization_weight,
                                        normalization_bias):
    kwargs = {"filename": output_ml_dataset_filename,
              "path_in_file": hdf5_dataset_path}
    hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

    attr_names = ("normalization_weight", "normalization_bias")
    attrs = (normalization_weight, normalization_bias)
    for attr_name, attr in zip(attr_names, attrs):
        kwargs = {"obj_id": hdf5_dataset_id, "attr_name": attr_name}
        attr_id = h5pywrappers.attr.ID(**kwargs)
        h5pywrappers.attr.save(attr, attr_id, write_mode="a")

    return None



_tol_for_comparing_floats = 10*np.finfo(np.float32).eps



class _MLDataNormalizer():
    def __init__(self,
                 keys_of_unnormalizable_ml_data_dict_elems,
                 keys_of_normalizable_ml_data_dict_elems,
                 ml_data_dict_elem_decoders,
                 overriding_normalization_weights_and_biases,
                 max_num_ml_data_instances_per_file_update):
        self._keys_of_unnormalizable_ml_data_dict_elems = \
            keys_of_unnormalizable_ml_data_dict_elems
        self._keys_of_normalizable_ml_data_dict_elems = \
            keys_of_normalizable_ml_data_dict_elems
        self._ml_data_dict_elem_decoders = \
            ml_data_dict_elem_decoders
        self._overriding_normalization_weights_and_biases = \
            overriding_normalization_weights_and_biases
        self._max_num_ml_data_instances_per_file_update = \
            max_num_ml_data_instances_per_file_update

        self._ml_data_dict_keys = (keys_of_unnormalizable_ml_data_dict_elems
                                   + keys_of_normalizable_ml_data_dict_elems)

        self._initialize_extrema_cache()
        self._update_normalization_weights_and_biases()

        return None



    def _update_extrema_cache(self, ml_data_dict):
        for key in self._extrema_cache:
            ml_data_dict_elem_decoders = self._ml_data_dict_elem_decoders
            ml_data_dict_item_decoder = ml_data_dict_elem_decoders.get(key,
                                                                       None)
            ml_data_dict_elem = (ml_data_dict[key]
                                 if (key in ml_data_dict)
                                 else ml_data_dict_elem_decoder(ml_data_dict))

            min_candidate_1 = np.min(ml_data_dict_elem).item()
            min_candidate_2 = self._extrema_cache[key]["min"]
            self._extrema_cache[key]["min"] = min(min_candidate_1,
                                                  min_candidate_2)

            max_candidate_1 = np.max(ml_data_dict_elem).item()
            max_candidate_2 = self._extrema_cache[key]["max"]
            self._extrema_cache[key]["max"] = max(max_candidate_1,
                                                  max_candidate_2)

        self._update_normalization_weights_and_biases()

        return None



    def _initialize_extrema_cache(self):
        self._extrema_cache = dict()
        for key in self._keys_of_normalizable_ml_data_dict_elems:
            self._extrema_cache[key] = {"min": float("inf"),
                                        "max": -float("inf")}

        return None



    def _update_normalization_weights_and_biases(self):
        self._normalization_weights = dict()
        self._normalization_biases = dict()

        for key in self._extrema_cache:
            overriding_normalization_weight_and_bias = \
                self._overriding_normalization_weights_and_biases.get(key, None)

            maximum_cache = self._extrema_cache[key]["max"]
            minimum_cache = self._extrema_cache[key]["min"]
            cache_range = (0.0
                           if np.isnan(abs(maximum_cache-minimum_cache))
                           else abs(maximum_cache-minimum_cache))

            tol = _tol_for_comparing_floats

            normalization_weight_candidate = \
                (((cache_range > tol)
                  / (cache_range
                     + (cache_range <= tol)))
                 + (((cache_range <= tol)
                     * (abs(minimum_cache) > tol))
                    / (minimum_cache
                       + (abs(minimum_cache) <= tol))))

            normalization_bias_candidate = \
                -((((cache_range > tol)
                    * normalization_weight_candidate)
                   + ((cache_range <= tol)
                      * (abs(minimum_cache) <= tol)))
                  * (minimum_cache, 1)[minimum_cache == float("inf")])

            self._normalization_weights[key] = \
                (normalization_weight_candidate
                 if (overriding_normalization_weight_and_bias is None)
                 else overriding_normalization_weight_and_bias["weight"])
            self._normalization_biases[key] = \
                (normalization_bias_candidate
                 if (overriding_normalization_weight_and_bias is None)
                 else overriding_normalization_weight_and_bias["bias"])

        return None



    def _normalize_ml_dataset_file(self, path_to_ml_dataset):
        msg = ("\n\nNormalizing, where applicable, data in the file storing "
               "the machine learning dataset...\n")
        print(msg)

        for key in self._normalization_weights:
            normalization_weight = self._normalization_weights[key]
            normalization_bias = self._normalization_biases[key]
            hdf5_dataset_path = key

            kwargs = {"filename": path_to_ml_dataset,
                      "path_in_file": hdf5_dataset_path}
            hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

            kwargs = {"dataset_id": hdf5_dataset_id, "read_only": False}
            hdf5_dataset = (h5pywrappers.dataset.load(**kwargs)
                            if (key not in self._ml_data_dict_elem_decoders)
                            else np.zeros((0,)))

            total_num_ml_data_instances = hdf5_dataset.shape[0]

            max_num_ml_data_instances_per_chunk = \
                (self._max_num_ml_data_instances_per_file_update
                 if (self._max_num_ml_data_instances_per_file_update < np.inf)
                 else total_num_ml_data_instances)
            
            fraction = (total_num_ml_data_instances
                        / max_num_ml_data_instances_per_chunk)
            num_chunks = np.ceil(fraction).astype(int)

            for chunk_idx in range(num_chunks):
                self._normalize_data_chunk(chunk_idx,
                                           max_num_ml_data_instances_per_chunk,
                                           hdf5_dataset,
                                           normalization_weight,
                                           normalization_bias)

            _ = (hdf5_dataset.file.close()
                 if (key not in self._ml_data_dict_elem_decoders)
                 else None)

            self._save_normalization_weight_and_bias(hdf5_dataset_path,
                                                     path_to_ml_dataset)

        msg = ("Finished normalizing data in the file storing the machine "
               "learning dataset.\n")
        print(msg)

        return None



    def _normalize_data_chunk(self,
                              chunk_idx,
                              max_num_ml_data_instances_per_chunk,
                              hdf5_dataset,
                              normalization_weight,
                              normalization_bias):
        kwargs = {"chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  max_num_ml_data_instances_per_chunk,
                  "input_hdf5_dataset": hdf5_dataset}
        data_chunk = _load_contiguous_data_chunk(**kwargs)

        normalized_data_chunk = (data_chunk*normalization_weight
                                 + normalization_bias).clip(min=0, max=1)

        kwargs = {"starting_idx_offset": \
                  0,
                  "chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  max_num_ml_data_instances_per_chunk,
                  "data_chunk": \
                  normalized_data_chunk,
                  "output_hdf5_dataset": \
                  hdf5_dataset}
        _save_data_chunk(**kwargs)

        return None



    def _save_normalization_weight_and_bias(self,
                                            hdf5_dataset_path,
                                            path_to_ml_dataset):
        key = hdf5_dataset_path
        normalization_weight = self._normalization_weights[hdf5_dataset_path]
        normalization_bias = self._normalization_biases[hdf5_dataset_path]
        output_ml_dataset_filename = path_to_ml_dataset

        _save_normalization_weight_and_bias(hdf5_dataset_path,
                                            output_ml_dataset_filename,
                                            normalization_weight,
                                            normalization_bias)

        return None



class _MLDataTypeValidator():
    def __init__(self, ml_data_dict_key_to_dtype_map):
        self._ml_data_dict_key_to_dtype_map = ml_data_dict_key_to_dtype_map

        return None



    def _check_dtypes_of_hdf5_datasets_of_ml_dataset_files(
            self, paths_to_ml_datasets):
        for path_to_ml_dataset in paths_to_ml_datasets:
            kwargs = {"path_to_ml_dataset": path_to_ml_dataset}
            self._check_dtypes_of_hdf5_datasets_of_ml_dataset_file(**kwargs)

        return None



    def _check_dtypes_of_hdf5_datasets_of_ml_dataset_file(self,
                                                          path_to_ml_dataset):
        for key in self._ml_data_dict_key_to_dtype_map:
            hdf5_dataset_path = key
            kwargs = {"hdf5_dataset_path": hdf5_dataset_path,
                      "path_to_ml_dataset": path_to_ml_dataset}
            self._check_dtype_of_hdf5_dataset_of_ml_dataset_file(**kwargs)

        return None



    def _check_dtype_of_hdf5_dataset_of_ml_dataset_file(self,
                                                        hdf5_dataset_path,
                                                        path_to_ml_dataset):
        kwargs = {"filename": path_to_ml_dataset,
                  "path_in_file": hdf5_dataset_path}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": hdf5_dataset_id, "read_only": True}
        hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

        data_chunk = (hdf5_dataset
                      if (hdf5_dataset.shape is None)
                      else hdf5_dataset[tuple(0 for _ in hdf5_dataset.shape)])

        kwargs = {"data_chunk": \
                  data_chunk,
                  "key_used_to_get_data_chunk": \
                  hdf5_dataset_path,
                  "name_of_obj_alias_from_which_data_chunk_was_obtained": \
                  "hdf5_dataset",
                  "obj_alias_from_which_data_chunk_was_obtained": \
                  hdf5_dataset}
        self._check_dtype_of_data_chunk(**kwargs)

        hdf5_dataset.file.close()

        return None



    def _check_dtype_of_data_chunk(
            self,
            data_chunk,
            key_used_to_get_data_chunk,
            name_of_obj_alias_from_which_data_chunk_was_obtained,
            obj_alias_from_which_data_chunk_was_obtained):
        map_alias = self._ml_data_dict_key_to_dtype_map
        key = key_used_to_get_data_chunk

        temp_numpy_array_1 = np.empty(tuple(), dtype=map_alias[key])
        temp_tensor_1 = torch.from_numpy(temp_numpy_array_1)
        
        expected_dtype = (temp_tensor_1.dtype
                          if isinstance(data_chunk, torch.Tensor)
                          else map_alias[key])

        temp_tensor_2_dtype = (data_chunk.dtype
                               if isinstance(data_chunk, torch.Tensor)
                               else None)
        temp_tensor_2 = torch.empty(tuple(),
                                    dtype=temp_tensor_2_dtype,
                                    device="cpu")
        temp_numpy_array_2 = (temp_tensor_2.numpy()
                              if isinstance(data_chunk, torch.Tensor)
                              else data_chunk)

        kwargs = {"arg1": temp_numpy_array_2.dtype,
                  "arg2": temp_numpy_array_1.dtype}
        dtype_of_data_chunk_is_invalid = not np.issubdtype(**kwargs)

        if dtype_of_data_chunk_is_invalid:
            kwargs = {"expected_dtype": \
                      expected_dtype,
                      "obj_alias_from_which_data_chunk_was_obtained": \
                      obj_alias_from_which_data_chunk_was_obtained,
                      "key_used_to_get_data_chunk": \
                      key_used_to_get_data_chunk,
                      "name_of_obj_alias_from_which_data_chunk_was_obtained": \
                      name_of_obj_alias_from_which_data_chunk_was_obtained}
            self._raise_error_related_to_invalid_data_chunk_dtype(**kwargs)

        return None



    def _raise_error_related_to_invalid_data_chunk_dtype(
            self,
            expected_dtype,
            obj_alias_from_which_data_chunk_was_obtained,
            key_used_to_get_data_chunk,
            name_of_obj_alias_from_which_data_chunk_was_obtained):
        name_of_expected_dtype = self._name_of_dtype(dtype=expected_dtype)
        obj_alias = obj_alias_from_which_data_chunk_was_obtained
        key = key_used_to_get_data_chunk

        unformatted_err_msg = (_ml_data_type_validator_err_msg_1
                               if isinstance(obj_alias, h5py.Dataset)
                               else _ml_data_type_validator_err_msg_2)

        format_arg_0 = \
            (key
             if isinstance(obj_alias, h5py.Dataset)
             else name_of_obj_alias_from_which_data_chunk_was_obtained)
        format_arg_1 = \
            (obj_alias.file.filename
             if isinstance(obj_alias, h5py.Dataset)
             else key)
        format_arg_2 = \
            name_of_expected_dtype

        args = (format_arg_0, format_arg_1, format_arg_2)
        err_msg = unformatted_err_msg.format(*args)

        _ = (obj_alias.file.close()
             if isinstance(obj_alias, h5py.Dataset)
             else None)
        
        raise TypeError(err_msg)

        return None



    def _name_of_dtype(self, dtype):
        name = str(dtype).removeprefix("<class '").removesuffix("'>")

        return name



class _MLDataValueValidator():
    def __init__(self,
                 ml_data_dict_key_to_unnormalized_value_limits_map,
                 ml_data_dict_key_to_custom_value_checker_map,
                 ml_data_normalizer):
        self._ml_data_dict_key_to_unnormalized_value_limits_map = \
            ml_data_dict_key_to_unnormalized_value_limits_map
        self._ml_data_dict_key_to_custom_value_checker_map = \
            ml_data_dict_key_to_custom_value_checker_map
        self._keys_of_normalizable_ml_data_dict_elems = \
            ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        return None



    def _check_values_of_hdf5_datasets_of_ml_dataset_file(
            self,
            path_to_ml_dataset,
            max_num_ml_data_instances_per_chunk):
        for key in self._ml_data_dict_key_to_unnormalized_value_limits_map:
            hdf5_dataset_path = key
            kwargs = {"hdf5_dataset_path": \
                      hdf5_dataset_path,
                      "path_to_ml_dataset": \
                      path_to_ml_dataset,
                      "max_num_ml_data_instances_per_chunk": \
                      max_num_ml_data_instances_per_chunk}
            self._check_values_of_hdf5_dataset_of_ml_dataset_file(**kwargs)

        return None



    def _check_values_of_hdf5_dataset_of_ml_dataset_file(
            self,
            hdf5_dataset_path,
            path_to_ml_dataset,
            max_num_ml_data_instances_per_chunk):
        kwargs = {"filename": path_to_ml_dataset,
                  "path_in_file": hdf5_dataset_path}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": hdf5_dataset_id, "read_only": True}
        hdf5_dataset = h5pywrappers.dataset.load(**kwargs)
        hdf5_dataset_shape = hdf5_dataset.shape

        modified_hdf5_dataset_shape = (hdf5_dataset_shape
                                       if (hdf5_dataset_shape is not None)
                                       else (0,))

        total_num_ml_data_instances = modified_hdf5_dataset_shape[0]
        fraction = (total_num_ml_data_instances
                    / max_num_ml_data_instances_per_chunk)
        num_chunks = np.ceil(fraction).astype(int)

        for chunk_idx in range(num_chunks):
            kwargs = {"chunk_idx": \
                      chunk_idx,
                      "max_num_ml_data_instances_per_chunk": \
                      max_num_ml_data_instances_per_chunk,
                      "input_hdf5_dataset": hdf5_dataset}
            data_chunk = _load_contiguous_data_chunk(**kwargs)
            hdf5_datasubset = data_chunk

            method_alias = \
                self._check_values_of_hdf5_datasubset_of_ml_dataset_file
            _ = \
                method_alias(hdf5_dataset, hdf5_datasubset)

        hdf5_dataset.file.close()

        return None



    def _check_values_of_hdf5_datasubset_of_ml_dataset_file(self,
                                                            hdf5_dataset,
                                                            hdf5_datasubset):
        kwargs = {"data_chunk_is_expected_to_be_normalized_if_normalizable": \
                  True,
                  "key_used_to_get_data_chunk": \
                  hdf5_dataset.name[1:],
                  "data_chunk": \
                  hdf5_datasubset,
                  "name_of_obj_alias_from_which_data_chunk_was_obtained": \
                  "hdf5_dataset",
                  "obj_alias_from_which_data_chunk_was_obtained": \
                  hdf5_dataset}
        self._check_values_of_data_chunk(**kwargs)

        return None



    def _check_values_of_data_chunk(
            self,
            data_chunk_is_expected_to_be_normalized_if_normalizable,
            key_used_to_get_data_chunk,
            data_chunk,
            name_of_obj_alias_from_which_data_chunk_was_obtained,
            obj_alias_from_which_data_chunk_was_obtained):
        kwargs = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        
        key = key_used_to_get_data_chunk
        if key in self._ml_data_dict_key_to_custom_value_checker_map:
            self._ml_data_dict_key_to_custom_value_checker_map[key](**kwargs)
        else:
            self._default_value_checker(**kwargs)

        return None



    def _default_value_checker(
            self,
            data_chunk_is_expected_to_be_normalized_if_normalizable,
            key_used_to_get_data_chunk,
            data_chunk,
            name_of_obj_alias_from_which_data_chunk_was_obtained,
            obj_alias_from_which_data_chunk_was_obtained):
        key = \
            key_used_to_get_data_chunk
        data_chunk_is_normalizable = \
            (key in self._keys_of_normalizable_ml_data_dict_elems)
        data_chunk_is_expected_to_be_normalized = \
            (data_chunk_is_normalizable
             and data_chunk_is_expected_to_be_normalized_if_normalizable)

        if data_chunk_is_expected_to_be_normalized:
            lower_value_limit = 0
            upper_value_limit = 1
        else:
            map_alias = self._ml_data_dict_key_to_unnormalized_value_limits_map
            value_limits = map_alias[key]
            lower_value_limit = value_limits[0]
            upper_value_limit = value_limits[1]

        tol = _tol_for_comparing_floats
        if ((data_chunk.min().item()+tol < lower_value_limit)
            or (upper_value_limit < data_chunk.max().item()-tol)):
            kwargs = {"obj_alias_from_which_data_chunk_was_obtained": \
                      obj_alias_from_which_data_chunk_was_obtained,
                      "key_used_to_get_data_chunk": \
                      key_used_to_get_data_chunk,
                      "name_of_obj_alias_from_which_data_chunk_was_obtained": \
                      name_of_obj_alias_from_which_data_chunk_was_obtained,
                      "lower_value_limit": \
                      lower_value_limit,
                      "upper_value_limit": \
                      upper_value_limit}
            self._raise_error_related_to_invalid_data_value(**kwargs)

        return None



    def _raise_error_related_to_invalid_data_value(
            self,
            obj_alias_from_which_data_chunk_was_obtained,
            key_used_to_get_data_chunk,
            name_of_obj_alias_from_which_data_chunk_was_obtained,
            lower_value_limit,
            upper_value_limit):
        obj_alias = obj_alias_from_which_data_chunk_was_obtained
        key = key_used_to_get_data_chunk

        unformatted_err_msg = (_ml_data_value_validator_err_msg_1
                               if isinstance(obj_alias, h5py.Dataset)
                               else _ml_data_value_validator_err_msg_2)

        format_arg_0 = \
            (key
             if isinstance(obj_alias, h5py.Dataset)
             else name_of_obj_alias_from_which_data_chunk_was_obtained)
        format_arg_1 = \
            (obj_alias.file.filename
             if isinstance(obj_alias, h5py.Dataset)
             else key)
        format_arg_2 = \
            lower_value_limit
        format_arg_3 = \
            upper_value_limit

        args = (format_arg_0, format_arg_1, format_arg_2, format_arg_3)
        err_msg = unformatted_err_msg.format(*args)

        _ = (obj_alias.file.close()
             if isinstance(obj_alias, h5py.Dataset)
             else None)
        
        raise ValueError(err_msg)

        return None                                



class _MLDataNormalizationWeightsAndBiasesLoader():
    def __init__(self, ml_data_normalizer, ml_data_value_validator):
        self._ml_data_normalizer = ml_data_normalizer
        self._ml_data_value_validator = ml_data_value_validator

        obj_alias = \
            ml_data_value_validator
        self._ml_data_dict_key_to_unnormalized_hdf5_dataset_value_limits_map = \
            obj_alias._ml_data_dict_key_to_unnormalized_value_limits_map
        
        return None



    def _load(self, path_to_ml_dataset):
        unformatted_err_msg = \
            _ml_data_normalization_weights_and_biases_loader_err_msg_1
        keys_of_normalizable_ml_data_dict_elems = \
            self._ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        normalization_weights = dict()
        normalization_biases = dict()

        for key in keys_of_normalizable_ml_data_dict_elems:
            hdf5_dataset_path = key
            kwargs = {"filename": path_to_ml_dataset,
                      "path_in_file": hdf5_dataset_path}
            hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

            attr_names = ("normalization_weight", "normalization_bias")
            for attr_name in attr_names:
                kwargs = {"obj_id": hdf5_dataset_id, "attr_name": attr_name}
                attr_id = h5pywrappers.attr.ID(**kwargs)
                attr = h5pywrappers.attr.load(attr_id)

                try:
                    kwargs = {"obj": attr, "obj_name": attr_name}
                    func_alias = czekitout.convert.to_float
                    if "weight" in attr_name:
                        normalization_weight = func_alias(**kwargs)
                    else:
                        normalization_bias = func_alias(**kwargs)
                except:
                    args = (attr_name.split("_")[-1],
                            attr_name.split("_")[-1],
                            hdf5_dataset_path,
                            path_to_ml_dataset)
                    err_msg = unformatted_err_msg.format(*args)
                    raise TypeError(err_msg)

            self._check_normalization_weight(hdf5_dataset_path,
                                             normalization_weight,
                                             path_to_ml_dataset)
            self._check_normalization_bias(hdf5_dataset_path,
                                           normalization_bias,
                                           normalization_weight,
                                           path_to_ml_dataset)

            normalization_weights[hdf5_dataset_path] = normalization_weight
            normalization_biases[hdf5_dataset_path] = normalization_bias

        return normalization_weights, normalization_biases



    def _check_normalization_weight(self,
                                    hdf5_dataset_path,
                                    normalization_weight,
                                    path_to_ml_dataset):
        method_alias = \
            self._calc_lowest_valid_normalization_weight_lower_limit
        lowest_valid_normalization_weight_lower_limit = \
            method_alias(hdf5_dataset_path)

        ml_data_normalizer = \
            self._ml_data_normalizer
        overriding_normalization_weights_and_biases = \
            ml_data_normalizer._overriding_normalization_weights_and_biases
        
        map_alias = overriding_normalization_weights_and_biases
        key = hdf5_dataset_path        

        unformatted_err_msg = \
            (_ml_data_normalization_weights_and_biases_loader_err_msg_2
             if (path_to_ml_dataset is None)
             else _ml_data_normalization_weights_and_biases_loader_err_msg_3)
        format_args = \
            (("weights", hdf5_dataset_path)
             if (path_to_ml_dataset is None)
             else ("weight", "weight", hdf5_dataset_path, path_to_ml_dataset))
        format_args += \
            ((key not in map_alias)*"finite, and greater than or " + "equal to",
             lowest_valid_normalization_weight_lower_limit)

        diff = (normalization_weight
                - lowest_valid_normalization_weight_lower_limit)
        tol = _tol_for_comparing_floats
        
        normalization_weight_is_invalid = \
            ((abs(diff) > tol)
             if (key in map_alias)
             else ((diff < 0) or (normalization_weight == np.inf)))

        if normalization_weight_is_invalid:
            args = format_args
            err_msg = unformatted_err_msg.format(*args)
            raise ValueError(err_msg)

        return None



    def _calc_lowest_valid_normalization_weight_lower_limit(self,
                                                            hdf5_dataset_path):
        ml_data_normalizer = \
            self._ml_data_normalizer
        overriding_normalization_weights_and_biases = \
            ml_data_normalizer._overriding_normalization_weights_and_biases

        map_alias_1 = \
            self._ml_data_dict_key_to_unnormalized_hdf5_dataset_value_limits_map
        map_alias_2 = \
            overriding_normalization_weights_and_biases
        
        key = hdf5_dataset_path
        unnormalized_hdf5_dataset_value_limits = map_alias_1.get(key,
                                                                 (None, None))

        lower_unnormalized_hdf5_dataset_value_limit = \
            unnormalized_hdf5_dataset_value_limits[0]
        upper_unnormalized_hdf5_dataset_value_limit = \
            unnormalized_hdf5_dataset_value_limits[1]

        float_alias_1 = lower_unnormalized_hdf5_dataset_value_limit
        float_alias_2 = upper_unnormalized_hdf5_dataset_value_limit

        lowest_valid_normalization_weight_lower_limit = \
            ((float_alias_2-float_alias_1)**(-1)
             if (key not in map_alias_2)
             else map_alias_2[key]["weight"])

        return lowest_valid_normalization_weight_lower_limit



    def _check_normalization_bias(self,
                                  hdf5_dataset_path,
                                  normalization_bias,
                                  normalization_weight,
                                  path_to_ml_dataset):
        method_alias = \
            self._calc_highest_valid_normalization_bias_upper_limit
        highest_valid_normalization_bias_upper_limit = \
            method_alias(hdf5_dataset_path, normalization_weight)

        ml_data_normalizer = \
            self._ml_data_normalizer
        overriding_normalization_weights_and_biases = \
            ml_data_normalizer._overriding_normalization_weights_and_biases
        
        map_alias = overriding_normalization_weights_and_biases
        key = hdf5_dataset_path        

        unformatted_err_msg = \
            (_ml_data_normalization_weights_and_biases_loader_err_msg_2
             if (path_to_ml_dataset is None)
             else _ml_data_normalization_weights_and_biases_loader_err_msg_3)
        format_args = \
            (("biases", hdf5_dataset_path)
             if (path_to_ml_dataset is None)
             else ("bias", "bias", hdf5_dataset_path, path_to_ml_dataset))
        format_args += \
            ((key not in map_alias)*"finite, and lesser than or " + "equal to",
             highest_valid_normalization_bias_upper_limit)

        diff = (normalization_bias
                - highest_valid_normalization_bias_upper_limit)
        tol = _tol_for_comparing_floats
        
        normalization_bias_is_invalid = \
            ((abs(diff) > tol)
             if (key in map_alias)
             else ((diff > 0) or (normalization_bias == -np.inf)))

        if normalization_bias_is_invalid:
            args = format_args
            err_msg = unformatted_err_msg.format(*args)
            raise ValueError(err_msg)
        
        return None



    def _calc_highest_valid_normalization_bias_upper_limit(
            self, hdf5_dataset_path, normalization_weight):
        ml_data_normalizer = \
            self._ml_data_normalizer
        overriding_normalization_weights_and_biases = \
            ml_data_normalizer._overriding_normalization_weights_and_biases

        map_alias_1 = \
            self._ml_data_dict_key_to_unnormalized_hdf5_dataset_value_limits_map
        map_alias_2 = \
            overriding_normalization_weights_and_biases
        
        key = hdf5_dataset_path
        unnormalized_hdf5_dataset_value_limits = map_alias_1.get(key,
                                                                 (None, None))

        lower_unnormalized_hdf5_dataset_value_limit = \
            unnormalized_hdf5_dataset_value_limits[0]

        highest_valid_normalization_bias_upper_limit = \
            (-normalization_weight*lower_unnormalized_hdf5_dataset_value_limit
             if (key not in map_alias_2)
             else map_alias_2[key]["bias"])

        return highest_valid_normalization_bias_upper_limit



_default_normalization_weights = None



def _check_and_convert_normalization_weights(params):
    obj_name = "normalization_weights"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_normalization_weights"

    if obj is None:
        normalization_weights = params["default_normalization_weights"]
    else:
        try:
            kwargs = {"obj": obj, "obj_name": obj_name}
            normalization_weights = czekitout.convert.to_dict(**kwargs)
        except:
            kwargs["accepted_types"] = (dict, type(None))
            czekitout.check.if_instance_of_any_accepted_types(**kwargs)

        ml_data_normalization_weights_and_biases_loader = \
            params["ml_data_normalization_weights_and_biases_loader"]
        ml_data_normalizer = \
            ml_data_normalization_weights_and_biases_loader._ml_data_normalizer
        keys_of_normalizable_ml_data_dict_elems = \
            ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems
    
        for key in keys_of_normalizable_ml_data_dict_elems:
            if key not in normalization_weights:
                unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
                err_msg = unformatted_err_msg.format("normalization_weights",
                                                     key)
                raise KeyError(err_msg)

            obj = normalization_weights[key]
            obj_name = "normalization_weights['{}']".format(key)
            kwargs = {"obj": obj, "obj_name": obj_name}
            normalization_weight = czekitout.convert.to_float(**kwargs)

            obj_alias = ml_data_normalization_weights_and_biases_loader
            method_alias = obj_alias._check_normalization_weight
            kwargs = {"hdf5_dataset_path": key,
                      "normalization_weight": normalization_weight,
                      "path_to_ml_dataset": None}
            method_alias(**kwargs)

            normalization_weights[key] = normalization_weight

    return normalization_weights



_default_normalization_biases = None



def _check_and_convert_normalization_biases(params):
    normalization_weights = _check_and_convert_normalization_weights(params)

    obj_name = "normalization_biases"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_normalization_biases"

    if obj is None:
        normalization_biases = params["default_normalization_biases"]
    else:
        try:
            kwargs = {"obj": obj, "obj_name": obj_name}
            normalization_biases = czekitout.convert.to_dict(**kwargs)
        except:
            kwargs["accepted_types"] = (dict, type(None))
            czekitout.check.if_instance_of_any_accepted_types(**kwargs)

        ml_data_normalization_weights_and_biases_loader = \
            params["ml_data_normalization_weights_and_biases_loader"]
        ml_data_normalizer = \
            ml_data_normalization_weights_and_biases_loader._ml_data_normalizer
        keys_of_normalizable_ml_data_dict_elems = \
            ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        for key in keys_of_normalizable_ml_data_dict_elems:
            if key not in normalization_biases:
                unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
                err_msg = unformatted_err_msg.format("normalization_biases",
                                                     key)
                raise KeyError(err_msg)

            obj = normalization_biases[key]
            obj_name = "normalization_biases['{}']".format(key)
            kwargs = {"obj": obj, "obj_name": obj_name}
            normalization_bias = czekitout.convert.to_float(**kwargs)

            normalization_weight = normalization_weights[key]

            obj_alias = ml_data_normalization_weights_and_biases_loader
            method_alias = obj_alias._check_normalization_bias
            kwargs = {"hdf5_dataset_path": key,
                      "normalization_bias": normalization_bias,
                      "normalization_weight": normalization_weight,
                      "path_to_ml_dataset": None}
            method_alias(**kwargs)

            normalization_biases[key] = normalization_bias

    return normalization_biases



def _calc_num_ml_data_instances_in_input_ml_dataset(ml_data_normalizer,
                                                    input_ml_dataset_filename):
    num_ml_data_instances_in_input_ml_dataset = 0

    for key in ml_data_normalizer._ml_data_dict_keys:
        random_hdf5_dataset_path = key

        kwargs = {"filename": input_ml_dataset_filename,
                  "path_in_file": random_hdf5_dataset_path}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": hdf5_dataset_id, "read_only": True}
        hdf5_dataset = h5pywrappers.dataset.load(**kwargs)
        hdf5_dataset_shape = hdf5_dataset.shape
        hdf5_dataset.file.close()

        num_ml_data_instances_in_input_ml_dataset = \
            (hdf5_dataset_shape[0]
             if (hdf5_dataset_shape is not None)
             else num_ml_data_instances_in_input_ml_dataset)

    return num_ml_data_instances_in_input_ml_dataset



def _save_normalization_weights_and_biases(ml_data_normalizer,
                                           normalization_weights,
                                           normalization_biases,
                                           output_ml_dataset_filename):
    for key in ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems:
        kwargs = {"hdf5_dataset_path": key,
                  "output_ml_dataset_filename": output_ml_dataset_filename,
                  "normalization_weight": normalization_weights[key],
                  "normalization_bias": normalization_biases[key]}
        _save_normalization_weight_and_bias(**kwargs)

    return None



class _MLDataRenormalizer():
    def __init__(self,
                 input_ml_dataset_filenames,
                 max_num_ml_data_instances_per_file_update,
                 ml_data_normalization_weights_and_biases_loader):
        self._input_ml_dataset_filenames = \
            input_ml_dataset_filenames
        self._ml_data_normalization_weights_and_biases_loader = \
            ml_data_normalization_weights_and_biases_loader

        ml_data_normalizer = \
            ml_data_normalization_weights_and_biases_loader._ml_data_normalizer
        ml_data_normalizer._max_num_ml_data_instances_per_file_update = \
            max_num_ml_data_instances_per_file_update
        self._ml_data_normalizer = \
            ml_data_normalizer
        self._ml_data_dict_keys = \
            ml_data_normalizer._ml_data_dict_keys

        obj_alias = ml_data_normalization_weights_and_biases_loader
        self._ml_data_value_validator = obj_alias._ml_data_value_validator

        normalization_weights_and_biases_of_output_ml_dataset = \
            self._calc_normalization_weights_and_biases_of_output_ml_dataset()
        self._output_normalization_weights = \
            normalization_weights_and_biases_of_output_ml_dataset[0]
        self._output_normalization_biases = \
            normalization_weights_and_biases_of_output_ml_dataset[1]

        renormalization_weights_and_biases_of_input_ml_datasets = \
            self._calc_renormalization_weights_and_biases_of_input_ml_datasets()
        self._renormalization_weights_of_input_ml_datasets = \
            renormalization_weights_and_biases_of_input_ml_datasets[0]
        self._renormalization_biases_of_input_ml_datasets = \
            renormalization_weights_and_biases_of_input_ml_datasets[1]
        
        self._ml_data_instance_counts_of_input_ml_datasets = \
            self._calc_ml_data_instance_counts_of_input_ml_datasets()
        self._total_num_ml_data_instances = \
            sum(self._ml_data_instance_counts_of_input_ml_datasets.values())

        self._max_num_ml_data_instances_per_chunk = \
            self._calc_max_num_ml_data_instances_per_chunk()

        return None



    def _calc_renormalization_weights_and_biases_of_input_ml_datasets(self):
        renormalization_weights_of_input_ml_datasets = dict()
        renormalization_biases_of_input_ml_datasets = dict()

        calc_renormalization_weights_and_biases_of_input_ml_dataset = \
            self._calc_renormalization_weights_and_biases_of_input_ml_dataset

        for input_ml_dataset_filename in self._input_ml_dataset_filenames:
            method_alias = \
                calc_renormalization_weights_and_biases_of_input_ml_dataset
            renormalization_weights_and_biases_of_input_ml_dataset = \
                method_alias(input_ml_dataset_filename)
            renormalization_weights_of_input_ml_dataset = \
                renormalization_weights_and_biases_of_input_ml_dataset[0]
            renormalization_biases_of_input_ml_dataset = \
                renormalization_weights_and_biases_of_input_ml_dataset[1]

            key = \
                input_ml_dataset_filename
            renormalization_weights_of_input_ml_datasets[key] = \
                renormalization_weights_of_input_ml_dataset
            renormalization_biases_of_input_ml_datasets[key] = \
                renormalization_biases_of_input_ml_dataset

        return (renormalization_weights_of_input_ml_datasets,
                renormalization_biases_of_input_ml_datasets)



    def _calc_renormalization_weights_and_biases_of_input_ml_dataset(
            self, input_ml_dataset_filename):
        renormalization_weights_of_input_ml_dataset = dict()
        renormalization_biases_of_input_ml_dataset = dict()

        method_alias = \
            self._ml_data_normalization_weights_and_biases_loader._load
        input_normalization_weights, input_normalization_biases = \
            method_alias(path_to_ml_dataset=input_ml_dataset_filename)

        keys_of_normalizable_ml_data_dict_elems = \
            self._ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        for key in self._ml_data_dict_keys:
            if key in keys_of_normalizable_ml_data_dict_elems:
                input_normalization_weight = \
                    input_normalization_weights[key]
                input_normalization_bias = \
                    input_normalization_biases[key]
                output_normalization_weight = \
                    self._output_normalization_weights[key]
                output_normalization_bias = \
                    self._output_normalization_biases[key]

                renormalization_weight = (output_normalization_weight
                                          / input_normalization_weight)
                renormalization_bias = (output_normalization_bias
                                        - (renormalization_weight
                                           * input_normalization_bias))
            else:
                renormalization_weight = 1
                renormalization_bias = 0

            renormalization_weights_of_input_ml_dataset[key] = \
                renormalization_weight
            renormalization_biases_of_input_ml_dataset[key] = \
                renormalization_bias

        return (renormalization_weights_of_input_ml_dataset,
                renormalization_biases_of_input_ml_dataset)



    def _calc_normalization_weights_and_biases_of_output_ml_dataset(self):
        output_normalization_weights = dict()
        output_normalization_biases = dict()

        keys_of_normalizable_ml_data_dict_elems = \
            self._ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        for key in keys_of_normalizable_ml_data_dict_elems:
            output_range_min = float("inf")
            output_range_max = -float("inf")
            
            for input_ml_dataset_filename in self._input_ml_dataset_filenames:
                method_alias = \
                    self._ml_data_normalization_weights_and_biases_loader._load
                input_normalization_weights, input_normalization_biases = \
                    method_alias(path_to_ml_dataset=input_ml_dataset_filename)
                input_normalization_weight = \
                    input_normalization_weights[key]
                input_normalization_bias = \
                    input_normalization_biases[key]
                input_range_min = \
                    -input_normalization_bias/input_normalization_weight
                input_range_max = \
                    input_range_min + (1/input_normalization_weight)

                output_range_min = min(input_range_min, output_range_min)
                output_range_max = max(input_range_max, output_range_max)

            output_normalization_weight = \
                1 / (output_range_max-output_range_min)
            output_normalization_bias = \
                -output_normalization_weight*output_range_min

            output_normalization_weights[key] = output_normalization_weight
            output_normalization_biases[key] = output_normalization_bias

        return (output_normalization_weights, output_normalization_biases)



    def _calc_ml_data_instance_counts_of_input_ml_datasets(self):
        ml_data_instance_counts_of_input_ml_datasets = dict()

        for input_ml_dataset_filename in self._input_ml_dataset_filenames:
            kwargs = \
                {"ml_data_normalizer": self._ml_data_normalizer,
                 "input_ml_dataset_filename": input_ml_dataset_filename}
            num_ml_data_instances_in_input_ml_dataset = \
                _calc_num_ml_data_instances_in_input_ml_dataset(**kwargs)

            key = \
                input_ml_dataset_filename
            ml_data_instance_counts_of_input_ml_datasets[key] = \
                num_ml_data_instances_in_input_ml_dataset

        return ml_data_instance_counts_of_input_ml_datasets



    def _calc_max_num_ml_data_instances_per_chunk(self):
        ml_data_normalizer = \
            self._ml_data_normalizer
        max_num_ml_data_instances_per_file_update = \
            ml_data_normalizer._max_num_ml_data_instances_per_file_update

        max_num_ml_data_instances_per_chunk = \
            (max_num_ml_data_instances_per_file_update
             if (max_num_ml_data_instances_per_file_update < np.inf)
             else self._total_num_ml_data_instances)

        return max_num_ml_data_instances_per_chunk



    def _copy_and_renormalize_all_input_data_and_save_to_output_file(
            self,
            output_ml_dataset_filename,
            rm_input_ml_dataset_files):
        hdf5_dataset_paths = self._ml_data_dict_keys
        self._num_ml_data_instances_copied_from_previous_ml_datasets = 0

        method_alias = \
            self._copy_and_renormalize_input_file_data_and_save_to_output_file

        for input_ml_dataset_filename in self._input_ml_dataset_filenames:
            for hdf5_dataset_path in hdf5_dataset_paths:
                kwargs = {"input_ml_dataset_filename": \
                          input_ml_dataset_filename,
                          "hdf5_dataset_path": \
                          hdf5_dataset_path,
                          "output_ml_dataset_filename": \
                          output_ml_dataset_filename}
                method_alias(**kwargs)

            key = \
                input_ml_dataset_filename
            self._num_ml_data_instances_copied_from_previous_ml_datasets += \
                self._ml_data_instance_counts_of_input_ml_datasets[key]

            if rm_input_ml_dataset_files:
                pathlib.Path(input_ml_dataset_filename).unlink(missing_ok=True)

        kwargs = {"output_ml_dataset_filename": output_ml_dataset_filename}
        self._save_output_normalization_weights_and_biases(**kwargs)

        return None



    def _copy_and_renormalize_input_file_data_and_save_to_output_file(
            self,
            input_ml_dataset_filename,
            hdf5_dataset_path,
            output_ml_dataset_filename):
        kwargs = {"filename": input_ml_dataset_filename,
                  "path_in_file": hdf5_dataset_path}
        input_hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": input_hdf5_dataset_id, "read_only": True}
        input_hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

        kwargs = {"filename": output_ml_dataset_filename,
                  "path_in_file": hdf5_dataset_path}
        output_hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": output_hdf5_dataset_id, "read_only": False}
        output_hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

        kwargs = \
            {"input_ml_dataset_filename": input_ml_dataset_filename,
             "hdf5_dataset_path": hdf5_dataset_path}
        renormalization_weight = \
            self._get_renormalization_weight_of_input_hdf5_dataset(**kwargs)
        renormalization_bias = \
            self._get_renormalization_bias_of_input_hdf5_dataset(**kwargs)

        key = input_ml_dataset_filename
        fraction = (self._ml_data_instance_counts_of_input_ml_datasets[key]
                    / self._max_num_ml_data_instances_per_chunk)
        num_chunks_per_hdf5_dataset = (np.ceil(fraction).astype(int)
                                       * (input_hdf5_dataset.shape is not None))

        method_alias = \
            self._copy_and_renormalize_input_data_chunk_and_save_to_output_file

        for chunk_idx in range(num_chunks_per_hdf5_dataset):
            method_alias(chunk_idx,
                         input_hdf5_dataset,
                         renormalization_weight,
                         renormalization_bias,
                         output_hdf5_dataset)

        input_hdf5_dataset.file.close()
        output_hdf5_dataset.file.close()

        return None



    def _get_renormalization_weight_of_input_hdf5_dataset(
            self, input_ml_dataset_filename, hdf5_dataset_path):
        key_1 = \
            input_ml_dataset_filename
        key_2 = \
            hdf5_dataset_path
        renormalization_weight_of_input_hdf5_dataset = \
            self._renormalization_weights_of_input_ml_datasets[key_1][key_2]

        return renormalization_weight_of_input_hdf5_dataset



    def _get_renormalization_bias_of_input_hdf5_dataset(
            self, input_ml_dataset_filename, hdf5_dataset_path):
        key_1 = \
            input_ml_dataset_filename
        key_2 = \
            hdf5_dataset_path
        renormalization_bias_of_input_hdf5_dataset = \
            self._renormalization_biases_of_input_ml_datasets[key_1][key_2]

        return renormalization_bias_of_input_hdf5_dataset



    def _copy_and_renormalize_input_data_chunk_and_save_to_output_file(
            self,
            chunk_idx,
            input_hdf5_dataset,
            renormalization_weight,
            renormalization_bias,
            output_hdf5_dataset):
        data_chunk = self._load_data_chunk(chunk_idx, input_hdf5_dataset)

        obj_alias = \
            self._ml_data_value_validator
        method_alias = \
            obj_alias._check_values_of_hdf5_datasubset_of_ml_dataset_file
        kwargs = \
            {"hdf5_dataset": input_hdf5_dataset,
             "hdf5_datasubset": data_chunk}
        _ = \
            method_alias(**kwargs)

        keys_of_normalizable_ml_data_dict_elems = \
            self._ml_data_normalizer._keys_of_normalizable_ml_data_dict_elems

        hdf5_dataset_path = input_hdf5_dataset.name[1:]
        key = hdf5_dataset_path
            
        renormalized_data_chunk = (data_chunk*renormalization_weight
                                   + renormalization_bias)
        if key in keys_of_normalizable_ml_data_dict_elems:
            renormalized_data_chunk.clip(min=0, max=1)

        self._save_renormalized_data_chunk(chunk_idx,
                                           renormalized_data_chunk,
                                           output_hdf5_dataset)

        return None



    def _load_data_chunk(self, chunk_idx, input_hdf5_dataset):
        kwargs = {"chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  self._max_num_ml_data_instances_per_chunk,
                  "input_hdf5_dataset": input_hdf5_dataset}
        data_chunk = _load_contiguous_data_chunk(**kwargs)

        return data_chunk



    def _save_renormalized_data_chunk(self,
                                      chunk_idx,
                                      renormalized_data_chunk,
                                      output_hdf5_dataset):
        starting_idx_offset = \
            self._num_ml_data_instances_copied_from_previous_ml_datasets

        kwargs = {"starting_idx_offset": \
                  starting_idx_offset,
                  "chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  self._max_num_ml_data_instances_per_chunk,
                  "data_chunk": \
                  renormalized_data_chunk,
                  "output_hdf5_dataset": \
                  output_hdf5_dataset}
        _save_data_chunk(**kwargs)

        return None



    def _save_output_normalization_weights_and_biases(
            self, output_ml_dataset_filename):
        kwargs = {"ml_data_normalizer": self._ml_data_normalizer,
                  "normalization_weights": self._output_normalization_weights,
                  "normalization_biases": self._output_normalization_biases,
                  "output_ml_dataset_filename": output_ml_dataset_filename}
        _save_normalization_weights_and_biases(**kwargs)

        return None



def _calc_adjusted_split_ratio(original_split_ratio, num_ml_data_instances):
    adjusted_split_ratio = (num_ml_data_instances
                            * np.array(original_split_ratio)
                            / np.sum(original_split_ratio))
    adjusted_split_ratio = np.round(adjusted_split_ratio).astype(int)

    for idx, _ in enumerate(adjusted_split_ratio):
        discrepancy = num_ml_data_instances - np.sum(adjusted_split_ratio)
        adjustment_candidate = adjusted_split_ratio[idx] + np.sign(discrepancy)
        readjustment_is_needed = ((discrepancy*adjusted_split_ratio[idx] != 0)
                                  and (adjustment_candidate >= 0))
        adjusted_split_ratio[idx] = (adjustment_candidate
                                     if readjustment_is_needed
                                     else adjusted_split_ratio[idx])

    return adjusted_split_ratio



class _MLDataShapeAnalyzer():
    def __init__(self,
                 variable_axis_size_dict_keys,
                 ml_data_dict_key_to_shape_template_map,
                 ml_data_dict_elem_decoders):
        self._variable_axis_size_dict_keys = \
            variable_axis_size_dict_keys
        self._ml_data_dict_key_to_shape_template_map = \
            ml_data_dict_key_to_shape_template_map
        self._ml_data_dict_elem_decoders = \
            ml_data_dict_elem_decoders

        return None



    def _hdf5_dataset_path_to_shape_map_for_ml_dataset_combo(
            self, input_ml_dataset_filenames):
        method_names = \
            ("_hdf5_dataset_path_to_shape_map_of_ml_dataset_file",
             "_check_hdf5_dataset_path_to_shape_maps_of_two_ml_dataset_files",
             "_hdf5_dataset_path_to_shape_map_of_ml_dataset_file_as_if_resized")
        method_aliases = \
            tuple(getattr(self, method_name) for method_name in method_names)

        num_input_ml_datasets = len(input_ml_dataset_filenames)
        total_num_ml_data_instances = 0
        
        for input_ml_dataset_idx in range(num_input_ml_datasets):
            input_ml_dataset_filename = \
                input_ml_dataset_filenames[input_ml_dataset_idx]
            hdf5_dataset_path_to_shape_map_1 = \
                method_aliases[0](path_to_ml_dataset=input_ml_dataset_filename)

            random_hdf5_dataset_shape = \
                next(iter(hdf5_dataset_path_to_shape_map_1.values()))
            num_ml_data_instances_in_input_ml_dataset = \
                random_hdf5_dataset_shape[0]
            total_num_ml_data_instances += \
                num_ml_data_instances_in_input_ml_dataset

            if input_ml_dataset_idx == 0:
                hdf5_dataset_path_to_shape_map_2 = \
                    hdf5_dataset_path_to_shape_map_1
            else:
                kwargs = \
                    {"map_1": hdf5_dataset_path_to_shape_map_1,
                     "map_2": hdf5_dataset_path_to_shape_map_2,
                     "path_to_ml_dataset_1": input_ml_dataset_filename,
                     "path_to_ml_dataset_2": input_ml_dataset_filenames[0]}
                _ = \
                    method_aliases[1](**kwargs)

        hdf5_dataset_path_to_shape_map = \
            hdf5_dataset_path_to_shape_map_1
        num_ml_data_instances_after_resizing = \
            total_num_ml_data_instances

        method_aliases[2](hdf5_dataset_path_to_shape_map,
                          num_ml_data_instances_after_resizing)

        return hdf5_dataset_path_to_shape_map



    def _hdf5_dataset_path_to_shape_map_of_ml_dataset_file(self,
                                                           path_to_ml_dataset):
        variable_axis_size_dict = dict()
        variable_axis_size_key_to_axis_id_map = dict()
        hdf5_dataset_path_to_shape_map = dict()
        
        for key in self._ml_data_dict_key_to_shape_template_map:
            shape_template = self._ml_data_dict_key_to_shape_template_map[key]
            hdf5_dataset_path = key

            kwargs = {"filename": path_to_ml_dataset,
                      "path_in_file": hdf5_dataset_path}
            hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

            kwargs = {"dataset_id": hdf5_dataset_id, "read_only": True}
            hdf5_dataset = h5pywrappers.dataset.load(**kwargs)
            hdf5_dataset_shape = hdf5_dataset.shape
            hdf5_dataset.file.close()

            check_hdf5_dataset_shape = self._check_hdf5_dataset_shape
            check_hdf5_dataset_shape(hdf5_dataset_shape,
                                     shape_template,
                                     variable_axis_size_dict,
                                     variable_axis_size_key_to_axis_id_map,
                                     hdf5_dataset_path,
                                     path_to_ml_dataset)

            hdf5_dataset_path_to_shape_map[hdf5_dataset_path] = \
                hdf5_dataset_shape

        return hdf5_dataset_path_to_shape_map



    def _check_hdf5_dataset_shape(self,
                                  hdf5_dataset_shape,
                                  shape_template,
                                  variable_axis_size_dict,
                                  variable_axis_size_key_to_axis_id_map,
                                  hdf5_dataset_path,
                                  path_to_ml_dataset):
        modified_hdf5_dataset_shape = (hdf5_dataset_shape
                                       if (hdf5_dataset_shape != None)
                                       else tuple())

        key = hdf5_dataset_path

        num_axes = len(modified_hdf5_dataset_shape)
        expected_num_axes = (len(shape_template)
                             if (key not in self._ml_data_dict_elem_decoders)
                             else 0)

        num_elems = np.prod(modified_hdf5_dataset_shape)
        num_elems_lower_limit = int(key
                                    not in
                                    self._ml_data_dict_elem_decoders)

        unformatted_err_msg = (_ml_data_shape_analyzer_err_msg_1
                               if (key not in self._ml_data_dict_elem_decoders)
                               else _ml_data_shape_analyzer_err_msg_2)

        if (((num_axes != expected_num_axes)
             or (num_elems < num_elems_lower_limit))
            or ((key in self._ml_data_dict_elem_decoders)
                and (hdf5_dataset_shape != None))):
            args = ((hdf5_dataset_path, path_to_ml_dataset, expected_num_axes)
                    if (key not in self._ml_data_dict_elem_decoders)
                    else (hdf5_dataset_path, path_to_ml_dataset))
            err_msg = unformatted_err_msg.format(*args)
            raise ValueError(err_msg)

        for current_axis_idx, _ in enumerate(modified_hdf5_dataset_shape):
            current_axis_size = modified_hdf5_dataset_shape[current_axis_idx]
            self._check_current_axis(shape_template,
                                     current_axis_idx,
                                     current_axis_size,
                                     variable_axis_size_dict,
                                     variable_axis_size_key_to_axis_id_map,
                                     path_to_ml_dataset,
                                     hdf5_dataset_path)

        return None



    def _check_current_axis(self,
                            shape_template,
                            current_axis_idx,
                            current_axis_size,
                            variable_axis_size_dict,
                            variable_axis_size_key_to_axis_id_map,
                            path_to_ml_dataset,
                            hdf5_dataset_path):
        unformatted_err_msg_3 = _ml_data_shape_analyzer_err_msg_3
        unformatted_err_msg_4 = _ml_data_shape_analyzer_err_msg_4
        unformatted_err_msg_5 = _ml_data_shape_analyzer_err_msg_5

        if isinstance(shape_template[current_axis_idx], str):
            key = shape_template[current_axis_idx]
            if key not in variable_axis_size_dict:
                variable_axis_size_dict[key] = current_axis_size
            else:
                if current_axis_size != variable_axis_size_dict[key]:
                    axis_id = variable_axis_size_key_to_axis_id_map[key]
                    args = (axis_id[0],
                            path_to_ml_dataset,
                            current_axis_idx,
                            axis_id[1])
                    args = ((hdf5_dataset_path,) + args
                            if (hdf5_dataset_path != axis_id[0])
                            else args)
                    err_msg = (unformatted_err_msg_3.format(*args)
                               if (hdf5_dataset_path != axis_id[0])
                               else unformatted_err_msg_4.format(*args))
                    raise ValueError(err_msg)
            axis_id = (hdf5_dataset_path, current_axis_idx)
            variable_axis_size_key_to_axis_id_map[key] = axis_id
        else:
            expected_axis_size = shape_template[current_axis_idx]
            if current_axis_size != expected_axis_size:
                err_msg = unformatted_err_msg_5.format(hdf5_dataset_path,
                                                       path_to_ml_dataset,
                                                       current_axis_idx,
                                                       expected_axis_size)
                raise ValueError(err_msg)

        return None



    def _check_hdf5_dataset_path_to_shape_maps_of_two_ml_dataset_files(
            self, map_1, map_2, path_to_ml_dataset_1, path_to_ml_dataset_2):
        unformatted_err_msg = _ml_data_shape_analyzer_err_msg_6
        
        hdf5_dataset_path_to_shape_map_1 = map_1
        hdf5_dataset_path_to_shape_map_2 = map_2

        key_of_variable_axis_size_corresponding_to_num_ml_data_instances = \
            self._variable_axis_size_dict_keys[0]
        first_key_of_variable_axis_size_dict = \
            key_of_variable_axis_size_corresponding_to_num_ml_data_instances

        for key in self._ml_data_dict_key_to_shape_template_map:
            shape_template = \
                self._ml_data_dict_key_to_shape_template_map[key]
            hdf5_dataset_path = \
                key
            hdf5_dataset_1_shape = \
                hdf5_dataset_path_to_shape_map_1[hdf5_dataset_path]
            hdf5_dataset_2_shape = \
                hdf5_dataset_path_to_shape_map_2[hdf5_dataset_path]

            num_axes = (len(shape_template)
                        * (key not in self._ml_data_dict_elem_decoders))
            for axis_idx in range(num_axes):
                key = first_key_of_variable_axis_size_dict
                if shape_template[axis_idx] != key:
                    axis_1_size = hdf5_dataset_1_shape[axis_idx]
                    axis_2_size = hdf5_dataset_2_shape[axis_idx]
                    if axis_1_size != axis_2_size:
                        args = (path_to_ml_dataset_1,
                                path_to_ml_dataset_2,
                                hdf5_dataset_path,
                                axis_idx,
                                axis_idx)
                        err_msg = unformatted_err_msg.format(*args)
                        raise ValueError(err_msg)
        
        return None



    def _hdf5_dataset_path_to_shape_map_of_ml_dataset_file_as_if_resized(
            self,
            hdf5_dataset_path_to_shape_map,
            num_ml_data_instances_after_resizing):
        key_of_variable_axis_size_corresponding_to_num_ml_data_instances = \
            self._variable_axis_size_dict_keys[0]
        first_key_of_variable_axis_size_dict = \
            key_of_variable_axis_size_corresponding_to_num_ml_data_instances

        for key in self._ml_data_dict_key_to_shape_template_map:
            shape_template = \
                self._ml_data_dict_key_to_shape_template_map.get(key, tuple())
            hdf5_dataset_path = \
                key

            hdf5_dataset_shape = \
                list(hdf5_dataset_path_to_shape_map.get(hdf5_dataset_path, []))

            for axis_idx, _ in enumerate(shape_template):
                key = \
                    first_key_of_variable_axis_size_dict
                if shape_template[axis_idx] == key:
                    hdf5_dataset_shape[axis_idx] = \
                        num_ml_data_instances_after_resizing

            hdf5_dataset_shape = \
                tuple(hdf5_dataset_shape)
            hdf5_dataset_path_to_shape_map[hdf5_dataset_path] = \
                hdf5_dataset_shape

        return None



    def _hdf5_dataset_path_to_shape_maps_for_ml_dataset_split(
            self, input_ml_dataset_filename, split_ratio):
        method_names = \
            ("_hdf5_dataset_path_to_shape_map_of_ml_dataset_file",
             "_hdf5_dataset_path_to_shape_map_of_ml_dataset_file_as_if_resized")
        method_aliases = \
            (getattr(self, method_names[0]), getattr(self, method_names[1]))

        kwargs = {"path_to_ml_dataset": input_ml_dataset_filename}
        hdf5_dataset_path_to_shape_map = method_aliases[0](**kwargs)

        num_ml_data_instances = 0
        for hdf5_dataset_path in hdf5_dataset_path_to_shape_map:
            key = hdf5_dataset_path
            hdf5_dataset_shape = ((0,)
                                  if (key in self._ml_data_dict_elem_decoders)
                                  else hdf5_dataset_path_to_shape_map[key])
            num_ml_data_instances = max(num_ml_data_instances,
                                        hdf5_dataset_shape[0])

        kwargs = {"original_split_ratio": split_ratio,
                  "num_ml_data_instances": num_ml_data_instances}
        adjusted_split_ratio = _calc_adjusted_split_ratio(**kwargs)

        hdf5_dataset_path_to_shape_maps = tuple()
        for output_ml_dataset_idx, _ in enumerate(adjusted_split_ratio):
            kwargs = {"hdf5_dataset_path_to_shape_map": \
                      hdf5_dataset_path_to_shape_map,
                      "num_ml_data_instances_after_resizing": \
                      adjusted_split_ratio[output_ml_dataset_idx]}
            method_aliases[1](**kwargs)

            hdf5_dataset_path_to_shape_maps += \
                (copy.deepcopy(hdf5_dataset_path_to_shape_map),)

        return hdf5_dataset_path_to_shape_maps



    def _check_shape_of_data_chunk(
            self,
            name_of_obj_alias_from_which_data_chunk_was_obtained,
            key_used_to_get_data_chunk,
            data_chunk,
            variable_axis_size_dict):
        unformatted_err_msg = _ml_data_shape_analyzer_err_msg_7
        args = (name_of_obj_alias_from_which_data_chunk_was_obtained,
                key_used_to_get_data_chunk)
        err_msg = unformatted_err_msg.format(*args)

        key = key_used_to_get_data_chunk
        shape_template = self._ml_data_dict_key_to_shape_template_map[key]

        if len(data_chunk.shape) != len(shape_template):
            raise ValueError(err_msg)

        for axis_idx, _ in enumerate(shape_template):            
            if shape_template[axis_idx] in variable_axis_size_dict:
                key = shape_template[axis_idx]
                if variable_axis_size_dict[key] is None:
                    continue
                expected_axis_size = variable_axis_size_dict[key]
            else:
                expected_axis_size = shape_template[axis_idx]
                
            if data_chunk.shape[axis_idx] != expected_axis_size:
                raise ValueError(err_msg)

        return None



    def _update_variable_axis_size_dict(self,
                                        key_used_to_get_data_chunk,
                                        variable_axis_size_dict,
                                        data_chunk):
        key = key_used_to_get_data_chunk
        shape_template = self._ml_data_dict_key_to_shape_template_map[key]

        for axis_idx, _ in enumerate(shape_template):
            if shape_template[axis_idx] in variable_axis_size_dict:
                key = shape_template[axis_idx]
                if variable_axis_size_dict[key] is None:
                    variable_axis_size_dict[key] = data_chunk.shape[axis_idx]

        return None



    def _check_variable_axis_size_dict(self,
                                       variable_axis_size_dict,
                                       ml_data_dict,
                                       name_of_obj_alias_of_ml_data_dict):

        return None



class _MLDataSplitter():
    def __init__(self,
                 input_ml_dataset_filename,
                 ml_data_normalization_weights_and_biases_loader,
                 enable_shuffling,
                 rng_seed,
                 max_num_ml_data_instances_per_file_update,
                 split_ratio):
        self._input_ml_dataset_filename = \
            input_ml_dataset_filename
        self._ml_data_normalization_weights_and_biases_loader = \
            ml_data_normalization_weights_and_biases_loader
        self._enable_shuffling = \
            enable_shuffling
        self._rng_seed = \
            rng_seed

        obj_alias = \
            ml_data_normalization_weights_and_biases_loader
        ml_data_normalizer = \
            obj_alias._ml_data_normalizer
        ml_data_normalizer._max_num_ml_data_instances_per_file_update = \
            max_num_ml_data_instances_per_file_update
        
        self._ml_data_normalizer = ml_data_normalizer
        self._ml_data_value_validator = obj_alias._ml_data_value_validator

        kwargs = \
            {"ml_data_normalizer": ml_data_normalizer,
             "input_ml_dataset_filename": input_ml_dataset_filename}
        self._total_num_ml_data_instances = \
            _calc_num_ml_data_instances_in_input_ml_dataset(**kwargs)

        kwargs = {"original_split_ratio": split_ratio,
                  "num_ml_data_instances": self._total_num_ml_data_instances}
        self._adjusted_split_ratio = _calc_adjusted_split_ratio(**kwargs)

        self._ml_data_dict_keys = ml_data_normalizer._ml_data_dict_keys

        self._partition_plan = self._calc_partition_plan()

        method_alias = \
            self._ml_data_normalization_weights_and_biases_loader._load
        self._input_normalization_weights, self._input_normalization_biases = \
            method_alias(path_to_ml_dataset=input_ml_dataset_filename)

        return None



    def _calc_partition_plan(self):
        rng = np.random.default_rng(self._rng_seed)
        adjusted_split_ratio = self._adjusted_split_ratio
        enable_shuffling = self._enable_shuffling

        ml_data_instance_idx_to_output_ml_dataset_idx_map = \
            tuple()
        for output_ml_dataset_idx, _ in enumerate(adjusted_split_ratio):
            num_ml_data_instances_in_output_ml_dataset = \
                adjusted_split_ratio[output_ml_dataset_idx]
            ml_dataset_idx = \
                output_ml_dataset_idx
            num_ml_data_instances_in_ml_dataset = \
                num_ml_data_instances_in_output_ml_dataset
            ml_data_instance_idx_to_output_ml_dataset_idx_map += \
                (ml_dataset_idx,)*num_ml_data_instances_in_ml_dataset
        ml_data_instance_idx_to_output_ml_dataset_idx_map = \
            np.array(ml_data_instance_idx_to_output_ml_dataset_idx_map)
        if enable_shuffling:
            _ = \
                rng.shuffle(ml_data_instance_idx_to_output_ml_dataset_idx_map)

        output_ml_dataset_idx_to_ml_data_instance_idx_subset_map = \
            tuple()
        for output_ml_dataset_idx, _ in enumerate(adjusted_split_ratio):
            map_alias_1 = \
                ml_data_instance_idx_to_output_ml_dataset_idx_map
            ml_data_instance_idx_subset = \
                tuple((map_alias_1 == output_ml_dataset_idx).nonzero()[0])
            output_ml_dataset_idx_to_ml_data_instance_idx_subset_map += \
                (ml_data_instance_idx_subset,)

        partition_plan = \
            output_ml_dataset_idx_to_ml_data_instance_idx_subset_map

        return partition_plan



    def _copy_and_split_input_data_and_save_to_output_files(
            self,
            output_ml_dataset_filenames,
            rm_input_ml_dataset_file):
        for output_ml_dataset_idx, _ in enumerate(output_ml_dataset_filenames):
            output_ml_dataset_filename = \
                output_ml_dataset_filenames[output_ml_dataset_idx]

            kwargs = {"output_ml_dataset_idx": output_ml_dataset_idx,
                      "output_ml_dataset_filename": output_ml_dataset_filename}
            self._copy_input_data_shard_and_save_to_output_file(**kwargs)

        if rm_input_ml_dataset_file:
            input_ml_dataset_filename = self._input_ml_dataset_filename
            pathlib.Path(input_ml_dataset_filename).unlink(missing_ok=True)

        return None



    def _copy_input_data_shard_and_save_to_output_file(
            self, output_ml_dataset_idx, output_ml_dataset_filename):
        hdf5_dataset_paths = self._ml_data_dict_keys

        method_alias = \
            self._calc_max_num_ml_data_instances_per_chunk
        max_num_ml_data_instances_per_chunk = \
            method_alias(output_ml_dataset_idx)

        fraction = (self._adjusted_split_ratio[output_ml_dataset_idx]
                    / max_num_ml_data_instances_per_chunk)
        num_chunks_per_hdf5_dataset = np.ceil(fraction).astype(int)

        if num_chunks_per_hdf5_dataset > 0:
            for hdf5_dataset_path in hdf5_dataset_paths:
                method_alias = \
                    self._copy_input_hdf5_datasubset_and_save_to_output_file
                kwargs = \
                    {"hdf5_dataset_path": \
                     hdf5_dataset_path,
                     "output_ml_dataset_filename": \
                     output_ml_dataset_filename,
                     "num_chunks_per_hdf5_dataset": \
                     num_chunks_per_hdf5_dataset,
                     "output_ml_dataset_idx": \
                     output_ml_dataset_idx,
                     "max_num_ml_data_instances_per_chunk": \
                     max_num_ml_data_instances_per_chunk}
                _ = \
                    method_alias(**kwargs)

            method_alias = \
                self._copy_input_normalization_weights_and_biases_to_output_file
            _ = \
                method_alias(output_ml_dataset_filename)

        return None



    def _calc_max_num_ml_data_instances_per_chunk(self, output_ml_dataset_idx):
        ml_data_normalizer = \
            self._ml_data_normalizer
        max_num_ml_data_instances_per_file_update = \
            ml_data_normalizer._max_num_ml_data_instances_per_file_update

        max_num_ml_data_instances_per_chunk = \
            (max_num_ml_data_instances_per_file_update
             if (max_num_ml_data_instances_per_file_update < np.inf)
             else self._adjusted_split_ratio[output_ml_dataset_idx])

        return max_num_ml_data_instances_per_chunk



    def _copy_input_hdf5_datasubset_and_save_to_output_file(
            self,
            hdf5_dataset_path,
            output_ml_dataset_filename,
            num_chunks_per_hdf5_dataset,
            output_ml_dataset_idx,
            max_num_ml_data_instances_per_chunk):
        kwargs = {"filename": self._input_ml_dataset_filename,
                  "path_in_file": hdf5_dataset_path}
        input_hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": input_hdf5_dataset_id, "read_only": True}
        input_hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

        kwargs = {"filename": output_ml_dataset_filename,
                  "path_in_file": hdf5_dataset_path}
        output_hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset_id": output_hdf5_dataset_id, "read_only": False}
        output_hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

        chunk_indices = range((input_hdf5_dataset.shape is not None)
                              * num_chunks_per_hdf5_dataset)

        for chunk_idx in chunk_indices:
            kwargs = {"output_ml_dataset_idx": \
                      output_ml_dataset_idx,
                      "chunk_idx": \
                      chunk_idx,
                      "max_num_ml_data_instances_per_chunk": \
                      max_num_ml_data_instances_per_chunk,
                      "input_hdf5_dataset": \
                      input_hdf5_dataset,
                      "output_hdf5_dataset": \
                      output_hdf5_dataset}
            self._copy_input_data_chunk_and_save_to_output_file(**kwargs)

        input_hdf5_dataset.file.close()
        output_hdf5_dataset.file.close()

        return None



    def _copy_input_data_chunk_and_save_to_output_file(
            self,
            output_ml_dataset_idx,
            chunk_idx,
            max_num_ml_data_instances_per_chunk,
            input_hdf5_dataset,
            output_hdf5_dataset):
        kwargs = {"output_ml_dataset_idx": \
                  output_ml_dataset_idx,
                  "chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  max_num_ml_data_instances_per_chunk,
                  "input_hdf5_dataset": \
                  input_hdf5_dataset}
        data_chunk = self._load_data_chunk(**kwargs)

        obj_alias = \
            self._ml_data_value_validator
        method_alias = \
            obj_alias._check_values_of_hdf5_datasubset_of_ml_dataset_file
        kwargs = \
            {"hdf5_dataset": input_hdf5_dataset,
             "hdf5_datasubset": data_chunk}
        _ = \
            method_alias(**kwargs)

        kwargs = {"output_ml_dataset_idx": \
                  output_ml_dataset_idx,
                  "chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  max_num_ml_data_instances_per_chunk,
                  "data_chunk": \
                  data_chunk,
                  "output_hdf5_dataset": \
                  output_hdf5_dataset}
        self._save_data_chunk(**kwargs)

        return None



    def _load_data_chunk(self,
                         output_ml_dataset_idx,
                         chunk_idx,
                         max_num_ml_data_instances_per_chunk,
                         input_hdf5_dataset):
        shuffling_has_been_enabled = self._enable_shuffling
        shuffling_has_not_been_enabled = (not self._enable_shuffling)

        previous_input_ml_data_instance_idx_subset = \
            (self._partition_plan[output_ml_dataset_idx-1]
             * (output_ml_dataset_idx>0))
        current_input_ml_data_instance_idx_subset = \
            self._partition_plan[output_ml_dataset_idx]

        start = \
            (chunk_idx*max_num_ml_data_instances_per_chunk
             + (shuffling_has_not_been_enabled
                * len(previous_input_ml_data_instance_idx_subset)))
        
        stop_candidate_1 = \
            (len(current_input_ml_data_instance_idx_subset)
             + (shuffling_has_not_been_enabled
                * len(previous_input_ml_data_instance_idx_subset)))
        
        stop_candidate_2 = \
            start + max_num_ml_data_instances_per_chunk
        
        stop = min(stop_candidate_1, stop_candidate_2)
        
        single_dim_slice = slice(start, stop)

        idx_subset = current_input_ml_data_instance_idx_subset
        idx_subsubset = list(idx_subset[single_dim_slice])
        
        data_chunk = (input_hdf5_dataset[idx_subsubset]
                      if shuffling_has_been_enabled
                      else input_hdf5_dataset[single_dim_slice])

        return data_chunk



    def _save_data_chunk(self,
                         output_ml_dataset_idx,
                         chunk_idx,
                         max_num_ml_data_instances_per_chunk,
                         data_chunk,
                         output_hdf5_dataset):
        kwargs = {"starting_idx_offset": \
                  0,
                  "chunk_idx": \
                  chunk_idx,
                  "max_num_ml_data_instances_per_chunk": \
                  max_num_ml_data_instances_per_chunk,
                  "data_chunk": \
                  data_chunk,
                  "output_hdf5_dataset": \
                  output_hdf5_dataset}
        _save_data_chunk(**kwargs)

        return None



    def _copy_input_normalization_weights_and_biases_to_output_file(
            self, output_ml_dataset_filename):
        kwargs = {"ml_data_normalizer": self._ml_data_normalizer,
                  "normalization_weights": self._input_normalization_weights,
                  "normalization_biases": self._input_normalization_biases,
                  "output_ml_dataset_filename": output_ml_dataset_filename}
        _save_normalization_weights_and_biases(**kwargs)

        return None



def _check_and_convert_generate_and_save_ml_dataset_params(params):
    params = params.copy()

    func_alias = _check_and_convert_output_filename
    params["output_filename"] = func_alias(params)

    func_alias = _check_and_convert_max_num_ml_data_instances_per_file_update
    params["max_num_ml_data_instances_per_file_update"] = func_alias(params)

    return params



def _check_and_convert_output_filename(params):
    obj_name = "output_filename"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    output_filename = czekitout.convert.to_str_from_str_like(**kwargs)
    
    return output_filename



def _check_and_convert_max_num_ml_data_instances_per_file_update(params):
    obj_name = "max_num_ml_data_instances_per_file_update"
    obj = params[obj_name]

    kwargs = \
        {"obj": obj, "obj_name": obj_name}
    max_num_ml_data_instances_per_file_update = \
        (obj
         if (obj == float("inf"))
         else czekitout.convert.to_positive_int(**kwargs))

    return max_num_ml_data_instances_per_file_update



_default_output_filename = "ml_dataset.h5"
_default_max_num_ml_data_instances_per_file_update = 100



def _generate_and_save_ml_dataset(
        output_filename,
        unnormalized_ml_data_instance_generator,
        ml_data_normalizer,
        num_ml_data_instances,
        ml_data_dict_key_to_dtype_map,
        axes_labels_of_hdf5_datasets_of_ml_dataset_file,
        start_time):
    _print_generate_and_save_ml_dataset_starting_msg(output_filename)

    func_alias = _generate_hdf5_dataset_path_to_shape_map_of_ml_dataset_file
    kwargs = {"unnormalized_ml_data_instance_generator": \
              unnormalized_ml_data_instance_generator,
              "ml_data_normalizer": \
              ml_data_normalizer,
              "num_ml_data_instances": \
              num_ml_data_instances}
    hdf5_dataset_path_to_shape_map_of_ml_dataset_file = func_alias(**kwargs)

    try:
        kwargs = {"output_filename": \
                  output_filename,
                  "hdf5_dataset_path_to_shape_map_of_ml_dataset_file": \
                  hdf5_dataset_path_to_shape_map_of_ml_dataset_file,
                  "ml_data_dict_key_to_dtype_map": \
                  ml_data_dict_key_to_dtype_map,
                  "axes_labels_of_hdf5_datasets_of_ml_dataset_file": \
                  axes_labels_of_hdf5_datasets_of_ml_dataset_file}
        _initialize_output_file_to_which_to_save_ml_dataset(**kwargs)

        kwargs = {"unnormalized_ml_data_instance_generator": \
                  unnormalized_ml_data_instance_generator,
                  "ml_data_normalizer": \
                  ml_data_normalizer,
                  "ml_data_dict_key_to_dtype_map": \
                  ml_data_dict_key_to_dtype_map,
                  "total_num_ml_data_instances": \
                  num_ml_data_instances,
                  "output_filename": \
                  output_filename}
        _generate_and_save_data_of_ml_dataset_to_output_file(**kwargs)
    except:
        current_func_name = "_generate_and_save_ml_dataset"
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(output_filename)
        raise IOError(err_msg)

    _print_generate_and_save_ml_dataset_end_msg(start_time, output_filename)

    return None



def _print_generate_and_save_ml_dataset_starting_msg(output_filename):
    unformatted_msg = ("Generating machine learning dataset and saving it to "
                       "the HDF5 file ``'{}'``...\n\n\n")
    msg = unformatted_msg.format(output_filename)
    print(msg)

    return None



def _generate_hdf5_dataset_path_to_shape_map_of_ml_dataset_file(
        unnormalized_ml_data_instance_generator,
        ml_data_normalizer,
        num_ml_data_instances):
    obj_alias = unnormalized_ml_data_instance_generator
    ml_data_instances = obj_alias._cached_ml_data_instances

    ml_data_dict = ml_data_instances

    hdf5_dataset_path_to_shape_map = \
        dict()
    for key, ml_data_dict_elem in ml_data_dict.items():
        hdf5_dataset_shape = \
            (None
             if (ml_data_dict_elem is None)
             else (num_ml_data_instances,) + ml_data_dict_elem.shape[1:])

        hdf5_dataset_path = \
            key
        hdf5_dataset_path_to_shape_map[hdf5_dataset_path] = \
            hdf5_dataset_shape

    return hdf5_dataset_path_to_shape_map



def _initialize_output_file_to_which_to_save_ml_dataset(
        output_filename,
        hdf5_dataset_path_to_shape_map_of_ml_dataset_file,
        ml_data_dict_key_to_dtype_map,
        axes_labels_of_hdf5_datasets_of_ml_dataset_file):
    output_dirname = str(pathlib.Path(output_filename).parent)
    _make_output_dir(output_dirname)

    with h5py.File(output_filename, "w"):
        pass

    hdf5_dataset_path_to_shape_map = \
        hdf5_dataset_path_to_shape_map_of_ml_dataset_file

    for hdf5_dataset_path in hdf5_dataset_path_to_shape_map:
        key = hdf5_dataset_path
        hdf5_group_path = str(pathlib.Path(hdf5_dataset_path).parent)
        hdf5_dataset_name = str(pathlib.Path(hdf5_dataset_path).name)
        hdf5_dataset_shape = hdf5_dataset_path_to_shape_map[hdf5_dataset_path]
        hdf5_dataset_dtype = ml_data_dict_key_to_dtype_map[key]

        kwargs = {"filename": output_filename, "path_in_file": hdf5_group_path}
        group_id = h5pywrappers.obj.ID(**kwargs)
        
        group = h5pywrappers.group.load(group_id, read_only=False)
        hdf5_dataset = group.create_dataset(name=hdf5_dataset_name,
                                            shape=hdf5_dataset_shape,
                                            dtype=hdf5_dataset_dtype)
        group.file.close()

        axes_labels_of_hdf5_dataset = \
            axes_labels_of_hdf5_datasets_of_ml_dataset_file[hdf5_dataset_path]

        _save_axes_labels_of_hdf5_dataset_as_attrs(axes_labels_of_hdf5_dataset,
                                                   hdf5_dataset_path,
                                                   output_filename)

    return None



def _save_axes_labels_of_hdf5_dataset_as_attrs(axes_labels_of_hdf5_dataset,
                                               hdf5_dataset_path,
                                               output_filename):
    kwargs = {"filename": output_filename, "path_in_file": hdf5_dataset_path}
    hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

    for axis_idx, axis_label in enumerate(axes_labels_of_hdf5_dataset):
        attr_name = "dim_{}".format(axis_idx)
        kwargs = {"obj_id": hdf5_dataset_id, "attr_name": attr_name}
        attr_id = h5pywrappers.attr.ID(**kwargs)
        
        kwargs = {"attr": axis_label, "attr_id": attr_id, "write_mode": "a"}
        h5pywrappers.attr.save(**kwargs)

    return None



def _make_output_dir(output_dirname):
    current_func_name = "_make_output_dir"

    try:
        pathlib.Path(output_dirname).mkdir(parents=True, exist_ok=True)
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(output_dirname)
        raise IOError(err_msg)

    return None



def _generate_and_save_data_of_ml_dataset_to_output_file(
        unnormalized_ml_data_instance_generator,
        ml_data_normalizer,
        ml_data_dict_key_to_dtype_map,
        total_num_ml_data_instances,
        output_filename):
    kwargs = {"unnormalized_ml_data_instance_generator": \
              unnormalized_ml_data_instance_generator,
              "ml_data_normalizer": \
              ml_data_normalizer,
              "total_num_ml_data_instances": \
              total_num_ml_data_instances,
              "ml_data_dict_key_to_dtype_map": \
              ml_data_dict_key_to_dtype_map}
    ml_dataset_buffer = _initialize_ml_dataset_buffer(**kwargs)

    ml_data_instance_idx = 0
    
    while ml_data_instance_idx < total_num_ml_data_instances:
        func_alias = \
            _update_and_flush_buffer_and_return_updated_ml_data_instance_idx
        kwargs = \
            {"unnormalized_ml_data_instance_generator": \
             unnormalized_ml_data_instance_generator,
             "ml_data_normalizer": \
             ml_data_normalizer,
             "ml_dataset_buffer": \
             ml_dataset_buffer,
             "ml_data_instance_idx": \
             ml_data_instance_idx,
             "total_num_ml_data_instances": \
             total_num_ml_data_instances,
             "output_filename": \
             output_filename}
        ml_data_instance_idx = \
            func_alias(**kwargs)

        ml_data_normalizer._update_extrema_cache(ml_data_dict=ml_dataset_buffer)

    path_to_ml_dataset = output_filename
    kwargs = {"path_to_ml_dataset": output_filename}
    ml_data_normalizer._normalize_ml_dataset_file(**kwargs)

    return None



def _initialize_ml_dataset_buffer(unnormalized_ml_data_instance_generator,
                                  ml_data_normalizer,
                                  total_num_ml_data_instances,
                                  ml_data_dict_key_to_dtype_map):
    ml_dataset_buffer = dict()

    func_alias = _generate_hdf5_dataset_path_to_shape_map_of_ml_dataset_file
    kwargs = {"unnormalized_ml_data_instance_generator": \
              unnormalized_ml_data_instance_generator,
              "ml_data_normalizer": \
              ml_data_normalizer,
              "num_ml_data_instances": \
              1}
    hdf5_dataset_path_to_shape_map = func_alias(**kwargs)

    max_num_ml_data_instances_per_file_update = \
        ml_data_normalizer._max_num_ml_data_instances_per_file_update

    args = (max_num_ml_data_instances_per_file_update,
            total_num_ml_data_instances)
    num_ml_data_instances_in_ml_dataset_buffer = min(*args)
    
    for hdf5_dataset_path in hdf5_dataset_path_to_shape_map:
        hdf5_dataset_shape = \
            hdf5_dataset_path_to_shape_map.get(hdf5_dataset_path, None)
        modified_hdf5_dataset_shape = \
            (hdf5_dataset_shape
             if (hdf5_dataset_shape != None)
             else tuple())

        hdf5_dataset_dtype = \
            ml_data_dict_key_to_dtype_map.get(hdf5_dataset_path, None)
        shape_of_array_to_be_initialized = \
            ((num_ml_data_instances_in_ml_dataset_buffer,)
             + modified_hdf5_dataset_shape[1:])
        ml_dataset_buffer[hdf5_dataset_path] = \
            np.zeros(shape_of_array_to_be_initialized,
                     dtype=hdf5_dataset_dtype)

        _ = (None
             if (hdf5_dataset_shape is not None)
             else ml_dataset_buffer.pop(hdf5_dataset_path))

    return ml_dataset_buffer



def _update_and_flush_buffer_and_return_updated_ml_data_instance_idx(
        ml_data_normalizer,
        unnormalized_ml_data_instance_generator,
        ml_dataset_buffer,
        ml_data_instance_idx,
        total_num_ml_data_instances,
        output_filename):
    max_num_ml_data_instances_per_file_update = \
        ml_data_normalizer._max_num_ml_data_instances_per_file_update

    buffered_ml_data_instance_indices = \
        range(max_num_ml_data_instances_per_file_update)
    
    for buffer_update_count in buffered_ml_data_instance_indices:
        start_time = time.time()
        buffered_ml_data_instance_idx = buffer_update_count

        kwargs = \
            {"num_ml_data_instances": 1}
        ml_data_instances = \
            unnormalized_ml_data_instance_generator._generate(**kwargs)

        func_alias = \
            _store_ml_data_instances_in_respective_buffers
        kwargs = \
            {"ml_data_instances": ml_data_instances,
             "buffered_ml_data_instance_idx": buffered_ml_data_instance_idx,
             "ml_dataset_buffer": ml_dataset_buffer}
        _ = \
            func_alias(**kwargs)

        elapsed_time = time.time() - start_time
        unformatted_msg = ("Finished generating machine learning data instance "
                           "#{}. Time taken to generate instance: {} s.\n")
        msg = unformatted_msg.format(ml_data_instance_idx, elapsed_time)
        print(msg)

        ml_data_instance_idx += 1
        if ml_data_instance_idx == total_num_ml_data_instances:
            break

    _flush_ml_dataset_buffer(buffered_ml_data_instance_idx,
                             ml_data_instance_idx,
                             ml_dataset_buffer,
                             output_filename)
        
    return ml_data_instance_idx
    


def _store_ml_data_instances_in_respective_buffers(
        ml_data_instances, buffered_ml_data_instance_idx, ml_dataset_buffer):
    for key in ml_dataset_buffer:
        num_ml_data_instances = ml_data_instances[key].shape[0]
            
        start_1 = buffered_ml_data_instance_idx
        stop_1 = buffered_ml_data_instance_idx + num_ml_data_instances
        single_dim_slice_1 = slice(start_1, stop_1)

        start_2 = 0
        stop_2 = num_ml_data_instances
        single_dim_slice_2 = slice(start_2, stop_2)
            
        ml_dataset_buffer[key][single_dim_slice_1] = \
            ml_data_instances[key][single_dim_slice_2]

    return None



def _flush_ml_dataset_buffer(buffered_ml_data_instance_idx,
                             ml_data_instance_idx,
                             ml_dataset_buffer,
                             output_filename):
    start_1 = 0
    stop_1 = buffered_ml_data_instance_idx+1
    single_dim_slice_1 = slice(start_1, stop_1)

    start_2 = ml_data_instance_idx - (buffered_ml_data_instance_idx+1)
    stop_2 = ml_data_instance_idx
    single_dim_slice_2 = slice(start_2, stop_2)

    for hdf5_dataset_path in ml_dataset_buffer:
        hdf5_datasubset = \
            ml_dataset_buffer[hdf5_dataset_path][single_dim_slice_1]

        kwargs = {"filename": output_filename,
                  "path_in_file": hdf5_dataset_path}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)
        
        kwargs = {"dataset_id": hdf5_dataset_id, "read_only": False}
        hdf5_dataset = h5pywrappers.dataset.load(**kwargs)
        hdf5_dataset[single_dim_slice_2] = hdf5_datasubset
        hdf5_dataset.file.close()

    return None



def _print_generate_and_save_ml_dataset_end_msg(start_time, output_filename):
    elapsed_time = time.time() - start_time
    unformatted_msg = ("\n\nFinished generating machine learning dataset and "
                       "saving it to the HDF5 file ``'{}'``. Time taken to "
                       "generate and save the machine learning dataset: {} "
                       "s.\n\n\n")
    msg = unformatted_msg.format(output_filename, elapsed_time)
    print(msg)

    return None



def _check_and_convert_combine_ml_dataset_files_params(params):
    params = params.copy()

    func_alias = \
        _check_and_convert_input_ml_dataset_filenames
    params["input_ml_dataset_filenames"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_output_ml_dataset_filename
    params["output_ml_dataset_filename"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_rm_input_ml_dataset_files
    params["rm_input_ml_dataset_files"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_max_num_ml_data_instances_per_file_update
    params["max_num_ml_data_instances_per_file_update"] = \
        func_alias(params)

    return params



def _check_and_convert_input_ml_dataset_filenames(params):
    obj_name = \
        "input_ml_dataset_filenames"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    input_ml_dataset_filenames = \
        czekitout.convert.to_tuple_of_strs(**kwargs)

    current_func_name = "_check_and_convert_input_ml_dataset_filenames"

    num_datasets = len(input_ml_dataset_filenames)
    if num_datasets < 1:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    return input_ml_dataset_filenames



def _check_and_convert_output_ml_dataset_filename(params):
    obj_name = \
        "output_ml_dataset_filename"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    output_ml_dataset_filename = \
        czekitout.convert.to_str_from_str_like(**kwargs)
    
    return output_ml_dataset_filename



def _check_and_convert_rm_input_ml_dataset_files(params):
    obj_name = "rm_input_ml_dataset_files"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    rm_input_ml_dataset_files = czekitout.convert.to_bool(**kwargs)
    
    return rm_input_ml_dataset_files



_default_output_ml_dataset_filename = "ml_dataset.h5"
_default_rm_input_ml_dataset_files = False



def _combine_ml_dataset_files(input_ml_dataset_filenames,
                              output_ml_dataset_filename,
                              ml_data_type_validator,
                              ml_data_shape_analyzer,
                              axes_labels_of_hdf5_datasets_of_ml_dataset_file,
                              ml_data_renormalizer,
                              rm_input_ml_dataset_files,
                              start_time):
    kwargs = {"input_ml_dataset_filenames": input_ml_dataset_filenames,
              "output_ml_dataset_filename": output_ml_dataset_filename}
    partial_msg = _generate_partial_msg_of_combine_ml_dataset_files(**kwargs)

    _print_combine_ml_dataset_files_starting_msg(partial_msg)

    current_func_name = "_combine_ml_dataset_files"

    try:
        method_name = ("_check_dtypes_of_hdf5_datasets"
                             "_of_ml_dataset_files")
        method_alias = getattr(ml_data_type_validator, method_name)
        method_alias(paths_to_ml_datasets=input_ml_dataset_filenames)

        func_name = ("_initialize_output_file"
                     "_to_which_to_copy_combined_contents_of_ml_datasets")
        func_alias = globals()[func_name]
        kwargs = {"ml_data_shape_analyzer": \
                  ml_data_shape_analyzer,
                  "input_ml_dataset_filenames": \
                  input_ml_dataset_filenames,
                  "ml_data_type_validator": \
                  ml_data_type_validator,
                  "output_ml_dataset_filename": \
                  output_ml_dataset_filename,
                  "axes_labels_of_hdf5_datasets_of_ml_dataset_file": \
                  axes_labels_of_hdf5_datasets_of_ml_dataset_file}
        func_alias(**kwargs)

        method_name = ("_copy_and_renormalize_all_input_data"
                             "_and_save_to_output_file")
        method_alias = getattr(ml_data_renormalizer, method_name)
        method_alias(output_ml_dataset_filename, rm_input_ml_dataset_files)
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(partial_msg)
        raise IOError(err_msg)

    _print_combine_ml_dataset_files_end_msg(start_time, partial_msg)
    
    return None



def _generate_partial_msg_of_combine_ml_dataset_files(
        input_ml_dataset_filenames, output_ml_dataset_filename):
    num_placeholders = len(input_ml_dataset_filenames) + 1
    unformatted_partial_msg = ("the contents of the machine learning dataset "
                               "files "
                               + ("``'{}'``, "*(num_placeholders-2))
                               + "and ``'{}'`` into a new machine learning "
                               "dataset file ``'{}'``")
    partial_msg = unformatted_partial_msg.format(*input_ml_dataset_filenames,
                                                 output_ml_dataset_filename)

    return partial_msg



def _print_combine_ml_dataset_files_starting_msg(partial_msg):
    msg = "Combining " + partial_msg + "...\n"
    print(msg)

    return None



def _initialize_output_file_to_which_to_copy_combined_contents_of_ml_datasets(
        ml_data_shape_analyzer,
        input_ml_dataset_filenames,
        ml_data_type_validator,
        output_ml_dataset_filename,
        axes_labels_of_hdf5_datasets_of_ml_dataset_file):
    obj_alias = \
        ml_data_shape_analyzer
    method_alias = \
        obj_alias._hdf5_dataset_path_to_shape_map_for_ml_dataset_combo
    hdf5_dataset_path_to_shape_map_of_ml_dataset_file = \
        method_alias(input_ml_dataset_filenames)

    ml_data_dict_key_to_dtype_map = \
        ml_data_type_validator._ml_data_dict_key_to_dtype_map

    func_alias = _initialize_output_file_to_which_to_save_ml_dataset
    kwargs = {"output_filename": \
              output_ml_dataset_filename,
              "hdf5_dataset_path_to_shape_map_of_ml_dataset_file": \
              hdf5_dataset_path_to_shape_map_of_ml_dataset_file,
              "ml_data_dict_key_to_dtype_map": \
              ml_data_dict_key_to_dtype_map,
              "axes_labels_of_hdf5_datasets_of_ml_dataset_file": \
              axes_labels_of_hdf5_datasets_of_ml_dataset_file}
    func_alias(**kwargs)

    return None



def _print_combine_ml_dataset_files_end_msg(start_time, partial_msg):
    elapsed_time = time.time() - start_time
    unformatted_msg = ("Finished combining {}. Time taken to combine the "
                       "contents of the input machine learning dataset files "
                       "into one file: {} s.\n\n\n")
    msg = unformatted_msg.format(partial_msg, elapsed_time)
    print(msg)

    return None



def _check_and_convert_split_ml_dataset_file_params(params):
    params = params.copy()

    func_alias = \
        _check_and_convert_input_ml_dataset_filename
    params["input_ml_dataset_filename"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_output_ml_dataset_filename_1
    params["output_ml_dataset_filename_1"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_output_ml_dataset_filename_2
    params["output_ml_dataset_filename_2"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_output_ml_dataset_filename_3
    params["output_ml_dataset_filename_3"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_split_ratio
    params["split_ratio"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_enable_shuffling
    params["enable_shuffling"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_rng_seed
    params["rng_seed"] = \
        func_alias(params)

    func_alias = \
        _check_and_convert_rm_input_ml_dataset_file
    params["rm_input_ml_dataset_file"] = \
        func_alias(params)
    
    func_alias = \
        _check_and_convert_max_num_ml_data_instances_per_file_update
    params["max_num_ml_data_instances_per_file_update"] = \
        func_alias(params)

    return params



def _check_and_convert_input_ml_dataset_filename(params):
    obj_name = \
        "input_ml_dataset_filename"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    input_ml_dataset_filename = \
        czekitout.convert.to_str_from_str_like(**kwargs)
    
    return input_ml_dataset_filename



def _check_and_convert_output_ml_dataset_filename_1(params):
    obj_name = \
        "output_ml_dataset_filename_1"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    output_ml_dataset_filename_1 = \
        czekitout.convert.to_str_from_str_like(**kwargs)
    
    return output_ml_dataset_filename_1



def _check_and_convert_output_ml_dataset_filename_2(params):
    obj_name = \
        "output_ml_dataset_filename_2"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    output_ml_dataset_filename_2 = \
        czekitout.convert.to_str_from_str_like(**kwargs)

    output_ml_dataset_filename_1 = \
        _check_and_convert_output_ml_dataset_filename_1(params)

    current_func_name = "_check_and_convert_output_ml_dataset_filename_2"

    path_1 = pathlib.Path(output_ml_dataset_filename_1).resolve()
    path_2 = pathlib.Path(output_ml_dataset_filename_2).resolve()
    if path_1 == path_2:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    return output_ml_dataset_filename_2



def _check_and_convert_output_ml_dataset_filename_3(params):
    obj_name = \
        "output_ml_dataset_filename_3"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    output_ml_dataset_filename_3 = \
        czekitout.convert.to_str_from_str_like(**kwargs)

    output_ml_dataset_filename_1 = \
        _check_and_convert_output_ml_dataset_filename_1(params)
    output_ml_dataset_filename_2 = \
        _check_and_convert_output_ml_dataset_filename_2(params)

    current_func_name = "_check_and_convert_output_ml_dataset_filename_3"

    path_1 = pathlib.Path(output_ml_dataset_filename_1).resolve()
    path_2 = pathlib.Path(output_ml_dataset_filename_2).resolve()
    path_3 = pathlib.Path(output_ml_dataset_filename_3).resolve()
    if (path_1 == path_3) or (path_2 == path_3):
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    return output_ml_dataset_filename_3



def _check_and_convert_split_ratio(params):
    obj_name = "split_ratio"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    split_ratio = czekitout.convert.to_tuple_of_nonnegative_floats(**kwargs)

    current_func_name = "_check_and_convert_split_ratio"

    if (len(split_ratio) != 3) or (sum(split_ratio) == 0):
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    return split_ratio



def _check_and_convert_enable_shuffling(params):
    obj_name = "enable_shuffling"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    enable_shuffling = czekitout.convert.to_bool(**kwargs)
    
    return enable_shuffling



def _check_and_convert_rng_seed(params):
    obj_name = "rng_seed"

    module_alias = fakecbed.discretized
    cls_alias = module_alias.CBEDPattern
    func_alias = cls_alias.get_validation_and_conversion_funcs()[obj_name]
    rng_seed = func_alias(params)

    return rng_seed



def _pre_serialize_rng_seed(rng_seed):
    obj_to_pre_serialize = rng_seed
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_rng_seed(serializable_rep):
    rng_seed = serializable_rep
    
    return rng_seed



def _check_and_convert_rm_input_ml_dataset_file(params):
    obj_name = "rm_input_ml_dataset_file"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    rm_input_ml_dataset_file = czekitout.convert.to_bool(**kwargs)
    
    return rm_input_ml_dataset_file



_default_output_ml_dataset_filename_1 = "ml_dataset_for_training.h5"
_default_output_ml_dataset_filename_2 = "ml_dataset_for_validation.h5"
_default_output_ml_dataset_filename_3 = "ml_dataset_for_testing.h5"
_default_split_ratio = (80, 10, 10)
_default_enable_shuffling = False
_default_rng_seed = None
_default_rm_input_ml_dataset_file = False



def _split_ml_dataset_file(ml_data_splitter,
                           output_ml_dataset_filenames,
                           ml_data_type_validator,
                           ml_data_shape_analyzer,
                           axes_labels_of_hdf5_datasets_of_ml_dataset_file,
                           rm_input_ml_dataset_file,
                           start_time):
    kwargs = {"ml_data_splitter": ml_data_splitter,
              "output_ml_dataset_filenames": output_ml_dataset_filenames}
    partial_msg = _generate_partial_msg_of_split_ml_dataset_file(**kwargs)    

    _print_split_ml_dataset_file_starting_msg(partial_msg)

    input_ml_dataset_filename = ml_data_splitter._input_ml_dataset_filename
    current_func_name = "_split_ml_dataset_file"

    try:
        method_name = "_check_dtypes_of_hdf5_datasets_of_ml_dataset_file"
        method_alias = getattr(ml_data_type_validator, method_name)
        method_alias(path_to_ml_dataset=input_ml_dataset_filename)
        
        func_name = ("_initialize_output_files_to_which_to_copy_contents"
                     "_of_split_ml_dataset")
        func_alias = globals()[func_name]
        kwargs = {**kwargs,
                  "ml_data_shape_analyzer": \
                  ml_data_shape_analyzer,
                  "input_ml_dataset_filename": \
                  input_ml_dataset_filename,
                  "ml_data_type_validator": \
                  ml_data_type_validator,
                  "axes_labels_of_hdf5_datasets_of_ml_dataset_file": \
                  axes_labels_of_hdf5_datasets_of_ml_dataset_file}
        func_alias(**kwargs)

        method_name = ("_copy_and_split_input_data"
                       "_and_save_to_output_files")
        method_alias = getattr(ml_data_splitter, method_name)
        method_alias(output_ml_dataset_filenames, rm_input_ml_dataset_file)
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(partial_msg)
        raise IOError(err_msg)

    _print_split_ml_dataset_file_end_msg(start_time, partial_msg)

    return None



def _generate_partial_msg_of_split_ml_dataset_file(ml_data_splitter,
                                                   output_ml_dataset_filenames):
    input_ml_dataset_filename = ml_data_splitter._input_ml_dataset_filename
    adjusted_split_ratio = ml_data_splitter._adjusted_split_ratio

    subset_of_output_ml_dataset_filenames = tuple()
    num_output_ml_datasets = 0
    
    for output_ml_dataset_idx, _ in enumerate(output_ml_dataset_filenames):
        if adjusted_split_ratio[output_ml_dataset_idx] > 0:
            output_ml_dataset_filename = \
                output_ml_dataset_filenames[output_ml_dataset_idx]
            subset_of_output_ml_dataset_filenames += \
                (output_ml_dataset_filename,)
            num_output_ml_datasets += \
                1
    
    unformatted_partial_msg = ("the machine learning dataset file {} into {} "
                               "smaller machine learning dataset files"
                               + ("``'{}'``, "*(num_output_ml_datasets-1))
                               + "and ``'{}'``")
    args = (input_ml_dataset_filename,
            num_output_ml_datasets,
            *subset_of_output_ml_dataset_filenames)
    partial_msg = unformatted_partial_msg.format(*args)

    return partial_msg



def _print_split_ml_dataset_file_starting_msg(partial_msg):
    msg = "Splitting " + partial_msg + "...\n"
    print(msg)

    return None



def _initialize_output_files_to_which_to_copy_contents_of_split_ml_dataset(
        ml_data_splitter,
        ml_data_shape_analyzer,
        input_ml_dataset_filename,
        ml_data_type_validator,
        output_ml_dataset_filenames,
        axes_labels_of_hdf5_datasets_of_ml_dataset_file):
    adjusted_split_ratio = ml_data_splitter._adjusted_split_ratio

    obj_alias = \
        ml_data_shape_analyzer
    method_alias = \
        obj_alias._hdf5_dataset_path_to_shape_maps_for_ml_dataset_split
    kwargs = \
        {"input_ml_dataset_filename": input_ml_dataset_filename,
         "split_ratio": ml_data_splitter._adjusted_split_ratio}
    hdf5_dataset_path_to_shape_maps_of_output_ml_dataset_files = \
        method_alias(**kwargs)

    ml_data_dict_key_to_dtype_map = \
        ml_data_type_validator._ml_data_dict_key_to_dtype_map

    for output_ml_dataset_idx, _ in enumerate(output_ml_dataset_filenames):
        if adjusted_split_ratio[output_ml_dataset_idx] > 0:
            output_ml_dataset_filename = \
                output_ml_dataset_filenames[output_ml_dataset_idx]

            hdf5_dataset_path_to_shape_maps = \
                hdf5_dataset_path_to_shape_maps_of_output_ml_dataset_files

            func_alias = _initialize_output_file_to_which_to_save_ml_dataset
            kwargs = {"output_filename": \
                      output_ml_dataset_filename,
                      "hdf5_dataset_path_to_shape_map_of_ml_dataset_file": \
                      hdf5_dataset_path_to_shape_maps[output_ml_dataset_idx],
                      "ml_data_dict_key_to_dtype_map": \
                      ml_data_dict_key_to_dtype_map,
                      "axes_labels_of_hdf5_datasets_of_ml_dataset_file": \
                      axes_labels_of_hdf5_datasets_of_ml_dataset_file}
            func_alias(**kwargs)

    return None



def _print_split_ml_dataset_file_end_msg(start_time, partial_msg):
    elapsed_time = time.time() - start_time
    unformatted_msg = ("Finished splitting {}. Time taken to split the "
                       "input machine learning dataset file: {} s.\n\n\n")
    msg = unformatted_msg.format(partial_msg, elapsed_time)
    print(msg)

    return None



def _check_and_convert_ml_data_dict(params):
    params = params.copy()

    obj_name = params["name_of_obj_alias_of_ml_data_dict"]
    kwargs = {"obj": params["ml_data_dict"], "obj_name": obj_name}
    params["ml_data_dict"] = czekitout.convert.to_dict(**kwargs)
    params["ml_data_dict"] = params["ml_data_dict"].copy()

    kwargs = {"ml_data_normalizer": \
              params["ml_data_normalizer"],
              "expected_ml_data_dict_keys": \
              params["expected_ml_data_dict_keys"],
              "ml_data_dict": \
              params["ml_data_dict"],
              "name_of_obj_alias_of_ml_data_dict": \
              params["name_of_obj_alias_of_ml_data_dict"]}
    _check_ml_data_dict_keys(**kwargs)

    kwargs = {"ml_data_dict": \
              params["ml_data_dict"],
              "name_of_obj_alias_of_ml_data_dict": \
              params["name_of_obj_alias_of_ml_data_dict"],
              "target_numerical_data_container_cls": \
              params["target_numerical_data_container_cls"],
              "target_device": \
              params["target_device"]}
    _convert_numerical_data_containers_in_ml_data_dict(**kwargs)

    param_name_subset = ("variable_axis_size_dict",
                         "ml_data_shape_analyzer",
                         "ml_data_dict",
                         "name_of_obj_alias_of_ml_data_dict",
                         "ml_data_type_validator",
                         "normalizable_elems_are_normalized",
                         "ml_data_value_validator")

    kwargs = {name: params[name] for name in param_name_subset}
    _check_dtypes_values_and_shapes_of_ml_data_dict(**kwargs)

    ml_data_dict = params["ml_data_dict"]

    return ml_data_dict



def _check_ml_data_dict_keys(ml_data_normalizer,
                             expected_ml_data_dict_keys,
                             ml_data_dict,
                             name_of_obj_alias_of_ml_data_dict):
    current_func_name = "_check_ml_data_dict_keys"
    
    for key in expected_ml_data_dict_keys:
        if key not in ml_data_dict:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            args = (name_of_obj_alias_of_ml_data_dict, key)
            err_msg = unformatted_err_msg.format(*args)
            raise KeyError(err_msg)

    for key in ml_data_dict:
        if key not in ml_data_normalizer._ml_data_dict_keys:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_2"]
            args = (name_of_obj_alias_of_ml_data_dict, key)
            err_msg = unformatted_err_msg.format(*args)
            raise KeyError(err_msg)

    return None



def _convert_numerical_data_containers_in_ml_data_dict(
        ml_data_dict,
        name_of_obj_alias_of_ml_data_dict,
        target_numerical_data_container_cls,
        target_device):
    for key in ml_data_dict:
        name_of_obj_alias_of_numerical_data_container = \
            (name_of_obj_alias_of_ml_data_dict + "['{}']".format(key))
        kwargs = \
            {"numerical_data_container": \
             ml_data_dict[key],
             "name_of_obj_alias_of_numerical_data_container": \
             name_of_obj_alias_of_numerical_data_container,
            "target_numerical_data_container_cls": \
             target_numerical_data_container_cls,
             "target_device": \
             target_device}
        ml_data_dict[key] = \
            _convert_numerical_data_container(**kwargs)

    return None



def _convert_numerical_data_container(
        numerical_data_container,
        name_of_obj_alias_of_numerical_data_container,
        target_numerical_data_container_cls,
        target_device):
    accepted_types = (torch.Tensor, np.ndarray)
    if not isinstance(numerical_data_container, accepted_types):
        try:
            numpy_array = np.array(numerical_data_container)
            numerical_data_container = numpy_array
        except:
            kwargs = {"obj": numerical_data_container,
                      "obj_name": name_of_obj_alias_of_numerical_data_container,
                      "accepted_types": accepted_types}
            czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    current_func_name = "_convert_numerical_data_container"

    try:
        container_cls = type(numerical_data_container)
        target_container_cls = target_numerical_data_container_cls

        if ((container_cls != target_container_cls)
            and (target_container_cls is not None)):
            numerical_data_container = \
                (torch.from_numpy(numerical_data_container).to(target_device)
                 if (target_container_cls == torch.Tensor)
                 else numerical_data_container.cpu().detach().numpy())
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        format_args = (name_of_obj_alias_of_numerical_data_container,)
        err_msg = unformatted_err_msg.format(*format_args)
        raise TypeError(err_msg)
        
    return numerical_data_container



def _check_dtypes_values_and_shapes_of_ml_data_dict(
        variable_axis_size_dict,
        ml_data_shape_analyzer,
        ml_data_dict,
        name_of_obj_alias_of_ml_data_dict,
        ml_data_type_validator,
        normalizable_elems_are_normalized,
        ml_data_value_validator):
    variable_axis_size_dict_keys = \
        ml_data_shape_analyzer._variable_axis_size_dict_keys
    variable_axis_size_dict = \
        ({key: None for key in variable_axis_size_dict_keys}
         if (variable_axis_size_dict is None)
         else variable_axis_size_dict)

    for key in ml_data_dict:
        data_chunk = ml_data_dict[key]

        kwargs = {"data_chunk": \
                  data_chunk,
                  "key_used_to_get_data_chunk": \
                  key,
                  "name_of_obj_alias_from_which_data_chunk_was_obtained": \
                  name_of_obj_alias_of_ml_data_dict,
                  "obj_alias_from_which_data_chunk_was_obtained": \
                  ml_data_dict}
        ml_data_type_validator._check_dtype_of_data_chunk(**kwargs)

        kwargs["data_chunk_is_expected_to_be_normalized_if_normalizable"] = \
            normalizable_elems_are_normalized
        _ = \
            ml_data_value_validator._check_values_of_data_chunk(**kwargs)

        del kwargs["obj_alias_from_which_data_chunk_was_obtained"]
        del kwargs["data_chunk_is_expected_to_be_normalized_if_normalizable"]
        kwargs["variable_axis_size_dict"] = variable_axis_size_dict
        ml_data_shape_analyzer._check_shape_of_data_chunk(**kwargs)

        del kwargs["name_of_obj_alias_from_which_data_chunk_was_obtained"]
        ml_data_shape_analyzer._update_variable_axis_size_dict(**kwargs)

    kwargs = {"variable_axis_size_dict": \
              variable_axis_size_dict,
              "ml_data_dict": \
              ml_data_dict,
              "name_of_obj_alias_of_ml_data_dict": \
              name_of_obj_alias_of_ml_data_dict}
    ml_data_shape_analyzer._check_variable_axis_size_dict(**kwargs)

    return None



_default_ml_data_instance_idx = 0



def _check_and_convert_ml_data_instance_idx(params):
    obj_name = "ml_data_instance_idx"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    ml_data_instance_idx = czekitout.convert.to_int(**kwargs)

    ml_dataset = \
        params["ml_dataset"]
    ml_dataset_core_attrs = \
        ml_dataset.get_core_attrs(deep_copy=False)
    path_to_ml_dataset = \
        ml_dataset_core_attrs["path_to_ml_dataset"]
    min_accepted_ml_data_instance_idx = \
        -len(ml_dataset)
    max_accepted_ml_data_instance_idx = \
        -min_accepted_ml_data_instance_idx-1
    
    current_func_name = "_check_and_convert_ml_data_instance_idx"

    if ((ml_data_instance_idx < min_accepted_ml_data_instance_idx)
        or (max_accepted_ml_data_instance_idx < ml_data_instance_idx)):
        partial_err_msg_1 = (" from the ML dataset stored in the file "
                             "``'{}'``".format(path_to_ml_dataset))
        partial_err_msg_2 = ("is the number of ML data instances in the ML "
                             "dataset, which in this case ")
        args = ((obj_name, ml_data_instance_idx)
                + (partial_err_msg_1, obj_name)
                + (partial_err_msg_2, max_accepted_ml_data_instance_idx+1))
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(*args)
        raise ValueError(err_msg)

    return ml_data_instance_idx



def _check_and_convert_normalize_normalizable_elems_in_ml_data_dict_params(
        params):
    original_params = params
    params = params.copy()

    params["check_ml_data_dict_first"] = \
        _check_and_convert_check_ml_data_dict_first(params)
    params["normalization_weights"] = \
        _check_and_convert_normalization_weights(params)
    params["normalization_biases"] = \
        _check_and_convert_normalization_biases(params)

    name_of_obj_alias_of_ml_data_dict = \
        "ml_data_dict"
    ml_data_normalization_weights_and_biases_loader = \
        params["ml_data_normalization_weights_and_biases_loader"]
    ml_data_normalizer = \
        ml_data_normalization_weights_and_biases_loader._ml_data_normalizer
    ml_data_value_validator = \
        ml_data_normalization_weights_and_biases_loader._ml_data_value_validator

    param_subset = \
        {"name_of_obj_alias_of_ml_data_dict": name_of_obj_alias_of_ml_data_dict,
         "ml_data_dict": params[name_of_obj_alias_of_ml_data_dict],
         "expected_ml_data_dict_keys": tuple(),
         "ml_data_normalizer": ml_data_normalizer,
         "target_numerical_data_container_cls": None,
         "target_device": None,
         "variable_axis_size_dict": params.get("variable_axis_size_dict", None),
         "normalizable_elems_are_normalized": False,
         "ml_data_value_validator": ml_data_value_validator}
    
    for key in param_subset:
        params[key] = param_subset[key]

    ml_data_dict_is_to_be_checked_first = params["check_ml_data_dict_first"]
    if ml_data_dict_is_to_be_checked_first:
        params["ml_data_dict"] = _check_and_convert_ml_data_dict(params)

    for key in params["ml_data_dict"]:
        original_params["ml_data_dict"][key] = params["ml_data_dict"][key]
    params["ml_data_dict"] = original_params["ml_data_dict"]
    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]

    return params



_default_check_ml_data_dict_first = True



def _check_and_convert_check_ml_data_dict_first(params):
    obj_name = "check_ml_data_dict_first"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    check_ml_data_dict_first = czekitout.convert.to_bool(**kwargs)

    return check_ml_data_dict_first



def _normalize_normalizable_elems_in_ml_data_dict(ml_data_dict,
                                                  normalization_weights,
                                                  normalization_biases):
    for key in ml_data_dict:
        if key in normalization_weights:
            normalization_weight = normalization_weights[key]
            normalization_bias = normalization_biases[key]
            ml_data_dict[key] = (normalization_weight*ml_data_dict[key]
                                 + normalization_bias).clip(min=0, max=1)

    return None



def _check_and_convert_unnormalize_normalizable_elems_in_ml_data_dict_params(
        params):
    original_params = params
    params = params.copy()

    params["check_ml_data_dict_first"] = \
        _check_and_convert_check_ml_data_dict_first(params)
    params["normalization_weights"] = \
        _check_and_convert_normalization_weights(params)
    params["normalization_biases"] = \
        _check_and_convert_normalization_biases(params)

    name_of_obj_alias_of_ml_data_dict = \
        "ml_data_dict"
    ml_data_normalization_weights_and_biases_loader = \
        params["ml_data_normalization_weights_and_biases_loader"]
    ml_data_normalizer = \
        ml_data_normalization_weights_and_biases_loader._ml_data_normalizer
    ml_data_value_validator = \
        ml_data_normalization_weights_and_biases_loader._ml_data_value_validator

    param_subset = \
        {"name_of_obj_alias_of_ml_data_dict": name_of_obj_alias_of_ml_data_dict,
         "ml_data_dict": params[name_of_obj_alias_of_ml_data_dict],
         "expected_ml_data_dict_keys": tuple(),
         "ml_data_normalizer": ml_data_normalizer,
         "target_numerical_data_container_cls": None,
         "target_device": None,
         "variable_axis_size_dict": params.get("variable_axis_size_dict", None),
         "normalizable_elems_are_normalized": True,
         "ml_data_value_validator": ml_data_value_validator}
    
    for key in param_subset:
        params[key] = param_subset[key]

    ml_data_dict_is_to_be_checked_first = params["check_ml_data_dict_first"]
    if ml_data_dict_is_to_be_checked_first:
        params["ml_data_dict"] = _check_and_convert_ml_data_dict(params)

    for key in params["ml_data_dict"]:
        original_params["ml_data_dict"][key] = params["ml_data_dict"][key]
    params["ml_data_dict"] = original_params["ml_data_dict"]
    for key in tuple(params.keys()):
        if key not in original_params:
            del params[key]

    return params



def _unnormalize_normalizable_elems_in_ml_data_dict(ml_data_dict,
                                                    normalization_weights,
                                                    normalization_biases):
    for key in ml_data_dict:
        if key in normalization_weights:
            normalization_weight = normalization_weights[key]
            normalization_bias = normalization_biases[key]
            ml_data_dict[key] = ((ml_data_dict[key]-normalization_bias)
                                 / normalization_weight)

    return None



class _MLDataDecoder():
    def __init__(self,
                 ml_data_dict_elem_decoders,
                 ml_data_dict_elem_decoding_order,
                 normalization_weights,
                 normalization_biases):
        self._ml_data_dict_elem_decoders = \
            ml_data_dict_elem_decoders
        self._ml_data_dict_elem_decoding_order = \
            ml_data_dict_elem_decoding_order
        self._normalization_weights = \
            normalization_weights
        self._normalization_biases = \
            normalization_biases

        return None



    def _decode(self, ml_data_dict):
        decoding_is_required = self._decoding_is_required(ml_data_dict)

        ml_data_dict_before_decoding = (ml_data_dict.copy()
                                        if decoding_is_required
                                        else ml_data_dict)

        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": self._normalization_weights,
                  "normalization_biases": self._normalization_biases}
        _ = (_unnormalize_normalizable_elems_in_ml_data_dict(**kwargs)
             if decoding_is_required
             else None)

        names_of_decodable_elems = \
            set(self._ml_data_dict_elem_decoding_order)
        keys_in_ml_data_dict_after_decoding = \
            set(ml_data_dict.keys()).union(names_of_decodable_elems)

        for key in keys_in_ml_data_dict_after_decoding:
            ml_data_dict_elem_decoder = \
                self._ml_data_dict_elem_decoders.get(key, None)
            ml_data_dict[key] = \
                (ml_data_dict_elem_decoder(ml_data_dict)
                 if (key not in ml_data_dict)
                 else ml_data_dict[key])

        kwargs = {"ml_data_dict": ml_data_dict,
                  "normalization_weights": self._normalization_weights,
                  "normalization_biases": self._normalization_biases}
        _ = (_normalize_normalizable_elems_in_ml_data_dict(**kwargs)
             if decoding_is_required
             else None)

        for key in ml_data_dict_before_decoding:
            ml_data_dict[key] = ml_data_dict_before_decoding[key]

        return None



    def _decoding_is_required(self, ml_data_dict):
        result = (not (set(self._ml_data_dict_elem_decoding_order)
                       <=
                       set(ml_data_dict.keys())))

        return result



def _get_device(device_name):
    device_name = (("cuda" if torch.cuda.is_available() else "cpu")
                   if (device_name is None)
                   else device_name)

    device = torch.device(device_name)

    return device



def _get_device_name(device):
    device_name = (device.type
                   + (device.index != None)*(":{}".format(device.index)))

    return device_name



class _TorchMLDataset(torch.utils.data.Dataset):
    def __init__(self,
                 path_to_ml_dataset,
                 ml_data_normalization_weights_and_biases_loader,
                 ml_data_type_validator,
                 ml_data_shape_analyzer,
                 entire_ml_dataset_is_to_be_cached,
                 ml_data_values_are_to_be_checked,
                 ml_data_dict_elem_decoders,
                 ml_data_dict_elem_decoding_order):
        self._path_to_ml_dataset = path_to_ml_dataset

        obj_alias = ml_data_normalization_weights_and_biases_loader
        ml_data_normalizer = obj_alias._ml_data_normalizer
        ml_data_value_validator = obj_alias._ml_data_value_validator

        self._ml_data_dict_keys = ml_data_normalizer._ml_data_dict_keys

        kwargs = \
            {"ml_data_normalizer": ml_data_normalizer}
        self._max_num_ml_data_instances_per_chunk = \
            self._calc_max_num_ml_data_instances_per_chunk(**kwargs)
        self._num_ml_data_instances_in_ml_dataset = \
            self._calc_num_ml_data_instances_in_ml_dataset(**kwargs)

        self._check_ml_dataset_file(ml_data_type_validator,
                                    ml_data_shape_analyzer,
                                    entire_ml_dataset_is_to_be_cached,
                                    ml_data_values_are_to_be_checked,
                                    ml_data_value_validator)

        if entire_ml_dataset_is_to_be_cached:
            kwargs = {"ml_data_values_are_to_be_checked": \
                      ml_data_values_are_to_be_checked,
                      "ml_data_value_validator": \
                      ml_data_value_validator}
            self._load_and_cache_entire_ml_dataset(**kwargs)

        self._entire_ml_dataset_is_loaded_and_cached = \
            entire_ml_dataset_is_to_be_cached

        kwargs = {"ml_data_normalization_weights_and_biases_loader": \
                  ml_data_normalization_weights_and_biases_loader,
                  "ml_data_dict_elem_decoders": \
                  ml_data_dict_elem_decoders,
                  "ml_data_dict_elem_decoding_order": \
                  ml_data_dict_elem_decoding_order}
        self._ml_data_decoder = self._generate_ml_data_decoder(**kwargs)

        return None



    def _calc_max_num_ml_data_instances_per_chunk(self, ml_data_normalizer):
        max_num_ml_data_instances_per_file_update = \
            ml_data_normalizer._max_num_ml_data_instances_per_file_update

        if max_num_ml_data_instances_per_file_update < np.inf:
            max_num_ml_data_instances_per_chunk = \
                max_num_ml_data_instances_per_file_update
        else:
            kwargs = \
                {"ml_data_normalizer": ml_data_normalizer}
            num_ml_data_instances_in_ml_dataset = \
                self._calc_num_ml_data_instances_in_ml_dataset(**kwargs)
            max_num_ml_data_instances_per_chunk = \
                num_ml_data_instances_in_ml_dataset

        return max_num_ml_data_instances_per_chunk



    def _calc_num_ml_data_instances_in_ml_dataset(self, ml_data_normalizer):
        kwargs = \
            {"ml_data_normalizer": ml_data_normalizer,
             "input_ml_dataset_filename": self._path_to_ml_dataset}
        num_ml_data_instances_in_ml_dataset = \
            _calc_num_ml_data_instances_in_input_ml_dataset(**kwargs)

        return num_ml_data_instances_in_ml_dataset



    def _check_ml_dataset_file(self,
                               ml_data_type_validator,
                               ml_data_shape_analyzer,
                               entire_ml_dataset_is_to_be_cached,
                               ml_data_values_are_to_be_checked,
                               ml_data_value_validator):
        obj_alias = \
            ml_data_type_validator
        method_alias = \
            obj_alias._check_dtypes_of_hdf5_datasets_of_ml_dataset_file
        _ = \
            method_alias(path_to_ml_dataset=self._path_to_ml_dataset)

        obj_alias = \
            ml_data_shape_analyzer
        method_alias = \
            obj_alias._hdf5_dataset_path_to_shape_map_of_ml_dataset_file
        _ = \
            method_alias(path_to_ml_dataset=self._path_to_ml_dataset)

        entire_ml_dataset_is_not_to_be_loaded_and_cached = \
            (not entire_ml_dataset_is_to_be_cached)

        if (ml_data_values_are_to_be_checked
            and entire_ml_dataset_is_not_to_be_loaded_and_cached):
            obj_alias = \
                ml_data_value_validator
            method_alias = \
                obj_alias._check_values_of_hdf5_datasets_of_ml_dataset_file
            kwargs = \
                {"path_to_ml_dataset": \
                 self._path_to_ml_dataset,
                 "max_num_ml_data_instances_per_chunk": \
                 self._max_num_ml_data_instances_per_chunk}
            _ = \
                method_alias(**kwargs)

        return None



    def _load_and_cache_entire_ml_dataset(self,
                                          ml_data_values_are_to_be_checked,
                                          ml_data_value_validator):
        self._ml_data_instances = dict()
        
        for key in self._ml_data_dict_keys:
            hdf5_dataset_path = key
            kwargs = {"filename": self._path_to_ml_dataset,
                      "path_in_file": hdf5_dataset_path}
            hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

            kwargs = {"dataset_id": hdf5_dataset_id, "read_only": True}
            hdf5_dataset = h5pywrappers.dataset.load(**kwargs)

            hdf5_datasubset = (hdf5_dataset[:]
                               if (hdf5_dataset.shape is not None)
                               else None)

            if (ml_data_values_are_to_be_checked
                and (hdf5_datasubset is not None)):
                method_name = ("_check_values_of_hdf5_datasubset_of_ml_dataset"
                               "_file")
                method_alias = getattr(ml_data_value_validator, method_name)
                method_alias(hdf5_dataset, hdf5_datasubset)

            hdf5_dataset.file.close()

            self._ml_data_instances[key] = torch.from_numpy(hdf5_datasubset)

        return None



    def _generate_ml_data_decoder(
            self,
            ml_data_normalization_weights_and_biases_loader,
            ml_data_dict_elem_decoders,
            ml_data_dict_elem_decoding_order):
        kwargs = \
            {"path_to_ml_dataset": self._path_to_ml_dataset}
        normalization_weights, normalization_biases = \
            ml_data_normalization_weights_and_biases_loader._load(**kwargs)

        ml_data_decoder = _MLDataDecoder(ml_data_dict_elem_decoders,
                                         ml_data_dict_elem_decoding_order,
                                         normalization_weights,
                                         normalization_biases)

        return ml_data_decoder



    def __len__(self):
        result = self._num_ml_data_instances_in_ml_dataset
        
        return result



    def __getitem__(self, item_idx):
        item = dict()

        ml_data_dict_elem_decoding_order = \
            self._ml_data_decoder._ml_data_dict_elem_decoding_order
        entire_ml_dataset_is_not_loaded_and_cached = \
            (not self._entire_ml_dataset_is_loaded_and_cached)
        
        if entire_ml_dataset_is_not_loaded_and_cached:
            hdf5_file = h5py.File(self._path_to_ml_dataset, "r")

        names_of_decodable_elems = \
            (key
             for key in self._ml_data_dict_keys
             if key not in ml_data_dict_elem_decoding_order)

        ml_data_instance_idx = item_idx

        for key in names_of_decodable_elems:
            if self._entire_ml_dataset_is_loaded_and_cached:
                ml_data_instances = \
                    self._ml_data_instances
                numerical_data_container = \
                    ml_data_instances[key]
                item[key] = \
                    numerical_data_container[ml_data_instance_idx]
            else:
                hdf5_dataset_path = \
                    key
                hdf5_datasubset = \
                    hdf5_file[hdf5_dataset_path][ml_data_instance_idx]
                item[key] = \
                    torch.from_numpy(np.asarray(hdf5_datasubset))

        if entire_ml_dataset_is_not_loaded_and_cached:
            hdf5_file.close()

        return item



    def _unnormalize_ml_data_dict(self, ml_data_dict):
        normalization_weights = self._ml_data_decoder._normalization_weights
        normalization_biases = self._ml_data_decoder._normalization_biases

        _unnormalize_normalizable_elems_in_ml_data_dict(ml_data_dict,
                                                        normalization_weights,
                                                        normalization_biases)

        return None



    def _get_ml_data_instances(self,
                               device_name,
                               single_dim_slice,
                               decode,
                               unnormalize_normalizable_elems):
        ml_data_instance_count = 0

        device = _get_device(device_name)
        
        for ml_data_instance_idx in single_dim_slice:
            item = self.__getitem__(item_idx=ml_data_instance_idx)
            ml_data_dict = {key: torch.unsqueeze(item[key], dim=0).to(device)
                            for key
                            in item}
            ml_data_dict_containing_a_single_ml_data_instance = ml_data_dict

            if ml_data_instance_count == 0:
                kwargs = {"ml_data_dict_containing_a_single_ml_data_instance": \
                          ml_data_dict_containing_a_single_ml_data_instance,
                          "single_dim_slice": \
                          single_dim_slice}
                ml_data_instances = self._initialize_ml_data_instances(**kwargs)

            for key in ml_data_instances:
                ml_data_instances[key][ml_data_instance_count] = \
                    ml_data_dict_containing_a_single_ml_data_instance[key][0]

            ml_data_instance_count += 1

        normalizable_elems_are_to_be_unnormalize = \
            unnormalize_normalizable_elems
        ml_data_instances_is_to_be_decoded = \
            decode

        if ml_data_instances_is_to_be_decoded:
            self._ml_data_decoder._decode(ml_data_dict=ml_data_instances)
        if normalizable_elems_are_to_be_unnormalize:
            self._unnormalize_ml_data_dict(ml_data_dict=ml_data_instances)

        return ml_data_instances



    def _initialize_ml_data_instances(
            self,
            ml_data_dict_containing_a_single_ml_data_instance,
            single_dim_slice):
        ml_data_instances = dict()
        for key in ml_data_dict_containing_a_single_ml_data_instance:
            data_chunk = ml_data_dict_containing_a_single_ml_data_instance[key]
            zero_array_shape = ((len(single_dim_slice),)
                                + data_chunk.shape[1:])
            zero_array = torch.zeros(zero_array_shape,
                                     dtype=data_chunk.dtype,
                                     device=data_chunk.device)
            ml_data_instances[key] = zero_array

        return ml_data_instances



def _check_and_convert_path_to_ml_dataset(params):
    obj_name = "path_to_ml_dataset"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    path_to_ml_dataset = czekitout.convert.to_str_from_str_like(**kwargs)
    
    return path_to_ml_dataset



def _pre_serialize_path_to_ml_dataset(path_to_ml_dataset):
    obj_to_pre_serialize = path_to_ml_dataset
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_path_to_ml_dataset(serializable_rep):
    path_to_ml_dataset = serializable_rep
    
    return path_to_ml_dataset



def _check_and_convert_entire_ml_dataset_is_to_be_cached(params):
    obj_name = "entire_ml_dataset_is_to_be_cached"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    entire_ml_dataset_is_to_be_cached = czekitout.convert.to_bool(**kwargs)
    
    return entire_ml_dataset_is_to_be_cached



def _pre_serialize_entire_ml_dataset_is_to_be_cached(
        entire_ml_dataset_is_to_be_cached):
    obj_to_pre_serialize = entire_ml_dataset_is_to_be_cached
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_entire_ml_dataset_is_to_be_cached(serializable_rep):
    entire_ml_dataset_is_to_be_cached = serializable_rep
    
    return entire_ml_dataset_is_to_be_cached



def _check_and_convert_ml_data_values_are_to_be_checked(params):
    obj_name = "ml_data_values_are_to_be_checked"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    ml_data_values_are_to_be_checked = czekitout.convert.to_bool(**kwargs)
    
    return ml_data_values_are_to_be_checked



def _pre_serialize_ml_data_values_are_to_be_checked(
        ml_data_values_are_to_be_checked):
    obj_to_pre_serialize = ml_data_values_are_to_be_checked
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_ml_data_values_are_to_be_checked(serializable_rep):
    ml_data_values_are_to_be_checked = serializable_rep
    
    return ml_data_values_are_to_be_checked



def _check_and_convert_max_num_ml_data_instances_per_chunk(params):
    obj_name = "max_num_ml_data_instances_per_chunk"
    obj = params[obj_name]

    if obj == float("inf"):
        max_num_ml_data_instances_per_chunk = \
            obj
    else:
        kwargs = \
            {"obj": obj, "obj_name": obj_name}
        max_num_ml_data_instances_per_chunk = \
            czekitout.convert.to_positive_int(**kwargs)

    return max_num_ml_data_instances_per_chunk



def _pre_serialize_max_num_ml_data_instances_per_chunk(
        max_num_ml_data_instances_per_chunk):
    obj_to_pre_serialize = max_num_ml_data_instances_per_chunk
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_max_num_ml_data_instances_per_chunk(serializable_rep):
    max_num_ml_data_instances_per_chunk = serializable_rep
    
    return max_num_ml_data_instances_per_chunk



def _check_and_convert_device_name(params):
    key = "name_of_obj_alias_of_device_name"
    obj_name = params.get(key, "device_name")
    obj = params[obj_name]

    current_func_name = "_check_and_convert_device_name"

    if obj is None:
        device_name = obj
    else:
        try:
            kwargs = {"obj": obj, "obj_name": obj_name}
            device_name = czekitout.convert.to_str_from_str_like(**kwargs)
            
            torch.device(device_name)
        except:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            err_msg = unformatted_err_msg.format(obj_name)
            raise ValueError(err_msg)

    _ = params.pop(key) if (key in params) else None

    return device_name



def _pre_serialize_device_name(device_name):
    obj_to_pre_serialize = device_name
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_device_name(serializable_rep):
    device_name = serializable_rep
    
    return device_name



def _check_and_convert_decode(params):
    obj_name = "decode"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    decode = czekitout.convert.to_bool(**kwargs)
    
    return decode



def _check_and_convert_unnormalize_normalizable_elems(params):
    obj_name = "unnormalize_normalizable_elems"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    unnormalize_normalizable_elems = czekitout.convert.to_bool(**kwargs)
    
    return unnormalize_normalizable_elems



def _check_and_convert_single_dim_slice(params):
    ml_dataset = \
        params["ml_dataset"]
    ml_dataset_core_attrs = \
        ml_dataset.get_core_attrs(deep_copy=False)
    path_to_ml_dataset = \
        ml_dataset_core_attrs["path_to_ml_dataset"]
    num_ml_data_instances_in_ml_dataset = \
        len(ml_dataset)

    obj_name = "single_dim_slice"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    single_dim_slice = czekitout.convert.to_single_dim_slice(**kwargs)

    ml_data_instance_indices = np.arange(num_ml_data_instances_in_ml_dataset)

    single_dim_slice = \
        ([single_dim_slice]
         if isinstance(single_dim_slice, int)
         else ml_data_instance_indices[single_dim_slice].tolist())

    current_func_name = "_check_and_convert_single_dim_slice"

    for ml_data_instance_idx in single_dim_slice:
        try:
            params["ml_data_instance_idx"] = ml_data_instance_idx
            _check_and_convert_ml_data_instance_idx(params)
        except:
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            args = (path_to_ml_dataset, num_ml_data_instances_in_ml_dataset)
            err_msg = unformatted_err_msg.format(*args)                                                 
            raise ValueError(err_msg)

    return single_dim_slice



_module_alias = \
    emicroml.modelling.optimizers
_default_entire_ml_dataset_is_to_be_cached = \
    False
_default_ml_data_values_are_to_be_checked = \
    False
_default_max_num_ml_data_instances_per_chunk = \
    _default_max_num_ml_data_instances_per_file_update
_default_skip_validation_and_conversion = \
    _module_alias._default_skip_validation_and_conversion
_default_device_name = \
    None
_default_decode = \
    False
_default_unnormalize_normalizable_elems = \
    False
_default_single_dim_slice = \
    0



class _MLDataset(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("path_to_ml_dataset",
                        "entire_ml_dataset_is_to_be_cached",
                        "ml_data_values_are_to_be_checked",
                        "max_num_ml_data_instances_per_chunk")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs

    

    def __init__(self, ctor_params):
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self._clear_torch_ml_dataset()
        self._generate_and_store_normalization_weights_and_biases()
        self._calc_and_store_num_ml_data_instances_in_ml_dataset()

        return None



    def _clear_torch_ml_dataset(self):
        self._torch_ml_dataset = None

        return None



    def _generate_and_store_normalization_weights_and_biases(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        ml_data_normalization_weights_and_biases_loader = \
            self._generate_ml_data_normalization_weights_and_biases_loader()

        kwargs = \
            {"path_to_ml_dataset": self_core_attrs["path_to_ml_dataset"]}
        normalization_weights, normalization_biases = \
            ml_data_normalization_weights_and_biases_loader._load(**kwargs)

        self._normalization_weights = normalization_weights
        self._normalization_biases = normalization_biases

        return None



    def _generate_ml_data_normalization_weights_and_biases_loader(self):
        pass



    def _calc_and_store_num_ml_data_instances_in_ml_dataset(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)
        
        ml_data_normalization_weights_and_biases_loader = \
            self._generate_ml_data_normalization_weights_and_biases_loader()
        ml_data_normalizer = \
            ml_data_normalization_weights_and_biases_loader._ml_data_normalizer

        kwargs = \
            {"ml_data_normalizer": ml_data_normalizer,
             "input_ml_dataset_filename": self_core_attrs["path_to_ml_dataset"]}
        self._num_ml_data_instances_in_ml_dataset = \
            _calc_num_ml_data_instances_in_input_ml_dataset(**kwargs)

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



    def _generate_and_store_torch_ml_dataset(self):
        self._torch_ml_dataset = self._generate_torch_ml_dataset()

        return None



    def _generate_torch_ml_dataset(self):
        pass



    def _get_torch_ml_dataset(self):
        if self._torch_ml_dataset is None:
            self._generate_and_store_torch_ml_dataset()

        torch_ml_dataset = self._torch_ml_dataset

        return torch_ml_dataset



    def __len__(self):
        result = self._num_ml_data_instances_in_ml_dataset
        
        return result



    def __getitem__(self, item_idx):
        torch_ml_dataset = self._get_torch_ml_dataset()
        item = torch_ml_dataset[item_idx]

        return item



    def get_ml_data_instances(self,
                              single_dim_slice=\
                              _default_single_dim_slice,
                              device_name=\
                              _default_device_name,
                              decode=\
                              _default_decode,
                              unnormalize_normalizable_elems=\
                              _default_unnormalize_normalizable_elems):
        r"""Return a subset of the machine learning data instances as a 
        dictionary.

        This method returns a subset of the machine learning (ML) data instances
        of the ML dataset as a dictionary ``ml_data_instances``. Each `dict` key
        in ``ml_data_instances`` is the name of a feature of the subset of the
        ML data instances, and the value corresponding to the `dict` key is a
        PyTorch tensor storing the values of the feature of the subset of ML
        data instances. The name of any feature is a string that stores the HDF5
        path to the HDF5 dataset storing the values of said feature of the ML
        dataset.

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
            This parameter specifies the device to be used to store the data of
            the PyTorch tensors. If ``device_name`` is a string, then it is the
            name of the device to be used, e.g. ``”cuda”`` or ``”cpu”``. If
            ``device_name`` is set to ``None`` and a GPU device is available,
            then a GPU device is to be used. Otherwise, the CPU is used.
        decode : `bool`, optional
            Specifies whether or not the subset of ML data instances are to be
            decoded. Generally speaking, some features of the subset of ML data
            instances may be encoded, implying that the values of said features
            are not currently directly present in whatever representation, be it
            a dictionary representation, an HDF5 file representation, or
            something else. However, the values of these features can be
            decoded, i.e. reconstructed from other features. If ``decode`` is
            set to ``True``, then any features that have been encoded will be
            decoded, and will be present in the dictionary representation of the
            subset of ML data instances. Otherwise, any features that have been
            encoded will not be decoded, and will not be present in the
            dictionary representation.
        unnormalize_normalizable_elems : `bool`, optional
            In :mod:`emicroml`, the non-decoded normalizable features of ML
            datasets stored in HDF5 files are expected to be normalized via a
            linear transformation such that the minimum and maximum values of
            such features lie within the closed interval :math:`[0, 1]`.

            If ``unnormalize_normalizable_elems`` is set to ``True``, then the
            dictionary representation of the subset of ML data instances will
            store the unnormalized values of the normalizable
            features. Otherwise, the dictionary representation of the subset of
            ML data instances will store the normalized values of the
            normalizable features, which lie within the closed interval of
            :math:`[0, 1]`.

        Returns
        -------
        ml_data_instances : `dict`
            The subset of ML data instances, represented as a dictionary. Let
            ``key`` be the `dict` key of ``ml_data_instances`` specifying one of
            the features of the subset of the ML data instances. Let
            ``num_ml_data_instances_in_subset`` be
            ``len(ml_data_instances[key])``. For every nonnegative integer ``n``
            less than ``num_ml_data_instances_in_subset``, then
            ``ml_data_instances[key][n]`` yields the value of the feature
            specified by ``key`` of ML data instance with the index
            ``ml_data_instance_subset_indices[n]``.

        """
        params = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}
        param_name_subset = tuple(params.keys())

        torch_ml_dataset = self._get_torch_ml_dataset()

        params["ml_dataset"] = self

        global_symbol_table = globals()
        for param_name in param_name_subset:
            func_name = "_check_and_convert_" + param_name
            func_alias = global_symbol_table[func_name]
            params[param_name] = func_alias(params)

        kwargs = {param_name: params[param_name]
                  for param_name
                  in param_name_subset}
        ml_data_instances = torch_ml_dataset._get_ml_data_instances(**kwargs)

        return ml_data_instances



    @property
    def normalization_weights(self):
        r"""`dict`: The normalization weights of the normalizable elements.

        Generally speaking, a machine learning (ML) data instance contains one
        or more features, and can be grouped into two different categories:
        normalizable and unnormalizable features.

        In :mod:`emicroml`, the non-decoded normalizable features of ML datasets
        stored in HDF5 files are expected to be normalized via a linear
        transformation such that the minimum and maximum values of such features
        lie within the closed interval :math:`[0, 1]`.

        Let ``unnormalized_values`` be the unnormalized values of a normalizable
        feature in a ML dataset. The normalization is performed by

        .. code-block:: python

            normalized_values = (unnormalized_values*normalization_weight
                                 + normalization_bias)

        where ``normalized_values`` are the normalized values,
        ``normalization_weight`` is a valid normalization weight, and
        ``normalization_bias`` is a valid noramlization bias.

        The current attribute stores the normalization weights of the
        normalizable features in the ML dataset. Each `dict` key in
        ``normalization_weights`` is the name of a normalizable feature, and the
        value corresponding to the `dict` key is the value of the normalization
        weight of said normalizable feature. The name of any feature is a string
        that stores the HDF5 path to the HDF5 dataset storing the values of said
        feature of the ML dataset.

        Note that ``normalization_weights`` should be considered **read-only**.

        """
        result = copy.deepcopy(self._normalization_weights)
        
        return result



    @property
    def normalization_biases(self):
        r"""`dict`: The normalization biases of the normalizable elements.

        Generally speaking, a machine learning (ML) data instance contains one
        or more features, and can be grouped into two different categories:
        normalizable and unnormalizable features.

        In :mod:`emicroml`, the non-decoded normalizable features of ML datasets
        stored in HDF5 files are expected to be normalized via a linear
        transformation such that the minimum and maximum values of such features
        lie within the closed interval :math:`[0, 1]`.

        Let ``unnormalized_values`` be the unnormalized values of a normalizable
        feature in a ML dataset. The normalization is performed by

        .. code-block:: python

            normalized_values = (unnormalized_values*normalization_weight
                                 + normalization_bias)

        where ``normalized_values`` are the normalized values,
        ``normalization_weight`` is a valid normalization weight, and
        ``normalization_bias`` is a valid noramlization bias.

        The current attribute stores the normalization biases of the
        normalizable features in the ML dataset. Each `dict` key in
        ``normalization_biases`` is the name of a normalizable feature, and the
        value corresponding to the `dict` key is the value of the normalization
        bias of said normalizable feature. The name of any feature is a string
        that stores the HDF5 path to the HDF5 dataset storing the values of said
        feature of the ML dataset.

        Note that ``normalization_biases`` should be considered **read-only**.

        """
        result = copy.deepcopy(self._normalization_biases)

        return result



def _check_and_convert_ml_dataset(params):
    key_1 = "name_of_obj_alias_of_ml_dataset"
    obj_name = params.get(key_1, "ml_dataset")
    obj = params[obj_name]

    key_2 = "accepted_nontrivial_cls_of_obj_alias_of_ml_dataset"
    accepted_nontrivial_cls = params[key_2]

    if obj_name in ("ml_validation_dataset", "ml_testing_dataset"):
        accepted_types = (accepted_nontrivial_cls, type(None))
    else:
        key_3 = "ml_testing_dataset"
        accepted_types = ((accepted_nontrivial_cls,)
                          if (params.get(key_3, None) is None)
                          else (accepted_nontrivial_cls, type(None)))

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    if obj is None:
        ml_dataset = None
    else:
        kwargs = obj.get_core_attrs(deep_copy=False)
        ml_dataset = accepted_nontrivial_cls(**kwargs)
        ml_dataset._torch_ml_dataset = obj._torch_ml_dataset

    for key in (key_1, key_2):
        _ = params.pop(key) if (key in params) else None

    return ml_dataset



def _check_and_convert_ml_training_dataset(params):
    params["name_of_obj_alias_of_ml_dataset"] = "ml_training_dataset"
    ml_training_dataset = _check_and_convert_ml_dataset(params)

    return ml_training_dataset



def _pre_serialize_ml_training_dataset(ml_training_dataset):
    serializable_rep = (ml_training_dataset
                        if (ml_training_dataset is None)
                        else ml_training_dataset.pre_serialize())
    
    return serializable_rep



_default_ml_training_dataset = None



def _check_and_convert_ml_validation_dataset(params):
    ml_training_dataset = \
        _check_and_convert_ml_training_dataset(params)

    params["name_of_obj_alias_of_ml_dataset"] = \
        "ml_validation_dataset"
    params["accepted_nontrivial_cls_of_obj_alias_of_ml_dataset"] = \
        type(ml_training_dataset)
    ml_validation_dataset = \
        _check_and_convert_ml_dataset(params)

    current_func_name = "_check_and_convert_ml_validation_dataset"

    if ml_validation_dataset is not None:
        normalization_weights_1 = ml_training_dataset._normalization_weights
        normalization_biases_1 = ml_training_dataset._normalization_biases

        normalization_weights_2 = ml_validation_dataset._normalization_weights
        normalization_biases_2 = ml_validation_dataset._normalization_biases

        tol = _tol_for_comparing_floats

        for key in normalization_weights_1:
            normalization_weight_1 = normalization_weights_1[key]
            normalization_weight_2 = normalization_weights_2[key]

            normalization_bias_1 = normalization_biases_1[key]
            normalization_bias_2 = normalization_biases_2[key]

            if ((abs(normalization_weight_1-normalization_weight_2) > tol)
                or (abs(normalization_bias_1-normalization_bias_2) > tol)):
                err_msg = globals()[current_func_name+"_err_msg_1"]
                raise ValueError(err_msg)

    return ml_validation_dataset



def _pre_serialize_ml_validation_dataset(ml_validation_dataset):
    serializable_rep = (ml_validation_dataset
                        if (ml_validation_dataset is None)
                        else ml_validation_dataset.pre_serialize())
    
    return serializable_rep



_default_ml_validation_dataset = None



def _check_and_convert_ml_testing_dataset(params):
    params["name_of_obj_alias_of_ml_dataset"] = "ml_testing_dataset"
    ml_testing_dataset = _check_and_convert_ml_dataset(params)

    return ml_testing_dataset



def _pre_serialize_ml_testing_dataset(ml_testing_dataset):
    serializable_rep = (ml_testing_dataset
                        if (ml_testing_dataset is None)
                        else ml_testing_dataset.pre_serialize())
    
    return serializable_rep



_default_ml_testing_dataset = None



def _check_and_convert_mini_batch_size(params):
    obj_name = "mini_batch_size"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    mini_batch_size = czekitout.convert.to_positive_int(**kwargs)

    return mini_batch_size



def _pre_serialize_mini_batch_size(mini_batch_size):
    serializable_rep = mini_batch_size
    
    return serializable_rep



def _de_pre_serialize_mini_batch_size(serializable_rep):
    mini_batch_size = serializable_rep
    
    return mini_batch_size



def _check_and_convert_num_data_loader_workers(params):
    obj_name = "num_data_loader_workers"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    num_data_loader_workers = czekitout.convert.to_nonnegative_int(**kwargs)

    return num_data_loader_workers



def _pre_serialize_num_data_loader_workers(num_data_loader_workers):
    serializable_rep = num_data_loader_workers
    
    return serializable_rep



def _de_pre_serialize_num_data_loader_workers(serializable_rep):
    num_data_loader_workers = serializable_rep
    
    return num_data_loader_workers



def _seed_worker(worker_id):
    rng_seed = torch.initial_seed() % 2**32
    np.random.seed(rng_seed)
    random.seed(rng_seed)

    return None



_default_mini_batch_size = 32
_default_num_data_loader_workers = 0



class _MLDatasetManager(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("mini_batch_size",
                        "rng_seed",
                        "num_data_loader_workers")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs



    def __init__(self, ctor_params):
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self._clear_torch_ml_training_dataloader()
        self._clear_torch_ml_validation_dataloader()
        self._clear_torch_ml_testing_dataloader()

        _seed_worker(0)

        self_core_attrs = self.get_core_attrs(deep_copy=False)
        rng_seed = self_core_attrs["rng_seed"]

        rng = np.random.default_rng(rng_seed)
        new_rng_seed = rng.integers(low=0, high=2**32-1).item()
            
        generator = torch.Generator()
        generator.manual_seed(new_rng_seed)
        self._generator = generator

        return None



    def _clear_torch_ml_training_dataloader(self):
        self._torch_ml_training_dataloader = None

        return None



    def _clear_torch_ml_validation_dataloader(self):
        self._torch_ml_validation_dataloader = None

        return None



    def _clear_torch_ml_testing_dataloader(self):
        self._torch_ml_testing_dataloader = None

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



    def _generate_and_store_torch_ml_testing_dataloader(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)
        
        ml_testing_dataset = self_core_attrs["ml_testing_dataset"]

        if ml_testing_dataset is not None:
            mini_batch_size = \
                self_core_attrs["mini_batch_size"]
            num_data_loader_workers = \
                self_core_attrs["num_data_loader_workers"]
            torch_ml_testing_dataset = \
                ml_testing_dataset._get_torch_ml_dataset()
            torch_ml_dataloader_cls = \
                torch.utils.data.DataLoader

            kwargs = {"dataset": torch_ml_testing_dataset,
                      "batch_size": mini_batch_size,
                      "shuffle": False,
                      "num_workers": num_data_loader_workers}
            torch_ml_testing_dataloader = torch_ml_dataloader_cls(**kwargs)
            torch_ml_testing_dataloader = torch_ml_testing_dataloader
        else:
            torch_ml_testing_dataloader = None

        self._torch_ml_testing_dataloader = torch_ml_testing_dataloader

        return None



    def _generate_and_store_torch_ml_training_dataloader(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        ml_training_dataset = self_core_attrs["ml_training_dataset"]

        if ml_training_dataset is not None:
            mini_batch_size = \
                self_core_attrs["mini_batch_size"]
            num_data_loader_workers = \
                self_core_attrs["num_data_loader_workers"]
            torch_ml_training_dataset = \
                ml_training_dataset._get_torch_ml_dataset()
            torch_ml_dataloader_cls = \
                torch.utils.data.DataLoader

            kwargs = {"dataset": torch_ml_training_dataset,
                      "batch_size": mini_batch_size,
                      "shuffle": True,
                      "num_workers": num_data_loader_workers,
                      "worker_init_fn": _seed_worker,
                      "generator": self._generator}
            torch_ml_training_dataloader = torch_ml_dataloader_cls(**kwargs)
        else:
            torch_ml_training_dataloader = None

        self._torch_ml_training_dataloader = torch_ml_training_dataloader

        return None



    def _generate_and_store_torch_ml_validation_dataloader(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        ml_validation_dataset = self_core_attrs["ml_validation_dataset"]

        if ml_validation_dataset is not None:
            mini_batch_size = \
                self_core_attrs["mini_batch_size"]
            num_data_loader_workers = \
                self_core_attrs["num_data_loader_workers"]
            torch_ml_validation_dataset = \
                ml_validation_dataset._get_torch_ml_dataset()
            torch_ml_dataloader_cls = \
                torch.utils.data.DataLoader

            kwargs = {"dataset": torch_ml_validation_dataset,
                      "batch_size": mini_batch_size,
                      "shuffle": True,
                      "num_workers": num_data_loader_workers,
                      "worker_init_fn": _seed_worker,
                      "generator": self._generator}
            torch_ml_validation_dataloader = torch_ml_dataloader_cls(**kwargs)
        else:
            torch_ml_validation_dataloader = None

        self._torch_ml_validation_dataloader = torch_ml_validation_dataloader

        return None



    def _get_torch_ml_training_dataloader(self):
        if self._torch_ml_training_dataloader is None:
            self._generate_and_store_torch_ml_training_dataloader()

        torch_ml_training_dataloader = self._torch_ml_training_dataloader

        return torch_ml_training_dataloader



    def _get_torch_ml_validation_dataloader(self):
        if self._torch_ml_validation_dataloader is None:
            self._generate_and_store_torch_ml_validation_dataloader()

        torch_ml_validation_dataloader = self._torch_ml_validation_dataloader

        return torch_ml_validation_dataloader



    def _get_torch_ml_testing_dataloader(self):
        if self._torch_ml_testing_dataloader is None:
            self._generate_and_store_torch_ml_testing_dataloader()

        torch_ml_testing_dataloader = self._torch_ml_testing_dataloader

        return torch_ml_testing_dataloader



def _check_and_convert_ml_dataset_manager(params):
    obj_name = "ml_dataset_manager"
    obj = params[obj_name]
    obj_core_attrs = obj.get_core_attrs(deep_copy=False)

    key = "ml_dataset_manager_cls"
    accepted_nontrivial_cls = params[key]
    del params[key]
    
    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": (accepted_nontrivial_cls,)}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    current_func_name = "_check_and_convert_ml_dataset_manager"

    partial_keys = ("training", "testing")
    unformatted_key_1 = "misc_model_{}_metadata"
    unformatted_key_2 = "ml_{}_dataset"
    for partial_key in partial_keys:
        key_1 = unformatted_key_1.format(partial_key)
        key_2 = unformatted_key_2.format(partial_key)
        if (key_1 in params) and (obj_core_attrs[key_2] is None):
            unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
            err_msg = unformatted_err_msg.format(partial_key)
            raise ValueError(err_msg)

    kwargs = \
        obj_core_attrs
    ml_dataset_manager = \
        accepted_nontrivial_cls(**kwargs)
    ml_dataset_manager._torch_ml_training_dataloader = \
        obj._torch_ml_training_dataloader
    ml_dataset_manager._torch_ml_validation_dataloader = \
        obj._torch_ml_validation_dataloader
    ml_dataset_manager._torch_ml_testing_dataloader = \
        obj._torch_ml_testing_dataloader

    return ml_dataset_manager



def _pre_serialize_ml_dataset_manager(ml_dataset_manager):
    serializable_rep = ml_dataset_manager.pre_serialize()
    
    return serializable_rep



class _DressedUpBuffer(torch.nn.Module):
    def __init__(self, obj_to_convert_and_store_as_dressed_up_buffer):
        super().__init__()

        buffer_name = "obj_stored_as_dressed_up_buffer_represents_a_str"
        if isinstance(obj_to_convert_and_store_as_dressed_up_buffer, str):
            buffer_val = torch.tensor(True)
        else:
            buffer_val = torch.tensor(False)
        self.register_buffer(buffer_name, buffer_val)

        buffer_name = "obj_stored_as_dressed_up_buffer"
        if isinstance(obj_to_convert_and_store_as_dressed_up_buffer, dict):
            module_dict = dict()
            for key in obj_to_convert_and_store_as_dressed_up_buffer:
                kwargs = {"obj_to_convert_and_store_as_dressed_up_buffer": \
                          obj_to_convert_and_store_as_dressed_up_buffer[key]}
                module_dict[key] = _DressedUpBuffer(**kwargs)
            module_dict = torch.nn.ModuleDict(module_dict)
            self.register_module(name=buffer_name, module=module_dict)
        else:
            obj_alias = obj_to_convert_and_store_as_dressed_up_buffer
            if isinstance(obj_alias, str):
                ords = list(map(ord, obj_alias))
                buffer_val = torch.tensor(ords)
            else:
                buffer_val = torch.tensor(obj_alias)
            self.register_buffer(buffer_name, buffer_val)

        return None



def _check_and_convert_ml_inputs(params):
    params = params.copy()

    obj_name = "ml_inputs"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    params[obj_name] = czekitout.convert.to_dict(**kwargs)

    input_tensor = next(iter(params["ml_inputs"].values()))
    target_device = (input_tensor.device
                     if isinstance(input_tensor, torch.Tensor)
                     else None)
    target_device = params.get("target_device", target_device)

    name_of_obj_alias_of_ml_data_dict = "ml_inputs"

    func_name = ("_check_and_convert_normalizable_elems"
                 "_of_ml_inputs_are_normalized")
    func_alias = globals()[func_name]
    normalizable_elems_are_normalized = func_alias(params)

    param_subset = \
        {"name_of_obj_alias_of_ml_data_dict": name_of_obj_alias_of_ml_data_dict,
         "ml_data_dict": params[name_of_obj_alias_of_ml_data_dict],
         "target_numerical_data_container_cls": torch.Tensor,
         "target_device": target_device,
         "normalizable_elems_are_normalized": normalizable_elems_are_normalized}

    for name in param_subset:
        params[name] = param_subset[name]

    ml_data_dict = _check_and_convert_ml_data_dict(params)
    ml_inputs = ml_data_dict
    
    return ml_inputs



def _check_and_convert_normalizable_elems_of_ml_inputs_are_normalized(params):
    obj_name = \
        "normalizable_elems_of_ml_inputs_are_normalized"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    normalizable_elems_of_ml_inputs_are_normalized = \
        czekitout.convert.to_bool(**kwargs)
    
    return normalizable_elems_of_ml_inputs_are_normalized



def _check_and_convert_unnormalize_normalizable_elems_of_ml_predictions(params):
    obj_name = \
        "unnormalize_normalizable_elems_of_ml_predictions"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    unnormalize_normalizable_elems_of_ml_predictions = \
        czekitout.convert.to_bool(**kwargs)
    
    return unnormalize_normalizable_elems_of_ml_predictions



def _check_and_convert_deep_copy(params):
    obj_name = "deep_copy"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    deep_copy = czekitout.convert.to_bool(**kwargs)

    return deep_copy



_default_normalizable_elems_of_ml_inputs_are_normalized = True
_default_unnormalize_normalizable_elems_of_ml_predictions = False
_default_deep_copy = True



class _MLModel(torch.nn.Module):
    def __init__(self,
                 ml_data_normalizer,
                 ml_data_type_validator,
                 ml_data_value_validator,
                 ml_data_shape_analyzer,
                 variable_axis_size_dict,
                 expected_keys_of_ml_inputs,
                 subcls_ctor_params):
        super().__init__()

        self._ml_data_normalizer = ml_data_normalizer
        self._ml_data_type_validator = ml_data_type_validator
        self._ml_data_value_validator = ml_data_value_validator
        self._ml_data_shape_analyzer = ml_data_shape_analyzer
        self._variable_axis_size_dict = variable_axis_size_dict
        self._expected_keys_of_ml_inputs = expected_keys_of_ml_inputs

        self._normalization_weights = \
            subcls_ctor_params.get("normalization_weights", dict())
        self._normalization_biases = \
            subcls_ctor_params.get("normalization_biases", dict())

        self._core_attrs = subcls_ctor_params

        kwargs = {"obj_to_convert_and_store_as_dressed_up_buffer": \
                  subcls_ctor_params}
        self._ctor_params = _DressedUpBuffer(**kwargs)

        return None



    def make_predictions(
            self,
            ml_inputs,
            normalizable_elems_of_ml_inputs_are_normalized=\
            _default_normalizable_elems_of_ml_inputs_are_normalized,
            unnormalize_normalizable_elems_of_ml_predictions=\
            _default_unnormalize_normalizable_elems_of_ml_predictions):
        params = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}

        param_name_subset_1 = \
            ("ml_data_normalizer",
             "ml_data_type_validator",
             "ml_data_value_validator",
             "ml_data_shape_analyzer",
             "variable_axis_size_dict",
             "expected_ml_data_dict_keys")
        
        for param_name_1 in param_name_subset_1:
            attr_name = ("_"+param_name_1
                         if (param_name_1 != "expected_ml_data_dict_keys")
                         else "_expected_keys_of_ml_inputs")
            params[param_name_1] = getattr(self, attr_name)

        params["target_device"] = next(self.parameters()).device

        param_name_subset_2 = \
            ("ml_inputs",
             "normalizable_elems_of_ml_inputs_are_normalized",
             "unnormalize_normalizable_elems_of_ml_predictions")

        global_symbol_table = globals()
        for param_name_2 in param_name_subset_2:
            func_name = "_check_and_convert_" + param_name_2
            func_alias = global_symbol_table[func_name]
            params[param_name_2] = func_alias(params)

        kwargs = {param_name_2: params[param_name_2]
                  for param_name_2
                  in param_name_subset_2}
        ml_predictions = self._make_predictions(**kwargs)

        return ml_predictions



    def _make_predictions(self,
                          ml_inputs,
                          normalizable_elems_of_ml_inputs_are_normalized,
                          unnormalize_normalizable_elems_of_ml_predictions):
        normalizable_elems_of_ml_inputs_are_not_normalized = \
            (not normalizable_elems_of_ml_inputs_are_normalized)

        kwargs = {"ml_data_dict": ml_inputs,
                  "normalization_weights": self._normalization_weights,
                  "normalization_biases": self._normalization_biases}
        _ = (_normalize_normalizable_elems_in_ml_data_dict(**kwargs)
             if normalizable_elems_of_ml_inputs_are_not_normalized
             else None)

        ml_predictions = self.__call__(ml_inputs)

        normalizable_elems_of_ml_predictions_are_to_be_unnormalized = \
            unnormalize_normalizable_elems_of_ml_predictions

        kwargs = {"ml_data_dict": ml_predictions,
                      "normalization_weights": self._normalization_weights,
                      "normalization_biases": self._normalization_biases}
        _ = (_unnormalize_normalizable_elems_in_ml_data_dict(**kwargs)
             if normalizable_elems_of_ml_predictions_are_to_be_unnormalized
             else None)

        return ml_predictions



    def get_core_attrs(self, deep_copy=_default_deep_copy):
        r"""Return the "core attributes", i.e. the construction parameters, as a
        `dict` object.

        Parameters
        ----------
        deep_copy : `bool`, optional
            Let ``core_attrs`` denote the core attributes.

            If ``deep_copy`` is set to ``True``, then a deep copy of
            ``core_attrs`` is returned.  Otherwise, a shallow copy of
            ``core_attrs`` is returned.

        Returns
        -------
        core_attrs : `dict`
            The core attributes.

        """
        params = {"deep_copy": deep_copy}
        deep_copy = _check_and_convert_deep_copy(params)
        
        core_attrs = (self.core_attrs
                      if (deep_copy == True)
                      else self._core_attrs.copy())

        return core_attrs



    @property
    def core_attrs(self):
        r"""`dict`: The "core attributes", i.e. the construction parameters.

        Note that ``core_attrs`` should be considered **read-only**.

        """
        result = copy.deepcopy(self._core_attrs)
        
        return result



def _initialize_layer_weights_according_to_activation_func(activation_func,
                                                           layer):
    activation_func_type_to_weight_initialization_func_map = \
        {torch.nn.ReLU: torch.nn.init.kaiming_normal_,
         torch.nn.LeakyReLU: torch.nn.init.kaiming_normal_,
         torch.nn.Sigmoid: torch.nn.init.xavier_normal_,
         torch.nn.Tanh: torch.nn.init.xavier_normal_,
         torch.nn.Softmax: torch.nn.init.xavier_normal_,
         torch.nn.Identity: torch.nn.init.xavier_normal_}

    activation_func_type = \
        type(activation_func)
    key = \
        activation_func_type
    weight_initialization_func = \
        activation_func_type_to_weight_initialization_func_map[key]

    kwargs = {"tensor": layer.weight}
    if weight_initialization_func == torch.nn.init.kaiming_normal_:
        kwargs["nonlinearity"] = ("relu"
                                  if (activation_func_type == torch.nn.ReLU)
                                  else "leaky_relu")
        kwargs["a"] = getattr(activation_func, "negative_slope", 0)
        kwargs["mode"] = "fan_out"
        weight_initialization_func(**kwargs)
    else:  # if weight_initialization_func == torch.nn.init.xavier_normal_:
        kwargs["gain"] = (5/3
                          if activation_func_type == torch.nn.Tanh
                          else 1)
        weight_initialization_func(**kwargs)

    return None



def _check_and_convert_mini_batch_norm_eps(params):
    obj_name = "mini_batch_norm_eps"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}    
    mini_batch_norm_eps = czekitout.convert.to_positive_float(**kwargs)

    return mini_batch_norm_eps



_default_mini_batch_norm_eps = 1e-5



class _BasicResNetBuildingBlock(torch.nn.Module):
    def __init__(self,
                 num_input_channels,
                 num_output_channels,
                 max_kernel_size,
                 first_conv_layer_performs_downsampling,
                 final_activation_func,
                 mini_batch_norm_eps):
        super().__init__()

        self._num_input_channels = \
            num_input_channels
        self._num_output_channels = \
            num_output_channels
        self._max_kernel_size = \
            max_kernel_size
        self._first_conv_layer_performs_downsampling = \
            first_conv_layer_performs_downsampling
        self._final_activation_func = \
            final_activation_func
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._conv_layers = self._generate_conv_layers()
        self._mini_batch_norms = self._generate_mini_batch_norms()

        return None



    def _generate_conv_layers(self):
        num_input_channels = \
            self._num_input_channels
        num_output_channels = \
            self._num_output_channels
        max_kernel_size = \
            self._max_kernel_size
        first_conv_layer_performs_downsampling = \
            self._first_conv_layer_performs_downsampling

        conv_layers = tuple()

        kwargs = {"in_channels": num_input_channels,
                  "out_channels": num_output_channels,
                  "kernel_size": max_kernel_size,
                  "stride": 1+first_conv_layer_performs_downsampling,
                  "padding": (max_kernel_size-1)//2,
                  "padding_mode": "zeros",
                  "bias": False}
        conv_layer = torch.nn.Conv2d(**kwargs)
        conv_layers += (conv_layer,)
        
        kwargs["in_channels"] = num_output_channels
        kwargs["stride"] = 1
        conv_layer = torch.nn.Conv2d(**kwargs)
        conv_layers += (conv_layer,)

        if ((num_input_channels != num_output_channels)
            or first_conv_layer_performs_downsampling):
            kwargs["in_channels"] = num_input_channels
            kwargs["kernel_size"] = 1
            kwargs["stride"] = 1+first_conv_layer_performs_downsampling
            kwargs["padding"] = 0
            conv_layer = torch.nn.Conv2d(**kwargs)
            conv_layers += (conv_layer,)
        
        self._initialize_conv_layer_weights(conv_layers)

        conv_layers = torch.nn.ModuleList(conv_layers)

        return conv_layers



    def _initialize_conv_layer_weights(self, conv_layers):
        for conv_layer_idx, conv_layer in enumerate(conv_layers):
            activation_func = (torch.nn.ReLU()
                               if (conv_layer_idx == 0)
                               else self._final_activation_func)
            kwargs = {"activation_func": activation_func, "layer": conv_layer}
            _initialize_layer_weights_according_to_activation_func(**kwargs)

        return None



    def _generate_mini_batch_norms(self):
        mini_batch_norms = tuple()
        for conv_layer_idx, _ in enumerate(self._conv_layers):
            kwargs = {"num_features": self._num_output_channels,
                      "eps": self._mini_batch_norm_eps}
            mini_batch_norm = torch.nn.BatchNorm2d(**kwargs)

            torch.nn.init.constant_(mini_batch_norm.bias, 0)
            if conv_layer_idx < 2:
                torch.nn.init.constant_(mini_batch_norm.weight, 1)
            else:
                torch.nn.init.constant_(mini_batch_norm.weight, 0)
            
            mini_batch_norms += (mini_batch_norm,)
                
        mini_batch_norms = torch.nn.ModuleList(mini_batch_norms)

        return mini_batch_norms



    def forward(self, input_tensor):
        intermediate_tensor_1 = self._conv_layers[0](input_tensor)
        intermediate_tensor_1 = self._mini_batch_norms[0](intermediate_tensor_1)
        intermediate_tensor_1 = torch.nn.functional.relu(intermediate_tensor_1)
        
        intermediate_tensor_1 = self._conv_layers[1](intermediate_tensor_1)
        intermediate_tensor_1 = self._mini_batch_norms[1](intermediate_tensor_1)

        if ((self._num_input_channels == self._num_output_channels)
            and (not self._first_conv_layer_performs_downsampling)):
            intermediate_tensor_2 = \
                input_tensor
        else:
            intermediate_tensor_2 = \
                self._conv_layers[2](input_tensor)
            intermediate_tensor_2 = \
                self._mini_batch_norms[2](intermediate_tensor_2)
            
        intermediate_tensor_1 += intermediate_tensor_2
        
        output_tensor = self._final_activation_func(intermediate_tensor_1)

        return output_tensor



class _BasicResNetStage(torch.nn.Sequential):
    # Here we are borrowing the term ``stage`` from the FishNet paper of Sun et
    # al.
    def __init__(self,
                 num_input_channels,
                 max_kernel_size,
                 num_building_blocks,
                 final_activation_func,
                 mini_batch_norm_eps):
        self._num_input_channels = \
            num_input_channels
        self._max_kernel_size = \
            max_kernel_size
        self._num_building_blocks = \
            num_building_blocks
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._num_output_channels = self._num_input_channels

        resnet_building_blocks = \
            self._generate_resnet_building_blocks(final_activation_func)

        super().__init__(*resnet_building_blocks)

        self._final_activation_func = final_activation_func

        return None



    def _generate_resnet_building_blocks(self, final_activation_func):
        resnet_building_block_indices = range(self._num_building_blocks)

        resnet_building_blocks = tuple()
        for resnet_building_block_idx in resnet_building_block_indices:
            if resnet_building_block_idx == 0:
                kwargs = {"num_input_channels": self._num_input_channels,
                          "num_output_channels": self._num_output_channels,
                          "max_kernel_size": self._max_kernel_size,
                          "first_conv_layer_performs_downsampling": False,
                          "final_activation_func": torch.nn.ReLU(),
                          "mini_batch_norm_eps": self._mini_batch_norm_eps}
            else:
                if resnet_building_block_idx == self._num_building_blocks-1:
                    kwargs["final_activation_func"] = final_activation_func

            resnet_building_block = _BasicResNetBuildingBlock(**kwargs)
            resnet_building_blocks += (resnet_building_block,)

        return resnet_building_blocks



class _DistopticaNetEntryFlow(torch.nn.Module):
    _num_downsamplings = 2

    def __init__(self,
                 num_input_channels,
                 num_filters_in_first_conv_layer,
                 kernel_size_of_first_conv_layer,
                 max_kernel_size_of_resnet_building_blocks,
                 mini_batch_norm_eps):
        super().__init__()

        self._num_input_channels = \
            num_input_channels
        self._num_filters_in_first_conv_layer = \
            num_filters_in_first_conv_layer
        self._kernel_size_of_first_conv_layer = \
            kernel_size_of_first_conv_layer
        self._max_kernel_size_of_resnet_building_blocks = \
            max_kernel_size_of_resnet_building_blocks
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._num_output_channels = num_filters_in_first_conv_layer

        self._first_conv_layer = self._generate_first_conv_layer()
        self._first_mini_batch_norm = self._generate_first_mini_batch_norm()
        self._downsampling_blocks = self._generate_downsampling_blocks()
        self._resnet_stage = self._generate_resnet_stage()

        return None



    def _generate_first_conv_layer(self):
        kwargs = {"in_channels": self._num_input_channels,
                  "out_channels": self._num_filters_in_first_conv_layer,
                  "kernel_size": self._kernel_size_of_first_conv_layer,
                  "stride": 1,
                  "padding": (self._kernel_size_of_first_conv_layer-1)//2,
                  "padding_mode": "zeros",
                  "bias": False}
        conv_layer = torch.nn.Conv2d(**kwargs)

        self._initialize_first_conv_layer_weights(conv_layer)

        return conv_layer



    def _initialize_first_conv_layer_weights(self, conv_layer):
        kwargs = {"activation_func": torch.nn.ReLU(), "layer": conv_layer}
        _initialize_layer_weights_according_to_activation_func(**kwargs)

        return None



    def _generate_first_mini_batch_norm(self):
        kwargs = {"num_features": self._first_conv_layer.out_channels,
                  "eps": self._mini_batch_norm_eps}
        mini_batch_norm = torch.nn.BatchNorm2d(**kwargs)

        torch.nn.init.constant_(mini_batch_norm.weight, 1)
        torch.nn.init.constant_(mini_batch_norm.bias, 0)

        return mini_batch_norm



    def _generate_downsampling_blocks(self):
        downsampling_blocks = tuple()

        num_downsamplings = self._num_downsamplings

        for _ in range(num_downsamplings):
            kwargs = {"num_input_channels": \
                      self._num_filters_in_first_conv_layer,
                      "num_output_channels": \
                      self._num_filters_in_first_conv_layer,
                      "max_kernel_size": \
                      self._max_kernel_size_of_resnet_building_blocks,
                      "first_conv_layer_performs_downsampling": \
                      True,
                      "final_activation_func": \
                      torch.nn.ReLU(),
                      "mini_batch_norm_eps": \
                      self._mini_batch_norm_eps}
            downsampling_block = _BasicResNetBuildingBlock(**kwargs)
            downsampling_blocks += (downsampling_block,)

        downsampling_blocks = torch.nn.ModuleList(downsampling_blocks)

        return downsampling_blocks



    def _generate_resnet_stage(self):
        kwargs = {"num_input_channels": \
                  self._num_filters_in_first_conv_layer,
                  "max_kernel_size": \
                  self._max_kernel_size_of_resnet_building_blocks,
                  "num_building_blocks": \
                  2,
                  "final_activation_func": \
                  torch.nn.ReLU(),
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}
        resnet_stage = _BasicResNetStage(**kwargs)

        return resnet_stage



    def forward(self, input_tensor):
        intermediate_tensor = self._first_conv_layer(input_tensor)
        intermediate_tensor = self._first_mini_batch_norm(intermediate_tensor)
        intermediate_tensor = torch.nn.functional.relu(intermediate_tensor)
        
        intermediate_tensor = self._downsampling_blocks[0](intermediate_tensor)
        intermediate_tensor = self._downsampling_blocks[1](intermediate_tensor)
        
        output_tensor = self._resnet_stage(intermediate_tensor)

        return output_tensor



class _DistopticaNetMiddleFlow(torch.nn.Module):
    def __init__(self,
                 distoptica_net_entry_flow,
                 building_block_counts_in_stages,
                 mini_batch_norm_eps):
        super().__init__()

        self._building_block_counts_in_stages = \
            building_block_counts_in_stages
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._num_input_channels = \
            distoptica_net_entry_flow._num_output_channels
        self._max_kernel_size = \
            distoptica_net_entry_flow._max_kernel_size_of_resnet_building_blocks
        self._downsampling_blocks = \
            self._generate_downsampling_blocks()
        self._num_downsamplings = \
            len(self._downsampling_blocks)
        self._resnet_stages = \
            self._generate_resnet_stages()
        self._num_output_channels = \
            self._resnet_stages[-1]._num_output_channels

        return None



    def _generate_downsampling_blocks(self):
        num_stages = len(self._building_block_counts_in_stages)
        downsampling_block_indices = range(num_stages)

        kwargs = {"num_input_channels": self._num_input_channels,
                  "max_kernel_size": self._max_kernel_size,
                  "first_conv_layer_performs_downsampling": True,
                  "final_activation_func": torch.nn.ReLU(),
                  "mini_batch_norm_eps": self._mini_batch_norm_eps}

        resnet_building_block_cls = _BasicResNetBuildingBlock
        kwargs["num_output_channels"] = 2*self._num_input_channels

        downsampling_blocks = tuple()
        for downsampling_block_idx in downsampling_block_indices:
            downsampling_block = resnet_building_block_cls(**kwargs)
            downsampling_blocks += (downsampling_block,)

            kwargs["num_input_channels"] = kwargs["num_output_channels"]
            kwargs["num_output_channels"] *= 2

        downsampling_blocks = torch.nn.ModuleList(downsampling_blocks)

        return downsampling_blocks



    def _generate_resnet_stages(self):
        num_stages = len(self._building_block_counts_in_stages)

        resnet_stages = tuple()
        
        kwargs = {"num_input_channels": \
                  self._downsampling_blocks[0]._num_output_channels,
                  "max_kernel_size": \
                  self._max_kernel_size,
                  "final_activation_func": \
                  torch.nn.ReLU(),
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}

        for stage_idx in range(num_stages):
            kwargs["num_building_blocks"] = \
                self._building_block_counts_in_stages[stage_idx]

            resnet_stage = _BasicResNetStage(**kwargs)
            resnet_stages += (resnet_stage,)

            kwargs["num_input_channels"] *= 2

        resnet_stages = torch.nn.ModuleList(resnet_stages)

        return resnet_stages



    def forward(self, input_tensor):
        intermediate_tensor_subset = tuple()

        zip_obj = zip(self._downsampling_blocks, self._resnet_stages)

        intermediate_tensor = input_tensor
        for downsampling_block, resnet_stage in zip_obj:
            intermediate_tensor = downsampling_block(intermediate_tensor)
            intermediate_tensor = resnet_stage(intermediate_tensor)

        intermediate_tensor_subset = intermediate_tensor_subset[:-1]
        output_tensor = intermediate_tensor

        return output_tensor, intermediate_tensor_subset



class _DistopticaNetExitFlow(torch.nn.Module):
    def __init__(self,
                 distoptica_net_middle_flow,
                 height_of_input_tensor_in_pixels,
                 width_of_input_tensor_in_pixels,
                 num_nodes_in_second_last_layer,
                 num_nodes_in_last_layer,
                 mini_batch_norm_eps):
        super().__init__()

        self._height_of_input_tensor_in_pixels = \
            height_of_input_tensor_in_pixels
        self._width_of_input_tensor_in_pixels = \
            width_of_input_tensor_in_pixels
        self._num_nodes_in_second_last_layer = \
            num_nodes_in_second_last_layer
        self._num_nodes_in_last_layer = \
            num_nodes_in_last_layer
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._num_input_channels = \
            distoptica_net_middle_flow._num_output_channels
        self._fc_layers = \
            self._generate_fc_layers(distoptica_net_middle_flow)        
        self._mini_batch_norm = \
            self._generate_mini_batch_norm()

        return None



    def _generate_fc_layers(self, distoptica_net_middle_flow):
        total_num_downsamplings = \
            (_DistopticaNetEntryFlow._num_downsamplings
             + distoptica_net_middle_flow._num_downsamplings)

        num_nodes_in_third_last_layer = (self._height_of_input_tensor_in_pixels
                                         * self._width_of_input_tensor_in_pixels
                                         * self._num_input_channels
                                         // 2**(2*total_num_downsamplings))

        fc_layers = tuple()

        kwargs = {"in_features": num_nodes_in_third_last_layer,
                  "out_features": self._num_nodes_in_second_last_layer,
                  "bias": False}
        fc_layer = torch.nn.Linear(**kwargs)
        fc_layers += (fc_layer,)

        kwargs = {"in_features": self._num_nodes_in_second_last_layer,
                  "out_features": self._num_nodes_in_last_layer,
                  "bias": True}
        fc_layer = torch.nn.Linear(**kwargs)
        fc_layers += (fc_layer,)

        self._initialize_fc_layer_weights(fc_layers)

        fc_layers = torch.nn.ModuleList(fc_layers)

        return fc_layers



    def _initialize_fc_layer_weights(self, fc_layers):
        for fc_layer_idx, fc_layer in enumerate(fc_layers):
            activation_func = (torch.nn.ReLU()
                               if (fc_layer_idx == 0)
                               else torch.nn.Identity())
            kwargs = {"activation_func": activation_func, "layer": fc_layer}
            _initialize_layer_weights_according_to_activation_func(**kwargs)

            if fc_layer_idx == 1:
                torch.nn.init.constant_(fc_layer.bias, 0)

        return None



    def _generate_mini_batch_norm(self):
        kwargs = {"num_features": self._fc_layers[0].out_features,
                  "eps": self._mini_batch_norm_eps}
        mini_batch_norm = torch.nn.BatchNorm1d(**kwargs)

        torch.nn.init.constant_(mini_batch_norm.weight, 1)
        torch.nn.init.constant_(mini_batch_norm.bias, 0)

        return mini_batch_norm



    def forward(self, input_tensor):
        intermediate_tensor = torch.flatten(input_tensor, start_dim=1)
        intermediate_tensor = self._fc_layers[0](intermediate_tensor)
        intermediate_tensor = self._mini_batch_norm(intermediate_tensor)
        intermediate_tensor = torch.nn.functional.relu(intermediate_tensor)
        output_tensor = self._fc_layers[1](intermediate_tensor)
            
        return output_tensor



class _DistopticaNet(torch.nn.Module):
    def __init__(self,
                 num_input_channels,
                 num_filters_in_first_conv_layer,
                 kernel_size_of_first_conv_layer,
                 max_kernel_size_of_resnet_building_blocks,
                 building_block_counts_in_stages,
                 height_of_input_tensor_in_pixels,
                 width_of_input_tensor_in_pixels,
                 num_nodes_in_second_last_layer,
                 num_nodes_in_last_layer,
                 mini_batch_norm_eps):
        super().__init__()

        self._num_input_channels = \
            num_input_channels
        self._num_filters_in_first_conv_layer = \
            num_filters_in_first_conv_layer
        self._kernel_size_of_first_conv_layer = \
            kernel_size_of_first_conv_layer
        self._max_kernel_size_of_resnet_building_blocks = \
            max_kernel_size_of_resnet_building_blocks
        self._building_block_counts_in_stages = \
            building_block_counts_in_stages
        self._height_of_input_tensor_in_pixels = \
            height_of_input_tensor_in_pixels
        self._width_of_input_tensor_in_pixels = \
            width_of_input_tensor_in_pixels
        self._num_nodes_in_second_last_layer = \
            num_nodes_in_second_last_layer
        self._num_nodes_in_last_layer = \
            num_nodes_in_last_layer
        self._mini_batch_norm_eps = \
            mini_batch_norm_eps

        self._entry_flow = self._generate_entry_flow()
        self._middle_flow = self._generate_middle_flow()
        self._exit_flow = self._generate_exit_flow()

        self._num_downsamplings = (self._entry_flow._num_downsamplings
                                   + self._middle_flow._num_downsamplings)

        return None



    def _generate_entry_flow(self):
        kwargs = {"num_input_channels": \
                  self._num_input_channels,
                  "num_filters_in_first_conv_layer": \
                  self._num_filters_in_first_conv_layer,
                  "kernel_size_of_first_conv_layer": \
                  self._kernel_size_of_first_conv_layer,
                  "max_kernel_size_of_resnet_building_blocks": \
                  self._max_kernel_size_of_resnet_building_blocks,
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}
        entry_flow = _DistopticaNetEntryFlow(**kwargs)

        return entry_flow



    def _generate_middle_flow(self):
        kwargs = {"distoptica_net_entry_flow": \
                  self._entry_flow,
                  "building_block_counts_in_stages": \
                  self._building_block_counts_in_stages,
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}
        middle_flow = _DistopticaNetMiddleFlow(**kwargs)

        return middle_flow



    def _generate_exit_flow(self):
        kwargs = {"distoptica_net_middle_flow": \
                  self._middle_flow,
                  "height_of_input_tensor_in_pixels": \
                  self._height_of_input_tensor_in_pixels,
                  "width_of_input_tensor_in_pixels": \
                  self._width_of_input_tensor_in_pixels,
                  "num_nodes_in_second_last_layer": \
                  self._num_nodes_in_second_last_layer,
                  "num_nodes_in_last_layer": \
                  self._num_nodes_in_last_layer,
                  "mini_batch_norm_eps": \
                  self._mini_batch_norm_eps}
        exit_flow = _DistopticaNetExitFlow(**kwargs)

        return exit_flow



    def forward(self, input_tensor):
        intermediate_tensor = self._entry_flow(input_tensor)

        intermediate_tensor_subset = tuple()

        middle_flow_output_and_intermediate_tensors = \
            self._middle_flow(intermediate_tensor)

        middle_flow_intermediate_tensor_subset = \
            middle_flow_output_and_intermediate_tensors[1]
        intermediate_tensor_subset += \
            middle_flow_intermediate_tensor_subset

        middle_flow_output_tensor = \
            middle_flow_output_and_intermediate_tensors[0]
        intermediate_tensor = \
            middle_flow_output_tensor
        output_tensor = \
            self._exit_flow(intermediate_tensor)
            
        return output_tensor, intermediate_tensor_subset



class _MLMetricCalculator():
    def __init__(self):
        return None



    def _calc_metrics_of_current_mini_batch(
            self,
            ml_inputs,
            ml_predictions,
            ml_targets,
            ml_model,
            ml_dataset_manager,
            mini_batch_indices_for_entire_training_session):
        metrics_of_current_mini_batch = dict()

        return metrics_of_current_mini_batch



class _MLMetricManager():
    def __init__(self,
                 ml_metric_calculator,
                 ml_model,
                 ml_dataset_manager,
                 lr_scheduler_manager,
                 output_data_filename):
        self._ml_metric_calculator = ml_metric_calculator
        self._ml_model = ml_model
        self._ml_dataset_manager = ml_dataset_manager

        ml_dataset_manager_core_attrs = \
            ml_dataset_manager.get_core_attrs(deep_copy=False)
        self._mini_batch_size = \
            ml_dataset_manager_core_attrs["mini_batch_size"]

        phases = ("training", "validation", "testing")
        self._ml_data_instance_metrics = dict()
        self._mini_batch_indices_for_entire_training_session = dict()
        self._single_dim_slices = dict()

        for phase in phases:
            self._ml_data_instance_metrics[phase] = dict()
            self._mini_batch_indices_for_entire_training_session[phase] = 0
            self._single_dim_slices[phase] = slice(0, 0)

        kwargs = \
            {"lr_scheduler_manager": lr_scheduler_manager}
        self._total_ml_data_instance_counts = \
            self._calc_total_ml_data_instance_counts(**kwargs)

        self._output_data_filename = output_data_filename

        return None



    def _calc_total_ml_data_instance_counts(self, lr_scheduler_manager):
        total_num_lr_steps = \
            (lr_scheduler_manager._total_num_steps
             if (lr_scheduler_manager is not None)
             else 0)
        phase_in_which_to_update_lr = \
            (lr_scheduler_manager._phase_in_which_to_update_lr
             if (lr_scheduler_manager is not None)
             else "N/A")

        total_ml_data_instance_counts = dict()
        phases = ("testing", "training", "validation")
        
        for phase in phases:
            method_name = "_get_torch_ml_{}_dataloader".format(phase)
            method_alias = getattr(self._ml_dataset_manager, method_name)
            torch_ml_dataloader = method_alias()

            if ((torch_ml_dataloader is None)
                or ((lr_scheduler_manager is not None) and (phase == "testing"))
                or ((lr_scheduler_manager is None) and (phase != "testing"))):
                total_ml_data_instance_counts[phase] = 0
            else:
                torch_ml_dataset = torch_ml_dataloader.dataset
                
                if phase_in_which_to_update_lr == "training":
                    if phase == "training":
                        total_ml_data_instance_counts[phase] = \
                            ((((total_num_lr_steps+1)
                               // len(torch_ml_dataloader))
                              * len(torch_ml_dataset))
                             + (((total_num_lr_steps+1)
                                 % len(torch_ml_dataloader))
                                * self._mini_batch_size))
                        total_num_epochs = \
                            ((total_ml_data_instance_counts[phase]
                              // len(torch_ml_dataset))
                             + ((total_ml_data_instance_counts[phase]
                                 % len(torch_ml_dataset)) != 0))
                    else:
                        total_ml_data_instance_counts[phase] = \
                            (((phase == "validation")*(total_num_epochs-1) + 1)
                             * len(torch_ml_dataset))
                else:
                    total_ml_data_instance_counts[phase] = \
                        (((phase != "testing")*total_num_lr_steps + 1)
                         * len(torch_ml_dataset))

        return total_ml_data_instance_counts



    def _update_ml_data_instance_metrics(self,
                                         ml_inputs,
                                         ml_predictions,
                                         ml_targets,
                                         phase):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__", "phase"))}
        self._metrics_of_current_mini_batch = \
            self._calc_metrics_of_current_mini_batch(**kwargs)

        single_dim_slices = \
            self._single_dim_slices
        ml_data_instance_metrics = \
            self._ml_data_instance_metrics
        metrics_of_current_mini_batch = \
            self._metrics_of_current_mini_batch
        mini_batch_indices_for_entire_training_session = \
            self._mini_batch_indices_for_entire_training_session
        total_ml_data_instance_counts = \
            self._total_ml_data_instance_counts

        key_set_1 = (phase,)
        key_set_2 = tuple(metrics_of_current_mini_batch.keys())

        for key_1 in key_set_1:
            key_2 = key_set_2[0]

            start = single_dim_slices[key_1].stop
            stop = start + torch.numel(metrics_of_current_mini_batch[key_2])
            single_dim_slice = slice(start, stop)
            single_dim_slices[key_1] = single_dim_slice

            for key_2 in key_set_2:
                if key_2 not in ml_data_instance_metrics[key_1]:
                    ml_data_instance_metrics[key_1][key_2] = \
                        np.zeros((total_ml_data_instance_counts[key_1],))

                ml_data_instance_metric_subset = \
                    metrics_of_current_mini_batch[key_2].cpu().detach().numpy()

                ml_data_instance_metrics[key_1][key_2][single_dim_slice] += \
                    ml_data_instance_metric_subset

            mini_batch_indices_for_entire_training_session[key_1] += 1

        return None



    def _calc_metrics_of_current_mini_batch(self,
                                            ml_inputs,
                                            ml_predictions,
                                            ml_targets):
        ml_metric_calculator = self._ml_metric_calculator

        kwargs = \
            {"ml_inputs": \
             ml_inputs,
             "ml_predictions": \
             ml_predictions,
             "ml_targets": \
             ml_targets,
             "ml_model": \
             self._ml_model,
             "ml_dataset_manager": \
             self._ml_dataset_manager,
             "mini_batch_indices_for_entire_training_session": \
             self._mini_batch_indices_for_entire_training_session}
        metrics_of_current_mini_batch = \
            ml_metric_calculator._calc_metrics_of_current_mini_batch(**kwargs)

        return metrics_of_current_mini_batch



    def _save_ml_data_instance_metrics(self):
        ml_data_instance_metrics = self._ml_data_instance_metrics
        filename = self._output_data_filename

        for key_1 in ml_data_instance_metrics:
            if self._total_ml_data_instance_counts[key_1] == 0:
                continue
            for key_2 in ml_data_instance_metrics[key_1]:
                unformatted_path_in_file = "ml_data_instance_metrics/{}/{}"
                path_in_file = unformatted_path_in_file.format(key_1, key_2)
                kwargs = {"filename": filename, "path_in_file": path_in_file}
                hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

                kwargs = {"dataset": ml_data_instance_metrics[key_1][key_2],
                          "dataset_id": hdf5_dataset_id,
                          "write_mode": "a"}
                h5pywrappers.dataset.save(**kwargs)

                kwargs = {"obj_id": hdf5_dataset_id, "attr_name": "dim_0"}
                attr_id = h5pywrappers.attr.ID(**kwargs)

                attr = "ml {} data instance idx".format(key_1)
                kwargs = {"attr": attr, "attr_id": attr_id, "write_mode": "a"}
                h5pywrappers.attr.save(**kwargs)

        return None



class _MLLossCalculator():
    def __init__(self):
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
        losses_of_current_mini_batch = dict()

        return losses_of_current_mini_batch



class _MLLossManager():
    def __init__(self,
                 ml_loss_calculator,
                 ml_model,
                 ml_dataset_manager,
                 lr_scheduler_manager,
                 output_data_filename):
        self._ml_loss_calculator = ml_loss_calculator
        self._ml_model = ml_model
        self._ml_dataset_manager = ml_dataset_manager

        phases = ("training", "validation")
        self._mini_batch_losses = dict()
        self._mini_batch_indices_for_entire_training_session = dict()
        self._mini_batch_indices_for_current_epoch = dict()

        for phase in phases:
            self._mini_batch_losses[phase] = dict()
            self._mini_batch_indices_for_entire_training_session[phase] = 0
            self._mini_batch_indices_for_current_epoch[phase] = 0

        kwargs = \
            {"lr_scheduler_manager": lr_scheduler_manager}
        self._total_mini_batch_counts = \
            self._calc_total_mini_batch_counts(**kwargs)

        self._output_data_filename = output_data_filename

        return None



    def _calc_total_mini_batch_counts(self, lr_scheduler_manager):
        total_num_lr_steps = \
            lr_scheduler_manager._total_num_steps
        phase_in_which_to_update_lr = \
            lr_scheduler_manager._phase_in_which_to_update_lr

        total_mini_batch_counts = dict()
        phases = ("training", "validation")
        
        for phase in phases:
            method_name = "_get_torch_ml_{}_dataloader".format(phase)
            method_alias = getattr(self._ml_dataset_manager, method_name)
            torch_ml_dataloader = method_alias()

            if torch_ml_dataloader is None:
                total_mini_batch_counts[phase] = 0
            else:
                if phase_in_which_to_update_lr == "training":
                    if phase == "training":
                        total_mini_batch_counts[phase] = \
                            total_num_lr_steps+1
                        total_num_epochs = \
                            ((total_mini_batch_counts[phase]
                              // len(torch_ml_dataloader))
                             + ((total_mini_batch_counts[phase]
                                 % len(torch_ml_dataloader)) != 0))
                    else:
                        total_mini_batch_counts[phase] = \
                            total_num_epochs*len(torch_ml_dataloader)
                else:
                    total_mini_batch_counts[phase] = \
                        (total_num_lr_steps+1) * len(torch_ml_dataloader)

        return total_mini_batch_counts



    def _reset_mini_batch_indices_for_current_epoch(self):
        for phase in self._mini_batch_indices_for_current_epoch:
            self._mini_batch_indices_for_current_epoch[phase] = 0

        return None



    def _update_mini_batch_losses(self,
                                  ml_inputs,
                                  ml_predictions,
                                  ml_targets,
                                  phase,
                                  ml_metric_manager):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        self._losses_of_current_mini_batch = \
            self._calc_losses_of_current_mini_batch(**kwargs)

        metrics_of_current_mini_batch = \
            ml_metric_manager._metrics_of_current_mini_batch

        key_set_1 = (phase,)
        key_set_2 = tuple(self._losses_of_current_mini_batch.keys())

        for key_1 in key_set_1:
            for key_2 in key_set_2:
                if key_2 not in self._mini_batch_losses[key_1]:
                    self._mini_batch_losses[key_1][key_2] = \
                        np.zeros((self._total_mini_batch_counts[key_1],))

                array_idx = \
                    self._mini_batch_indices_for_entire_training_session[key_1]
                self._mini_batch_losses[key_1][key_2][array_idx] += \
                    self._losses_of_current_mini_batch[key_2].item()

                if key_1 != "training":
                    del self._losses_of_current_mini_batch[key_2]

            self._mini_batch_indices_for_entire_training_session[key_1] += 1
            self._mini_batch_indices_for_current_epoch[key_1] += 1

        key_set_3 = tuple(metrics_of_current_mini_batch.keys())
        for key_3 in key_set_3:
            del metrics_of_current_mini_batch[key_3]

        return None



    def _calc_losses_of_current_mini_batch(self,
                                           ml_inputs,
                                           ml_predictions,
                                           ml_targets,
                                           phase,
                                           ml_metric_manager):
        kwargs = \
            {key: val
             for key, val in locals().items()
             if (key not in ("self", "__class__"))}
        kwargs["ml_model"] = \
            self._ml_model
        kwargs["ml_dataset_manager"] = \
            self._ml_dataset_manager
        kwargs["mini_batch_indices_for_entire_training_session"] = \
            self._mini_batch_indices_for_entire_training_session
        ml_loss_calculator = \
            self._ml_loss_calculator
        losses_of_current_mini_batch = \
            ml_loss_calculator._calc_losses_of_current_mini_batch(**kwargs)

        return losses_of_current_mini_batch



    def _perform_backpropagation(self):
        self._losses_of_current_mini_batch["total"].backward()

        key_set = tuple(self._losses_of_current_mini_batch.keys())
        for key in key_set:
            del self._losses_of_current_mini_batch[key]

        return None



    def _calc_avg_total_mini_batch_loss_of_current_epoch(self, phase):
        stop = self._mini_batch_indices_for_entire_training_session[phase]
        start = stop - self._mini_batch_indices_for_current_epoch[phase]
        single_dim_slice = slice(start, stop)

        total_mini_batch_losses_of_current_epoch = \
            self._mini_batch_losses[phase]["total"][single_dim_slice]
        avg_total_mini_batch_loss_of_current_epoch = \
            total_mini_batch_losses_of_current_epoch.mean()

        return avg_total_mini_batch_loss_of_current_epoch



    def _save_mini_batch_losses(self):
        mini_batch_losses = self._mini_batch_losses
        filename = self._output_data_filename

        for key_1 in mini_batch_losses:
            if self._total_mini_batch_counts[key_1] == 0:
                continue
            for key_2 in mini_batch_losses[key_1]:
                unformatted_path_in_file = "mini_batch_losses/{}/{}"
                path_in_file = unformatted_path_in_file.format(key_1, key_2)
                kwargs = {"filename": filename, "path_in_file": path_in_file}
                hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

                kwargs = {"dataset": self._mini_batch_losses[key_1][key_2],
                          "dataset_id": hdf5_dataset_id,
                          "write_mode": "a"}
                h5pywrappers.dataset.save(**kwargs)

                kwargs = {"obj_id": hdf5_dataset_id, "attr_name": "dim_0"}
                attr_id = h5pywrappers.attr.ID(**kwargs)

                attr = "{} mini batch instance idx".format(key_1)
                kwargs = {"attr": attr, "attr_id": attr_id, "write_mode": "a"}
                h5pywrappers.attr.save(**kwargs)

        return None



def _check_and_convert_checkpoints(params):
    obj_name = "checkpoints"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_checkpoints"

    if obj is None:
        checkpoints = None
    else:
        try:
            kwargs = {"obj": obj, "obj_name": obj_name}
            func_alias = czekitout.convert.to_tuple_of_nonnegative_ints
            checkpoints = func_alias(**kwargs)
        except:
            err_msg = globals()[current_func_name+"_err_msg_1"]
            raise ValueError(err_msg)

    return checkpoints



def _pre_serialize_checkpoints(checkpoints):
    serializable_rep = checkpoints
    
    return serializable_rep



def _de_pre_serialize_checkpoints(serializable_rep):
    checkpoints = serializable_rep
    
    return checkpoints



def _check_and_convert_lr_scheduler_manager(params):
    module_alias = emicroml.modelling.lr
    func_alias = module_alias._check_and_convert_lr_scheduler_manager
    lr_scheduler_manager = func_alias(params)

    return lr_scheduler_manager



def _pre_serialize_lr_scheduler_manager(lr_scheduler_manager):
    module_alias = emicroml.modelling.lr
    func_alias = module_alias._pre_serialize_lr_scheduler_manager
    serializable_rep = func_alias(lr_scheduler_manager)
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_manager(serializable_rep):
    module_alias = emicroml.modelling.lr
    func_alias = module_alias._de_pre_serialize_lr_scheduler_manager
    lr_scheduler_manager = func_alias(serializable_rep)

    return lr_scheduler_manager



def _check_and_convert_output_dirname(params):
    obj_name = "output_dirname"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}    
    output_dirname = czekitout.convert.to_str_from_str_like(**kwargs)

    return output_dirname



def _pre_serialize_output_dirname(output_dirname):
    serializable_rep = output_dirname
    
    return serializable_rep



def _de_pre_serialize_output_dirname(serializable_rep):
    output_dirname = serializable_rep
    
    return output_dirname



def _check_and_convert_misc_model_training_metadata(params):
    params["name_of_obj_alias_of_metadata"] = "misc_model_training_metadata"
    misc_model_training_metadata = _check_and_convert_metadata(params)

    return misc_model_training_metadata



def _check_and_convert_metadata(params):
    obj_name = params.pop("name_of_obj_alias_of_metadata")
    obj = params[obj_name]

    current_func_name = "_check_and_convert_metadata"

    try:
        json.dumps(obj)
    except:
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(obj_name)
        raise ValueError(err_msg)
    
    metadata = copy.deepcopy(obj)

    return metadata



def _pre_serialize_misc_model_training_metadata(misc_model_training_metadata):
    serializable_rep = misc_model_training_metadata
    
    return serializable_rep



def _de_pre_serialize_misc_model_training_metadata(serializable_rep):
    misc_model_training_metadata = serializable_rep
    
    return misc_model_training_metadata



def _check_and_convert_ml_model(params):
    obj_name = "ml_model"
    obj = params[obj_name]

    key = "ml_model_cls"
    accepted_types = (params[key],)
    del params[key]

    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)
    ml_model = obj

    return ml_model



def _check_and_convert_ml_model_param_groups(params):
    obj_name = "ml_model_param_groups"
    obj = params[obj_name]

    current_func_name = "_check_and_convert_ml_model_param_groups"

    try:
        ml_model_param_groups = tuple()
        for ml_model_param_group in obj:
            ml_model_param_group = list(ml_model_param_group)
            torch.optim.AdamW(params=ml_model_param_group)
            ml_model_param_groups += (ml_model_param_group,)

        key = "lr_scheduler_manager"
        lr_scheduler_manager = params[key]
        num_lr_schedulers = len(lr_scheduler_manager._lr_schedulers)
        del params[key]

        if len(obj) != num_lr_schedulers:
            err_msg = globals()[current_func_name+"_err_msg_1"]
            raise ValueError(err_msg)
    except:
        err_msg = globals()[current_func_name+"_err_msg_2"]
        raise ValueError(err_msg)

    return ml_model_param_groups



_module_alias = emicroml.modelling.lr
_default_checkpoints = None
_default_lr_scheduler_manager = _module_alias._default_lr_scheduler_manager
_default_output_dirname = "results"
_default_misc_model_training_metadata = dict()



class _MLModelTrainer(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("device_name",
                        "checkpoints",
                        "lr_scheduler_manager",
                        "output_dirname",
                        "misc_model_training_metadata")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs

    

    def __init__(self, ctor_params):
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None


    
    def execute_post_core_attrs_update_actions(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        kwargs = {"device_name": self_core_attrs["device_name"]}
        self._device = _get_device(**kwargs)

        self._ml_dataset_manager = \
            self_core_attrs["ml_dataset_manager"]
        self._lr_scheduler_manager = \
            self_core_attrs["lr_scheduler_manager"]
        self._output_dirname = \
            self_core_attrs["output_dirname"]
        self._misc_model_training_metadata = \
            self_core_attrs["misc_model_training_metadata"]

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_validation_dataset = \
            ml_dataset_manager_core_attrs["ml_validation_dataset"]

        self._lr_step_idx = \
            self._lr_scheduler_manager._lr_step_idx
        self._total_num_lr_steps = \
            self._lr_scheduler_manager._total_num_steps
        self._phase_in_which_to_update_lr = \
            self._lr_scheduler_manager._phase_in_which_to_update_lr

        self._checkpoints = ((self._total_num_lr_steps,)
                             if (self_core_attrs["checkpoints"] is None)
                             else self_core_attrs["checkpoints"])

        if ((ml_validation_dataset is None)
            and (self._phase_in_which_to_update_lr == "validation")
            and (self._total_num_lr_steps > 0)):
            raise ValueError(_ml_model_trainer_err_msg_1)

        self._ml_model_training_summary_output_data_filename = \
            self._output_dirname + "/ml_model_training_summary_output_data.h5"

        self._start_time = None
        self._ml_model = None
        self._ml_model_cls = None
        self._ml_metric_calculator = None
        self._ml_metric_manager = None
        self._ml_loss_calculator = None
        self._ml_loss_manager = None
        self._training_has_not_finished = None
                
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



    def train_ml_model(self, ml_model, ml_model_param_groups):
        params = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}

        self._start_time = time.time()
        self._training_has_not_finished = True

        try:
            params = self._check_and_convert_train_ml_model_params(params)
            self._ml_model = params["ml_model"].to(self._device)
            ml_model_param_groups = params["ml_model_param_groups"]

            self._print_train_ml_model_starting_msg()

            self._generate_and_store_ml_metric_manager()

            self._generate_and_store_ml_loss_manager()
            
            self._initialize_lr_schedules(ml_model_param_groups)

            self._initialize_ml_model_training_summary_output_data_file()

            self._execute_training_and_validation_cycles()

            self._ml_metric_manager._save_ml_data_instance_metrics()

            self._ml_loss_manager._save_mini_batch_losses()

            self._save_lr_schedules()

            self._print_train_ml_model_end_msg()

            self._ml_model = None
            self._ml_metric_calculator = None
            self._ml_metric_manager = None
            self._ml_loss_calculator = None
            self._ml_loss_manager = None
        except:
            err_msg = _ml_model_trainer_err_msg_2
            raise ValueError(err_msg)

        return None



    def _check_and_convert_train_ml_model_params(self, params):
        params["ml_model_cls"] = \
            self._ml_model_cls
        params["ml_model"] = \
            _check_and_convert_ml_model(params)

        params["lr_scheduler_manager"] = \
            self._lr_scheduler_manager
        params["ml_model_param_groups"] = \
            _check_and_convert_ml_model_param_groups(params)

        return params



    def _print_train_ml_model_starting_msg(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        ml_model_cls_name = \
            czekitout.name.fully_qualified_class_name(self._ml_model)

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_training_dataset = \
            ml_dataset_manager_core_attrs["ml_training_dataset"]
        ml_validation_dataset = \
            ml_dataset_manager_core_attrs["ml_validation_dataset"]

        ml_training_dataset_core_attrs = \
            ml_training_dataset.get_core_attrs(deep_copy=False)
        path_to_ml_dataset_for_training = \
            ml_training_dataset_core_attrs["path_to_ml_dataset"]

        if ml_validation_dataset is None:
            unformatted_msg = ("Training the machine learning (ML) model "
                               "``ml_model`` of the type `{}` using the ML "
                               "dataset stored in the file ``'{}'`` for "
                               "training...\n\n\n")
            msg = unformatted_msg.format(ml_model_cls_name,
                                         path_to_ml_dataset_for_training)
        else:
            ml_validation_dataset_core_attrs = \
                ml_validation_dataset.get_core_attrs(deep_copy=False)
            path_to_ml_dataset_for_validation = \
                ml_validation_dataset_core_attrs["path_to_ml_dataset"]

            unformatted_msg = ("Training the machine learning (ML) model "
                               "``ml_model`` of the type `{}` using the ML "
                               "datasets stored in the files ``'{}'`` and "
                               "``'{}'`` for training and validation "
                               "respectively...\n\n\n")
            msg = unformatted_msg.format(ml_model_cls_name,
                                         path_to_ml_dataset_for_training,
                                         path_to_ml_dataset_for_validation)
        
        print(msg)

        return None



    def _generate_and_store_ml_metric_manager(self):
        kwargs = {"ml_metric_calculator": \
                  self._ml_metric_calculator,
                  "ml_model": \
                  self._ml_model,
                  "ml_dataset_manager": \
                  self._ml_dataset_manager,
                  "lr_scheduler_manager": \
                  self._lr_scheduler_manager,
                  "output_data_filename": \
                  self._ml_model_training_summary_output_data_filename}
        self._ml_metric_manager = _MLMetricManager(**kwargs)

        return None



    def _generate_and_store_ml_loss_manager(self):
        kwargs = {"ml_loss_calculator": \
                  self._ml_loss_calculator,
                  "ml_model": \
                  self._ml_model,
                  "ml_dataset_manager": \
                  self._ml_dataset_manager,
                  "lr_scheduler_manager": \
                  self._lr_scheduler_manager,
                  "output_data_filename": \
                  self._ml_model_training_summary_output_data_filename}
        self._ml_loss_manager = _MLLossManager(**kwargs)

        return None



    def _initialize_lr_schedules(self, ml_model_param_groups):
        lr_scheduler_manager = self._lr_scheduler_manager

        kwargs = {"ml_model_param_groups": ml_model_param_groups}
        lr_scheduler_manager._generate_and_store_torch_ml_optimizers(**kwargs)

        lr_scheduler_manager._generate_and_store_torch_lr_schedulers()
        
        lr_scheduler_manager._initialize_lr_schedules()

        return None



    def _initialize_ml_model_training_summary_output_data_file(self):
        filename = self._ml_model_training_summary_output_data_filename

        kwargs = {"filename": filename,
                  "path_in_file": "ml_model_trainer_params"}
        json_document_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"json_document": self.pre_serialize(),
                  "json_document_id": json_document_id,
                  "write_mode": "w"}
        h5pywrappers.json.document.save(**kwargs)

        torch_ml_training_dataloader = \
            self._ml_dataset_manager._get_torch_ml_training_dataloader()
        torch_ml_validation_dataloader = \
            self._ml_dataset_manager._get_torch_ml_validation_dataloader()

        num_training_mini_batches_per_epoch = \
            len(torch_ml_training_dataloader)
        num_validation_mini_batches_per_epoch = \
            (0
             if (torch_ml_validation_dataloader is None)
             else len(torch_ml_validation_dataloader))

        kwargs = {"filename": filename,
                  "path_in_file": "num_training_mini_batches_per_epoch"}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset": np.array(num_training_mini_batches_per_epoch),
                  "dataset_id": hdf5_dataset_id,
                  "write_mode": "a"}
        h5pywrappers.dataset.save(**kwargs)

        kwargs = {"filename": filename,
                  "path_in_file": "num_validation_mini_batches_per_epoch"}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset": np.array(num_validation_mini_batches_per_epoch),
                  "dataset_id": hdf5_dataset_id,
                  "write_mode": "a"}
        h5pywrappers.dataset.save(**kwargs)

        return None



    def _execute_training_and_validation_cycles(self):
        epoch = 0
        while self._training_has_not_finished:
            self._execute_training_and_validation_cycle(epoch)
            epoch += 1

        return None



    def _execute_training_and_validation_cycle(self, epoch):
        start_time = time.time()
        msg = "Starting epoch #{}...\n".format(epoch)
        print(msg)

        ml_metric_manager = self._ml_metric_manager
        ml_loss_manager = self._ml_loss_manager

        ml_loss_manager._reset_mini_batch_indices_for_current_epoch()
        self._execute_training_phase_of_cycle(epoch)
        self._execute_validation_phase_of_cycle(epoch)
        elapsed_time = time.time() - start_time

        method_alias = \
            ml_loss_manager._calc_avg_total_mini_batch_loss_of_current_epoch
        avg_total_training_mini_batch_loss_of_current_epoch = \
            method_alias(phase="training")

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_validation_dataset = \
            ml_dataset_manager_core_attrs["ml_validation_dataset"]

        if ml_validation_dataset is None:
            unformatted_msg = ("Epoch #{} has been completed; Average total "
                               "training mini-batch loss = {}; Processing time "
                               "for epoch = {} s.\n\n\n")
            args = (epoch,
                    avg_total_training_mini_batch_loss_of_current_epoch,
                    elapsed_time)
        else:
            avg_total_validation_mini_batch_loss_of_current_epoch = \
                method_alias(phase="validation")

            unformatted_msg = ("Epoch #{} has been completed; Average total "
                               "training mini-batch loss = {}; Average total "
                               "validation mini-batch loss = {}; Processing "
                               "time for epoch = {} s.\n\n\n")
            args = (epoch,
                    avg_total_training_mini_batch_loss_of_current_epoch,
                    avg_total_validation_mini_batch_loss_of_current_epoch,
                    elapsed_time)
            
        msg = unformatted_msg.format(*args)
        print(msg, flush=True)

        return None



    def _execute_training_phase_of_cycle(self, epoch):
        self._ml_model.train()

        lr_scheduler_manager = \
            self._lr_scheduler_manager
        phase_in_which_to_update_lr = \
            self._phase_in_which_to_update_lr
        torch_ml_dataloader = \
            self._ml_dataset_manager._get_torch_ml_training_dataloader()
    
        for mini_batch_idx, mini_batch in enumerate(torch_ml_dataloader):
            self._process_training_mini_batch(mini_batch,
                                              epoch,
                                              mini_batch_idx)

            if phase_in_which_to_update_lr == "training":
                if self._lr_step_idx in self._checkpoints:
                    self._save_ml_model(lr_step_idx=self._lr_step_idx)
                if self._lr_step_idx == self._total_num_lr_steps:
                    self._training_has_not_finished = False
                    break
                self._lr_step()

        print()

        return None



    def _process_training_mini_batch(self, mini_batch, epoch, mini_batch_idx):
        start_time = time.time()

        module_alias = \
            self._decode_mini_batch_and_split_into_ml_inputs_and_targets
        ml_inputs, ml_targets = \
            module_alias(mini_batch, epoch)

        lr_schedulers = self._lr_scheduler_manager._lr_schedulers

        for lr_scheduler_idx, lr_scheduler in enumerate(lr_schedulers):
            torch_ml_optimizer = lr_scheduler._torch_ml_optimizer
            torch_ml_optimizer.zero_grad(set_to_none=True)

        kwargs = {"ml_inputs": ml_inputs,
                  "ml_predictions": self._ml_model(ml_inputs),
                  "ml_targets": ml_targets,
                  "phase": "training"}
        self._ml_metric_manager._update_ml_data_instance_metrics(**kwargs)

        kwargs["ml_metric_manager"] = self._ml_metric_manager
        self._ml_loss_manager._update_mini_batch_losses(**kwargs)
        
        self._ml_loss_manager._perform_backpropagation()

        for lr_scheduler_idx, lr_scheduler in enumerate(lr_schedulers):
            torch_ml_optimizer = lr_scheduler._torch_ml_optimizer
            torch_ml_optimizer.step()
            
        elapsed_time = time.time() - start_time            
        unformatted_msg = ("Training mini_batch #{} has been processed for "
                           "epoch #{}; Processing time for mini_batch = {} s.")
        msg = unformatted_msg.format(mini_batch_idx, epoch, elapsed_time)
        print(msg)
        
        return None



    def _decode_mini_batch_and_split_into_ml_inputs_and_targets(self,
                                                                mini_batch,
                                                                epoch):
        mini_batch = {key: mini_batch[key].to(self._device)
                      for key
                      in mini_batch}

        ml_dataset_manager = \
            self._ml_dataset_manager
        torch_ml_dataloader = \
            ml_dataset_manager._get_torch_ml_training_dataloader()
        
        torch_ml_dataset = torch_ml_dataloader.dataset
        torch_ml_dataset._ml_data_decoder._decode(ml_data_dict=mini_batch)

        expected_keys_of_ml_inputs = self._ml_model._expected_keys_of_ml_inputs

        ml_inputs = dict()
        ml_targets = dict()
        for key in mini_batch:
            if key in expected_keys_of_ml_inputs:
                ml_inputs[key] = mini_batch[key]
            else:
                ml_targets[key] = mini_batch[key]

        ml_inputs["epoch"] = epoch

        return ml_inputs, ml_targets



    def _lr_step(self):
        kwargs = {"ml_loss_manager": self._ml_loss_manager}
        self._lr_scheduler_manager._step(**kwargs)            
        self._lr_step_idx = self._lr_scheduler_manager._lr_step_idx

        return None



    def _execute_validation_phase_of_cycle(self, epoch):
        self._ml_model.eval()

        lr_scheduler_manager = \
            self._lr_scheduler_manager
        phase_in_which_to_update_lr = \
            self._phase_in_which_to_update_lr
        torch_ml_dataloader = \
            self._ml_dataset_manager._get_torch_ml_validation_dataloader()

        if torch_ml_dataloader is not None:
            for mini_batch_idx, mini_batch in enumerate(torch_ml_dataloader):
                self._process_validation_mini_batch(mini_batch,
                                                    epoch,
                                                    mini_batch_idx)

            if phase_in_which_to_update_lr == "validation":
                if self._lr_step_idx in self._checkpoints:
                    self._save_ml_model(lr_step_idx=self._lr_step_idx)
                if self._lr_step_idx == self._total_num_lr_steps:
                    self._training_has_not_finished = False
                else:
                    self._lr_step()

            print()
        else:
            if phase_in_which_to_update_lr == "validation":
                if self._lr_step_idx in self._checkpoints:
                    self._save_ml_model(lr_step_idx=self._lr_step_idx)
                self._training_has_not_finished = False

        return None



    def _process_validation_mini_batch(self, mini_batch, epoch, mini_batch_idx):
        start_time = time.time()

        module_alias = \
            self._decode_mini_batch_and_split_into_ml_inputs_and_targets
        ml_inputs, ml_targets = \
            module_alias(mini_batch, epoch)

        lr_schedulers = self._lr_scheduler_manager._lr_schedulers

        for lr_scheduler_idx, lr_scheduler in enumerate(lr_schedulers):
            torch_ml_optimizer = lr_scheduler._torch_ml_optimizer
            torch_ml_optimizer.zero_grad(set_to_none=True)
            
        with torch.no_grad():
            kwargs = {"ml_inputs": ml_inputs,
                      "ml_predictions": self._ml_model(ml_inputs),
                      "ml_targets": ml_targets,
                      "phase": "validation"}
            self._ml_metric_manager._update_ml_data_instance_metrics(**kwargs)

            kwargs["ml_metric_manager"] = self._ml_metric_manager
            self._ml_loss_manager._update_mini_batch_losses(**kwargs)

        elapsed_time = time.time() - start_time            
        unformatted_msg = ("Validation mini_batch #{} has been processed for "
                           "epoch #{}; Processing time for mini_batch = {} s.")
        msg = unformatted_msg.format(mini_batch_idx, epoch, elapsed_time)
        print(msg)
        
        return None



    def _save_ml_model(self, lr_step_idx):
        filename = (self._output_dirname
                    + "/ml_model_at_lr_step_{}.pth".format(lr_step_idx))
        torch.save(self._ml_model.state_dict(), filename)

        return None



    def _save_lr_schedules(self):
        filename = self._ml_model_training_summary_output_data_filename
        self._lr_scheduler_manager._save_lr_schedules(filename)

        return None



    def _print_train_ml_model_end_msg(self):
        elapsed_time = time.time() - self._start_time

        ml_model_cls_name = \
            czekitout.name.fully_qualified_class_name(self._ml_model)

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_training_dataset = \
            ml_dataset_manager_core_attrs["ml_training_dataset"]
        ml_validation_dataset = \
            ml_dataset_manager_core_attrs["ml_validation_dataset"]
        
        ml_training_dataset_core_attrs = \
            ml_training_dataset.get_core_attrs(deep_copy=False)
        path_to_ml_dataset_for_training = \
            ml_training_dataset_core_attrs["path_to_ml_dataset"]

        output_dirname = self._output_dirname

        if ml_validation_dataset is None:
            unformatted_msg_1 = ("Finished training the machine learning (ML) "
                                 "model ``ml_model`` of the type `{}` using the "
                                 "ML dataset stored in the file ``'{}'`` for "
                                 "training.")
            msg_1 = unformatted_msg_1.format(ml_model_cls_name,
                                             path_to_ml_dataset_for_training)
        else:
            ml_validation_dataset_core_attrs = \
                ml_validation_dataset.get_core_attrs(deep_copy=False)
            path_to_ml_dataset_for_validation = \
                ml_validation_dataset_core_attrs["path_to_ml_dataset"]
            
            unformatted_msg_1 = ("Finished training the machine learning (ML) "
                                 "model ``ml_model`` of the type `{}` using the "
                                 "ML datasets stored in the files ``'{}'`` and "
                                 "``'{}'`` for training and validation "
                                 "respectively.")
            msg_1 = unformatted_msg_1.format(ml_model_cls_name,
                                             path_to_ml_dataset_for_training,
                                             path_to_ml_dataset_for_validation)

        unformatted_msg_2 = ("{} The ML model training "
                             "results have been saved in the directory "
                             "``'{}'``. Time taken to train the ML model and "
                             "to save the results: {} s.\n\n\n")
        msg_2 = unformatted_msg_2.format(msg_1, output_dirname, elapsed_time)
        print(msg_2)

        return None



def _check_and_convert_misc_model_testing_metadata(params):
    params["name_of_obj_alias_of_metadata"] = "misc_model_testing_metadata"
    misc_model_testing_metadata = _check_and_convert_metadata(params)

    return misc_model_testing_metadata



def _pre_serialize_misc_model_testing_metadata(misc_model_testing_metadata):
    serializable_rep = misc_model_testing_metadata
    
    return serializable_rep



def _de_pre_serialize_misc_model_testing_metadata(serializable_rep):
    misc_model_testing_metadata = serializable_rep
    
    return misc_model_testing_metadata



_default_misc_model_testing_metadata = dict()



class _MLModelTester(fancytypes.PreSerializableAndUpdatable):
    ctor_param_names = ("device_name",
                        "output_dirname",
                        "misc_model_testing_metadata")
    kwargs = {"namespace_as_dict": globals(),
              "ctor_param_names": ctor_param_names}

    _validation_and_conversion_funcs_ = \
        fancytypes.return_validation_and_conversion_funcs(**kwargs)
    _pre_serialization_funcs_ = \
        fancytypes.return_pre_serialization_funcs(**kwargs)
    _de_pre_serialization_funcs_ = \
        fancytypes.return_de_pre_serialization_funcs(**kwargs)

    del ctor_param_names, kwargs

    
    
    def __init__(self, ctor_params):
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None


    
    def execute_post_core_attrs_update_actions(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        kwargs = {"device_name": self_core_attrs["device_name"]}
        self._device = _get_device(**kwargs)

        self._ml_dataset_manager = \
            self_core_attrs["ml_dataset_manager"]
        self._output_dirname = \
            self_core_attrs["output_dirname"]
        self._misc_model_testing_metadata = \
            self_core_attrs["misc_model_testing_metadata"]

        self._ml_model_testing_summary_output_data_filename = \
            self._output_dirname + "/ml_model_testing_summary_output_data.h5"

        self._start_time = None
        self._ml_model = None
        self._ml_model_cls = None
        self._ml_metric_calculator = None
        self._ml_metric_manager = None
        self._testing_has_not_finished = None
                
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



    def test_ml_model(self, ml_model):
        params = {key: val
                  for key, val in locals().items()
                  if (key not in ("self", "__class__"))}

        self._start_time = time.time()
        self._testing_has_not_finished = True

        params = self._check_and_convert_test_ml_model_params(params)
        self._ml_model = params["ml_model"].to(self._device)

        self._print_test_ml_model_starting_msg()

        self._generate_and_store_ml_metric_manager()

        self._initialize_ml_model_testing_summary_output_data_file()

        self._process_testing_mini_batches()

        self._ml_metric_manager._save_ml_data_instance_metrics()

        self._print_test_ml_model_end_msg()

        self._ml_model = None
        self._ml_metric_calculator = None
        self._ml_metric_manager = None

        return None



    def _check_and_convert_test_ml_model_params(self, params):
        params["ml_model_cls"] = self._ml_model_cls
        params["ml_model"] = _check_and_convert_ml_model(params)

        return params



    def _print_test_ml_model_starting_msg(self):
        ml_model_cls_name = \
            czekitout.name.fully_qualified_class_name(self._ml_model)

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_testing_dataset = \
            ml_dataset_manager_core_attrs["ml_testing_dataset"]
        ml_testing_dataset_core_attrs = \
            ml_testing_dataset.get_core_attrs(deep_copy=False)
        path_to_ml_dataset_for_testing = \
            ml_testing_dataset_core_attrs["path_to_ml_dataset"]

        unformatted_msg = ("Testing the machine learning (ML) model "
                           "``ml_model`` of the type `{}` using the ML dataset "
                           "stored in the file ``'{}'``...\n\n\n")
        msg = unformatted_msg.format(ml_model_cls_name,
                                     path_to_ml_dataset_for_testing)
        print(msg)

        return None



    def _generate_and_store_ml_metric_manager(self):
        kwargs = {"ml_metric_calculator": \
                  self._ml_metric_calculator,
                  "ml_model": \
                  self._ml_model,
                  "ml_dataset_manager": \
                  self._ml_dataset_manager,
                  "lr_scheduler_manager": \
                  None,
                  "output_data_filename": \
                  self._ml_model_testing_summary_output_data_filename}
        self._ml_metric_manager = _MLMetricManager(**kwargs)

        return None



    def _initialize_ml_model_testing_summary_output_data_file(self):
        filename = self._ml_model_testing_summary_output_data_filename

        kwargs = {"filename": filename,
                  "path_in_file": "ml_model_tester_params"}
        json_document_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"json_document": self.pre_serialize(),
                  "json_document_id": json_document_id,
                  "write_mode": "w"}
        h5pywrappers.json.document.save(**kwargs)

        total_num_ml_testing_data_instances = \
            self._ml_metric_manager._total_ml_data_instance_counts["testing"]

        kwargs = {"filename": filename,
                  "path_in_file": "total_num_ml_testing_data_instances"}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset": np.array(total_num_ml_testing_data_instances),
                  "dataset_id": hdf5_dataset_id,
                  "write_mode": "a"}
        h5pywrappers.dataset.save(**kwargs)

        return None



    def _process_testing_mini_batches(self):
        self._ml_model.eval()

        torch_ml_dataloader = \
            self._ml_dataset_manager._get_torch_ml_testing_dataloader()
        
        for mini_batch_idx, mini_batch in enumerate(torch_ml_dataloader):
            self._process_testing_mini_batch(mini_batch, mini_batch_idx)

        print("\n\n")

        return None



    def _process_testing_mini_batch(self, mini_batch, mini_batch_idx):
        start_time = time.time()

        module_alias = \
            self._decode_mini_batch_and_split_into_ml_inputs_and_targets
        ml_inputs, ml_targets = \
            module_alias(mini_batch)

        with torch.no_grad():
            ml_predictions = self._ml_model(ml_inputs)

            ml_metric_manager = self._ml_metric_manager

            kwargs = {"ml_inputs": ml_inputs,
                      "ml_predictions": ml_predictions,
                      "ml_targets": ml_targets,
                      "phase": "testing"}
            ml_metric_manager._update_ml_data_instance_metrics(**kwargs)

        elapsed_time = time.time() - start_time            
        unformatted_msg = ("Testing mini_batch #{} has been processed; "
                           "Processing time for mini_batch = {} s.")
        msg = unformatted_msg.format(mini_batch_idx, elapsed_time)
        print(msg)
        
        return None



    def _decode_mini_batch_and_split_into_ml_inputs_and_targets(self,
                                                                mini_batch):
        mini_batch = {key: mini_batch[key].to(self._device)
                      for key
                      in mini_batch}

        ml_dataset_manager = \
            self._ml_dataset_manager
        torch_ml_dataloader = \
            ml_dataset_manager._get_torch_ml_testing_dataloader()
        
        torch_ml_dataset = torch_ml_dataloader.dataset
        ml_data_decoder = torch_ml_dataset._ml_data_decoder
        ml_data_decoder._decode(ml_data_dict=mini_batch)

        kwargs = {"ml_data_dict": \
                  mini_batch,
                  "normalization_weights": \
                  ml_data_decoder._normalization_weights,
                  "normalization_biases": \
                  ml_data_decoder._normalization_biases}
        _unnormalize_normalizable_elems_in_ml_data_dict(**kwargs)

        kwargs = {"ml_data_dict": \
                  mini_batch,
                  "normalization_weights": \
                  self._ml_model._normalization_weights,
                  "normalization_biases": \
                  self._ml_model._normalization_biases}
        _normalize_normalizable_elems_in_ml_data_dict(**kwargs)

        expected_keys_of_ml_inputs = self._ml_model._expected_keys_of_ml_inputs

        ml_inputs = dict()
        ml_targets = dict()
        for key in mini_batch:
            if key in expected_keys_of_ml_inputs:
                ml_inputs[key] = mini_batch[key]
            else:
                ml_targets[key] = mini_batch[key]

        ml_inputs["epoch"] = 0

        return ml_inputs, ml_targets



    def _print_test_ml_model_end_msg(self):
        elapsed_time = time.time() - self._start_time

        ml_model_cls_name = \
            czekitout.name.fully_qualified_class_name(self._ml_model)

        ml_dataset_manager_core_attrs = \
            self._ml_dataset_manager.get_core_attrs(deep_copy=False)
        ml_testing_dataset = \
            ml_dataset_manager_core_attrs["ml_testing_dataset"]        
        ml_testing_dataset_core_attrs = \
            ml_testing_dataset.get_core_attrs(deep_copy=False)
        path_to_ml_dataset_for_testing = \
            ml_testing_dataset_core_attrs["path_to_ml_dataset"]

        output_dirname = self._output_dirname

        unformatted_msg = ("Finished testing the machine learning (ML) model "
                           "``ml_model`` of the type `{}` using the ML dataset "
                           "stored in the file ``'{}'``. The ML model testing "
                           "results have been saved in the directory ``'{}'``. "
                           "Time taken to test the ML model and to save the "
                           "results: {} s.\n\n\n")
        msg = unformatted_msg.format(ml_model_cls_name,
                                     path_to_ml_dataset_for_testing,
                                     output_dirname,
                                     elapsed_time)
        print(msg)

        return None



def _check_and_convert_load_ml_model_from_file_params(params):
    params = params.copy()

    func_alias = _check_and_convert_ml_model_state_dict_filename
    params["ml_model_state_dict_filename"] = func_alias(params)

    func_alias = _check_and_convert_device_name
    params["device_name"] = func_alias(params)

    return params



def _check_and_convert_ml_model_state_dict_filename(params):
    obj_name = \
        "ml_model_state_dict_filename"
    kwargs = \
        {"obj": params[obj_name], "obj_name": obj_name}
    ml_model_state_dict_filename = \
        czekitout.convert.to_str_from_str_like(**kwargs)
    
    return ml_model_state_dict_filename



def _load_ml_model_from_file(ml_model_state_dict_filename,
                             device_name,
                             ml_model_cls):
    current_func_name = "_load_ml_model_from_file"

    try:
        kwargs = {"f": ml_model_state_dict_filename,
                  "map_location": torch.device('cpu'),
                  "weights_only": True}
        ml_model_state_dict = torch.load(**kwargs)
        
        ml_model = _load_ml_model_from_state_dict(ml_model_state_dict,
                                                  device_name,
                                                  ml_model_cls)
        
    except:
        func_alias = czekitout.name.fully_qualified_class_name
        ml_model_cls_name = func_alias(ml_model_cls)
        unformatted_err_msg = globals()[current_func_name+"_err_msg_1"]
        err_msg = unformatted_err_msg.format(ml_model_state_dict_filename,
                                             ml_model_cls_name)        
        raise ValueError(err_msg)

    return ml_model



def _check_and_convert_load_ml_model_from_state_dict_params(params):
    params = params.copy()

    func_alias = _check_and_convert_ml_model_state_dict
    params["ml_model_state_dict"] = func_alias(params)

    func_alias = _check_and_convert_device_name
    params["device_name"] = func_alias(params)

    return params



def _check_and_convert_ml_model_state_dict(params):
    obj_name = "ml_model_state_dict"
    obj = params[obj_name]
    kwargs = {"obj": obj,
              "obj_name": obj_name,
              "accepted_types": (collections.OrderedDict,)}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    ml_model_state_dict = obj
    
    return ml_model_state_dict



def _load_ml_model_from_state_dict(ml_model_state_dict,
                                   device_name,
                                   ml_model_cls):
    kwargs = {"obj": ml_model_state_dict,
              "obj_name": "ml_model_state_dict",
              "accepted_types": (collections.OrderedDict,)}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    current_func_name = "_load_ml_model_from_state_dict"

    try:
        ml_model_ctor_params = \
            _load_ml_model_ctor_params_from_state_dict(ml_model_state_dict)
        device = \
            _get_device(device_name)
        
        kwargs = ml_model_ctor_params
        ml_model = ml_model_cls(**kwargs)
        ml_model = ml_model.to(device)
        ml_model.load_state_dict(ml_model_state_dict)
        
    except:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)
    
    return ml_model



def _load_ml_model_ctor_params_from_state_dict(ml_model_state_dict):
    partial_key_1 = "_ctor_params"
    partial_key_2 = "obj_stored_as_dressed_up_buffer"
    partial_key_3 = "_represents_a_str"

    current_func_name = "_load_ml_model_ctor_params_from_state_dict"

    try:
        key_set_1 = ml_model_state_dict.keys()

        ml_model_ctor_params = dict()

        for key_1 in key_set_1:
            if ((len(key_1) > 1)
                and (key_1.split(".")[0] == partial_key_1)
                and (key_1.split(".")[-1] == partial_key_2)):
                tensor = ml_model_state_dict[key_1]

                prefix = partial_key_1 + "." + partial_key_2 + "."
                partial_key_4 = key_1.removeprefix(prefix)

                suffix = "." + partial_key_2
                partial_key_5 = partial_key_4.removesuffix(suffix)
            
                key_set_2 = partial_key_5.split("."+partial_key_2+".")

                current_dict = ml_model_ctor_params
                for key_2_idx, key_2 in enumerate(key_set_2):
                    if key_2_idx == len(key_set_2)-1:
                        key_3 = key_1 + partial_key_3
                        if ml_model_state_dict[key_3]:
                            current_dict[key_2] = _tensor_to_str(tensor)
                        else:
                            current_dict[key_2] = tensor.tolist()
                    else:
                        if key_2 not in current_dict:
                            current_dict[key_2] = dict()
                        current_dict = current_dict[key_2]

    except:
        err_msg = globals()[current_func_name+"_err_msg_1"]
        raise ValueError(err_msg)

    return ml_model_ctor_params



def _tensor_to_str(tensor):
    ords = tensor.tolist()
    result = "".join(map(chr, ords))

    return result



###########################
## Define error messages ##
###########################

_ml_data_type_validator_err_msg_1 = \
    ("The data type of the HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 "
     "file at the file path ``'{}'`` must be a sub-dtype of ``{}``.")
_ml_data_type_validator_err_msg_2 = \
    ("The data type of the object ``{}['{}']`` must be a sub-dtype of ``{}``.")

_ml_data_value_validator_err_msg_1 = \
    ("The HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the file "
     "path ``'{}'`` contains at least one data element with a value outside "
     "the valid range of values, namely the closed interval [{}, {}].")
_ml_data_value_validator_err_msg_2 = \
    ("The object ``{}['{}']`` contains at least one data element with a value "
     "outside the valid range of values, namely the closed interval [{}, {}].")

_ml_data_normalization_weights_and_biases_loader_err_msg_1 = \
    ("The normalization {} stored as the HDF5 attribute ``'normalization_{}'`` "
     "of the HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the "
     "file path ``'{}'`` must be a real number.")
_ml_data_normalization_weights_and_biases_loader_err_msg_2 = \
    ("The object ``normalization_{}['{}']`` must be {} {}.")
_ml_data_normalization_weights_and_biases_loader_err_msg_3 = \
    ("The normalization {} stored as the HDF5 attribute ``'normalization_{}'`` "
     "of the HDF5 dataset at the HDF5 path ``'{}'`` of the HDF5 file at the "
     "file path ``'{}'`` must be {} {}.")

_check_and_convert_normalization_weights_err_msg_1 = \
    ("The object ``{}`` is missing the key ``'{}'``.")

_check_and_convert_normalization_biases_err_msg_1 = \
    _check_and_convert_normalization_weights_err_msg_1

_ml_data_shape_analyzer_err_msg_1 = \
    ("The HDF5 dataset ``hdf5_dataset``at the HDF5 path ``'{}'`` of the HDF5 "
     "file at the file path ``'{}'`` must contain at least one data element "
     "and satisfy ``len(hdf5_dataset.shape) == {}``.")
_ml_data_shape_analyzer_err_msg_2 = \
    ("The HDF5 dataset ``hdf5_dataset``at the HDF5 path ``'{}'`` of the HDF5 "
     "file at the file path ``'{}'`` must have a shape equal to ``None``.")
_ml_data_shape_analyzer_err_msg_3 = \
    ("The HDF5 dataset ``hdf5_dataset``at the HDF5 path ``'{}'`` of the HDF5 "
     "file at the file path ``'{}'`` must satisfy "
     "``hdf5_dataset.shape[{}] == hdf5_dataset.shape[{}]``.")
_ml_data_shape_analyzer_err_msg_4 = \
    ("The HDF5 datasets ``hdf5_dataset_1`` and ``hdf5_dataset_2`` at the HDF5 "
     "paths ``'{}'`` and ``'{}'`` respectively of the HDF5 file at the file "
     "path ``'{}'`` must satisfy "
     "``hdf5_dataset_1.shape[{}] == hdf5_dataset_2.shape[{}]``.")
_ml_data_shape_analyzer_err_msg_5 = \
    ("The HDF5 dataset ``hdf5_dataset``at the HDF5 path ``'{}'`` of the HDF5 "
     "file at the file path ``'{}'`` must satisfy "
     "``hdf5_dataset.shape[{}] == {}``.")
_ml_data_shape_analyzer_err_msg_6 = \
    ("The HDF5 datasets ``hdf5_dataset_1`` and ``hdf5_dataset_2`` stored "
     "respectively in the HDF5 files at the file paths ``'{}'`` and ``'{}'``, "
     "both of which located at the common HDF5 path ``'{}'``, must satisfy "
     "``hdf5_dataset_1.shape[{}] == hdf5_dataset_2.shape[{}]``.")
_ml_data_shape_analyzer_err_msg_7 = \
    ("The object ``{}['{}']`` does not have the expected shape.")

_generate_and_save_ml_dataset_err_msg_1 = \
    ("An error occurred in trying to generate the machine learning dataset to "
     "save at the file path ``'{}'``: see traceback for details.")

_make_output_dir_err_msg_1 = \
    ("An error occurred in trying to make the directory ``'{}'``: see "
     "traceback for details.")

_check_and_convert_input_ml_dataset_filenames_err_msg_1 = \
    ("The object ``input_ml_dataset_filenames`` must store at least one "
     "string.")

_combine_ml_dataset_files_err_msg_1 = \
    ("An error occurred in trying to combine {}: see traceback for details.")

_check_and_convert_output_ml_dataset_filename_2_err_msg_1 = \
    ("The objects "
     "``output_ml_dataset_filename_1``, "
     "``output_ml_dataset_filename_2``, and "
     "``output_ml_dataset_filename_3`` must specify different file paths from "
     "one another.")
_check_and_convert_output_ml_dataset_filename_3_err_msg_1 = \
    _check_and_convert_output_ml_dataset_filename_2_err_msg_1

_check_and_convert_split_ratio_err_msg_1 = \
    ("The object ``split_ratio`` must be a triplet of nonnegative real "
     "numbers that add up to a positive number.")

_split_ml_dataset_file_err_msg_1 = \
    ("An error occurred in trying to split {}: see traceback for details.")

_check_ml_data_dict_keys_err_msg_1 = \
    _check_and_convert_normalization_weights_err_msg_1
_check_ml_data_dict_keys_err_msg_2 = \
    ("The object ``{}`` contains the key ``'{}'``, which is invalid.")

_convert_numerical_data_container_err_msg_1 = \
    ("The object ``{}`` must be an array of integers, real-numbers, or "
     "booleans.")

_check_and_convert_ml_data_instance_idx_err_msg_1 = \
    ("An error occurred in trying to get a machine learning (ML) data instance "
     "with the corresponding ML data instance index ``{}={}``{}: the object "
     "``{}`` must be an integer between ``-num_ml_data_instances`` and "
     "``num_ml_data_instances-1``, where ``num_ml_data_instances`` {}is equal "
     "to ``{}``.")

_check_and_convert_device_name_err_msg_1 = \
    ("The object ``{}`` must be either of the type `NoneType` or `str`, "
     "wherein the latter case, ``device_name`` must be a valid device name.")

_check_and_convert_single_dim_slice_err_msg_1 = \
    ("An error occurred in trying to get a sequence of machine learning (ML) "
     "data instances, with corresponding ML data instance indices specified by "
     "the object ``single_dim_slice``, from the ML dataset stored in the file "
     "``'{}'``: the object ``single_dim_slice`` must specify an integer or a "
     "sequence of integers, where the value of each integer must be between "
     "``-num_ml_data_instances`` and ``num_ml_data_instances-1``, with "
     "``num_ml_data_instances`` being the total number of ML data instances in "
     "the ML dataset, which in this case is equal to ``{}``.")

_check_and_convert_ml_validation_dataset_err_msg_1 = \
    ("The object ``ml_validation_dataset`` does not have the same "
     "normalization weights and biases as those of the object "
     "``ml_training_dataset``.")

_check_and_convert_ml_dataset_manager_err_msg_1 = \
    ("The object ``ml_dataset_manager`` must contain or specify a valid "
     "machine learning {} dataset.")

_check_and_convert_checkpoints_err_msg_1 = \
    ("The object ``checkpoints`` must either be of the type `NoneType` or be a "
     "sequence of nonnegative integers.")

_check_and_convert_metadata_err_msg_1 = \
    ("The object ``{}`` must be a JSON-serializable dictionary.")

_check_and_convert_ml_model_param_groups_err_msg_1 = \
    ("The object ``ml_model_param_groups`` must be a sequence that is equal "
     "in length to the number of learning rate schedulers to be used in "
     "machine learning model training.")
_check_and_convert_ml_model_param_groups_err_msg_2 = \
    ("The object ``ml_model_param_groups`` must be a valid sequence of machine "
     "learning model parameter groups: see traceback for details.")

_ml_model_trainer_err_msg_1 = \
    ("The object ``lr_scheduler_manager`` specifies that a nonzero number of "
     "learning rate steps are to be performed collectively in the validation "
     "cycles, however the object ``ml_dataset_manager`` does not contain nor "
     "specify a valid machine learning (ML) validation dataset: in order to "
     "train the ML model with all other hyperparameters fixed, a valid ML "
     "validation dataset must be specified in ``ml_dataset_manager.")
_ml_model_trainer_err_msg_2 = \
    ("An error occurred during machine learning model training: see traceback "
     "for details.")

_load_ml_model_from_file_err_msg_1 = \
    ("The object ``ml_model_state_dict_filename`` storing the path ``'{}'`` "
     "does not specify a path to a file storing a valid machine learning (ML) "
     "model state dictionary for the ML model type ``'{}'``: see traceback "
     "for details.")

_load_ml_model_from_state_dict_err_msg_1 = \
    ("The object ``ml_model_state_dict`` is an invalid machine learning model "
     "state dictionary: see the traceback for details.")

_load_ml_model_ctor_params_from_state_dict_err_msg_1 = \
    ("An error occurred in trying to load the constructor parameters of the "
     "machine learning model from the object ``ml_model_state_dict``: see the "
     "traceback for details.")
