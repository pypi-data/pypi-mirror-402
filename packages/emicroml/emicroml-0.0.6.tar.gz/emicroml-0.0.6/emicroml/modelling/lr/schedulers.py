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
"""For creating learning rate schedulers.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For general array handling.
import numpy as np

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes

# For loading objects from and saving objects to HDF5 files.
import h5pywrappers

# For constructing learning rate schedulers.
import torch



# For creating wrappers to PyTorch optimizer classes.
import emicroml.modelling.optimizers



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = ["BaseLRScheduler",
           "Constant",
           "Linear",
           "Exponential",
           "ReduceOnPlateau",
           "CosineAnnealingWithWarmRestarts",
           "Nonsequential",
           "Sequential",
           "Generic"]



_module_alias = \
    emicroml.modelling.optimizers
_default_skip_validation_and_conversion = \
    _module_alias._default_skip_validation_and_conversion



class BaseLRScheduler(fancytypes.PreSerializableAndUpdatable):
    r"""A wrapper to a PyTorch learning rate scheduler class.

    One cannot construct an instance of the class
    :class:`emicroml.modelling.lr.schedulers.BaseLRScheduler`, only subclasses
    of itself defined in :mod:`emicroml.modelling.lr.schedulers` module.

    Parameters
    ----------
    ctor_params : `dict`
        The construction parameters of the subclass.

    """
    def __init__(self, ctor_params):
        if type(self) is BaseLRScheduler:
            self._generate_and_store_torch_lr_scheduler()
        else:
            kwargs = ctor_params
            kwargs["skip_cls_tests"] = True
            fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

            self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self._lr_step_idx = 0
        self._clear_torch_ml_optimizer()
        self._clear_torch_lr_scheduler()
        self._clear_lr_schedule()

        return None



    def _clear_torch_ml_optimizer(self):
        self._torch_ml_optimizer = None

        return None



    def _clear_torch_lr_scheduler(self):
        self._torch_lr_scheduler = None

        return None



    def _clear_lr_schedule(self):
        self._lr_schedule = None

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



    def _generate_and_store_torch_ml_optimizer(self, ml_model_param_group):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        ml_optimizer = self_core_attrs["ml_optimizer"]

        kwargs = {"ml_model_param_group": ml_model_param_group}
        ml_optimizer._generate_and_store_torch_ml_optimizer(**kwargs)

        self._torch_ml_optimizer = ml_optimizer._torch_ml_optimizer

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        raise NotImplementedError(_base_lr_scheduler_err_msg_1)



    def _initialize_lr_schedule(self):
        self._lr_step_idx = 0
        self._lr_schedule = np.zeros((self.total_num_steps+1,))
        self._lr_schedule[0] = self._get_current_lr()

        return None



    @property
    def total_num_steps(self):
        r"""`int`: The total number of steps in the learning rate scheduler.

        ``total_num_steps`` is equal to the total number of times the global
        learning rate multiplier is updated after its initialization. The first
        time the affected machine learning model fitting parameters are updated
        after being initialized is done using the initial value of the global
        learning rate multiplier, i.e. the value of the global learning rate
        multiplier prior to any steps in the learning rate scheduler being
        performed.

        Note that ``total_num_steps`` should be considered **read-only**.

        """
        self_core_attrs = self.get_core_attrs(deep_copy=False)
        result = self_core_attrs["total_num_steps"]
        
        return result



    def _get_current_lr(self):
        current_lr = self._torch_ml_optimizer.param_groups[-1]["lr"]

        return current_lr



    def _step(self, ml_loss_manager, phase):
        self._lr_step_idx += 1

        func_alias = self._torch_lr_scheduler.step
        func_alias_co_varnames = func_alias.__code__.co_varnames

        kwargs = {"ml_loss_manager": ml_loss_manager,
                  "phase": phase,
                  "epoch": None}
        for key in tuple(kwargs.keys()):
            if key not in func_alias_co_varnames:
                del kwargs[key]

        func_alias(**kwargs)

        lr_step_idx = self._lr_step_idx
        self._lr_schedule[lr_step_idx] = self._get_current_lr()

        return None



    def _save_lr_schedule(self,
                          filename,
                          path_in_file,
                          phase_in_which_lr_steps_are_performed):
        kwargs = {"filename": filename, "path_in_file": path_in_file}
        hdf5_dataset_id = h5pywrappers.obj.ID(**kwargs)

        kwargs = {"dataset": np.array(self._lr_schedule),
                  "dataset_id": hdf5_dataset_id,
                  "write_mode": "a"}
        h5pywrappers.dataset.save(**kwargs)

        kwargs = {"obj_id": hdf5_dataset_id, "attr_name": "dim_0"}
        attr_id = h5pywrappers.attr.ID(**kwargs)

        attr = ("training mini batch instance idx"
                if phase_in_which_lr_steps_are_performed == "training"
                else "epoch")

        kwargs = {"attr": attr, "attr_id": attr_id, "write_mode": "a"}
        h5pywrappers.attr.save(**kwargs)

        return None



def _check_and_convert_ml_optimizer(params):
    module_alias = emicroml.modelling.optimizers
    func_alias = module_alias._check_and_convert_ml_optimizer
    ml_optimizer = func_alias(params)

    return ml_optimizer



def _pre_serialize_ml_optimizer(ml_optimizer):
    module_alias = emicroml.modelling.optimizers
    func_alias = module_alias._pre_serialize_ml_optimizer
    serializable_rep = func_alias(ml_optimizer)
    
    return serializable_rep



def _de_pre_serialize_ml_optimizer(serializable_rep):
    module_alias = emicroml.modelling.optimizers
    func_alias = module_alias._de_pre_serialize_ml_optimizer
    ml_optimizer = func_alias(serializable_rep)
    
    return ml_optimizer



def _check_and_convert_total_num_steps(params):
    obj_name = "total_num_steps"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    total_num_steps = czekitout.convert.to_nonnegative_int(**kwargs)

    return total_num_steps



def _pre_serialize_total_num_steps(total_num_steps):
    obj_to_pre_serialize = total_num_steps
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_total_num_steps(serializable_rep):
    total_num_steps = serializable_rep

    return total_num_steps



def _check_and_convert_scale_factor(params):
    obj_name = "scale_factor"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    scale_factor = czekitout.convert.to_positive_float(**kwargs)

    return scale_factor



def _pre_serialize_scale_factor(scale_factor):
    obj_to_pre_serialize = scale_factor
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_scale_factor(serializable_rep):
    scale_factor = serializable_rep

    return scale_factor



_module_alias = \
    emicroml.modelling.optimizers
_default_ml_optimizer = \
    _module_alias._default_ml_optimizer
_default_total_num_steps = \
    0
_default_scale_factor = \
    1
_default_skip_validation_and_conversion = \
    _module_alias._default_skip_validation_and_conversion



class Constant(BaseLRScheduler):
    r"""A wrapper to the PyTorch learning rate scheduler class 
    :class:`torch.optim.lr_scheduler.ConstantLR`.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The parameters ``last_epoch``, and ``verbose`` of the class
    :class:`torch.optim.lr_scheduler.ConstantLR` take on their default values in
    the current context.

    Parameters
    ----------
    ml_optimizer : :class:`emicroml.modelling.optimizers.Generic` | `None`, optional
        ``ml_optimizer`` specifies the generic wrapper to the PyTorch optimizer
        class to use in conjunction with the learning rate scheduler. This
        parameter implicitly determines the parameter ``optimizer`` of the
        :class:`torch.optim.lr_scheduler.ConstantLR`. If ``ml_optimizer`` is set
        to ``None``, then the parameter will be reassigned to the value
        ``emicroml.modelling.optimizers.Generic()``.
    total_num_steps : `int`, optional
        The total number of steps in the learning rate
        scheduler. ``total_num_steps`` is equal to the total number of times the
        global learning rate multiplier is updated after initialization. The
        parameter ``total_iters`` of the class
        :class:`torch.optim.lr_scheduler.ConstantLR` is equal to
        ``total_num_steps+1``.
    scale_factor : `float`, optional
        Same as the parameter ``factor`` of the class
        :class:`torch.optim.lr_scheduler.ConstantLR`.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("ml_optimizer",
                        "total_num_steps",
                        "scale_factor")
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
                 ml_optimizer=\
                 _default_ml_optimizer,
                 total_num_steps=\
                 _default_total_num_steps,
                 scale_factor=\
                 _default_scale_factor,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        module_alias = torch.optim.lr_scheduler
        kwargs = {"optimizer": self._torch_ml_optimizer,
                  "factor": self_core_attrs["scale_factor"],
                  "total_iters": self_core_attrs["total_num_steps"]+1}
        torch_lr_scheduler = module_alias.ConstantLR(**kwargs)
        self._torch_lr_scheduler = torch_lr_scheduler

        return None



def _check_and_convert_start_scale_factor(params):
    obj_name = "start_scale_factor"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    start_scale_factor = czekitout.convert.to_nonnegative_float(**kwargs)

    return start_scale_factor



def _pre_serialize_start_scale_factor(start_scale_factor):
    obj_to_pre_serialize = start_scale_factor
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_start_scale_factor(serializable_rep):
    start_scale_factor = serializable_rep

    return start_scale_factor



def _check_and_convert_end_scale_factor(params):
    obj_name = "end_scale_factor"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    end_scale_factor = czekitout.convert.to_nonnegative_float(**kwargs)

    return end_scale_factor



def _pre_serialize_end_scale_factor(end_scale_factor):
    obj_to_pre_serialize = end_scale_factor
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_end_scale_factor(serializable_rep):
    end_scale_factor = serializable_rep

    return end_scale_factor



_default_start_scale_factor = 0.5
_default_end_scale_factor = 1



class Linear(BaseLRScheduler):
    r"""A wrapper to the PyTorch learning rate scheduler class 
    :class:`torch.optim.lr_scheduler.LinearLR`.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The parameters ``last_epoch``, and ``verbose`` of the class
    :class:`torch.optim.lr_scheduler.LinearLR` take on their default values in
    the current context.

    Parameters
    ----------
    ml_optimizer : :class:`emicroml.modelling.optimizers.Generic` | `None`, optional
        ``ml_optimizer`` specifies the generic wrapper to the PyTorch optimizer
        class to use in conjunction with the learning rate scheduler. This
        parameter implicitly determines the parameter ``optimizer`` of the
        :class:`torch.optim.lr_scheduler.LinearLR`. If ``ml_optimizer`` is set
        to ``None``, then the parameter will be reassigned to the value
        ``emicroml.modelling.optimizers.Generic()``.
    total_num_steps : `int`, optional
        The total number of steps in the learning rate
        scheduler. ``total_num_steps`` is equal to the total number of times the
        global learning rate multiplier is updated after initialization. The
        parameter ``total_iters`` of the class
        :class:`torch.optim.lr_scheduler.LinearLR` is equal to
        ``total_num_steps+1``.
    start_scale_factor : `float`, optional
        Same as the parameter ``start_factor`` of the class
        :class:`torch.optim.lr_scheduler.LinearLR`.
    end_scale_factor : `float`, optional
        Same as the parameter ``end_factor`` of the class
        :class:`torch.optim.lr_scheduler.LinearLR`.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("ml_optimizer",
                        "total_num_steps",
                        "start_scale_factor",
                        "end_scale_factor")
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
                 ml_optimizer=\
                 _default_ml_optimizer,
                 total_num_steps=\
                 _default_total_num_steps,
                 start_scale_factor=\
                 _default_start_scale_factor,
                 end_scale_factor=\
                 _default_end_scale_factor,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        module_alias = torch.optim.lr_scheduler
        kwargs = {"optimizer": self._torch_ml_optimizer,
                  "start_factor": self_core_attrs["start_scale_factor"],
                  "end_factor": self_core_attrs["end_scale_factor"],
                  "total_iters": self_core_attrs["total_num_steps"]+1}
        torch_lr_scheduler = module_alias.LinearLR(**kwargs)
        self._torch_lr_scheduler = torch_lr_scheduler

        return None



def _check_and_convert_multiplicative_decay_factor(params):
    obj_name = "multiplicative_decay_factor"
    func_alias = czekitout.convert.to_nonnegative_float
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    multiplicative_decay_factor = func_alias(**kwargs)

    return multiplicative_decay_factor



def _pre_serialize_multiplicative_decay_factor(multiplicative_decay_factor):
    obj_to_pre_serialize = multiplicative_decay_factor
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_multiplicative_decay_factor(serializable_rep):
    multiplicative_decay_factor = serializable_rep

    return multiplicative_decay_factor



_default_multiplicative_decay_factor = 1



class Exponential(BaseLRScheduler):
    r"""A wrapper to the PyTorch learning rate scheduler class 
    :class:`torch.optim.lr_scheduler.ExponentialLR`.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The parameters ``last_epoch``, and ``verbose`` of the class
    :class:`torch.optim.lr_scheduler.ExponentialLR` take on their default values
    in the current context.

    Parameters
    ----------
    ml_optimizer : :class:`emicroml.modelling.optimizers.Generic` | `None`, optional
        ``ml_optimizer`` specifies the generic wrapper to the PyTorch optimizer
        class to use in conjunction with the learning rate scheduler. This
        parameter implicitly determines the parameter ``optimizer`` of the
        :class:`torch.optim.lr_scheduler.ExponentialLR`. If ``ml_optimizer`` is
        set to ``None``, then the parameter will be reassigned to the value
        ``emicroml.modelling.optimizers.Generic()``.
    total_num_steps : `int`, optional
        The total number of steps in the learning rate
        scheduler. ``total_num_steps`` is equal to the total number of times the
        global learning rate multiplier is updated after initialization. 
    multiplicative_decay_factor : `float`, optional
        Same as the parameter ``gamma`` of the class
        :class:`torch.optim.lr_scheduler.ExponentialLR`.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("ml_optimizer",
                        "total_num_steps",
                        "multiplicative_decay_factor")
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
                 ml_optimizer=\
                 _default_ml_optimizer,
                 total_num_steps=\
                 _default_total_num_steps,
                 multiplicative_decay_factor=\
                 _default_multiplicative_decay_factor,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        module_alias = torch.optim.lr_scheduler
        kwargs = {"optimizer": self._torch_ml_optimizer,
                  "gamma": self_core_attrs["multiplicative_decay_factor"]}
        torch_lr_scheduler = module_alias.ExponentialLR(**kwargs)
        self._torch_lr_scheduler = torch_lr_scheduler

        return None



_default_ml_loss_manager = None
_default_phase = "validation"
_default_epoch = None



_cls_alias = torch.optim.lr_scheduler._LRScheduler
class _TorchReduceOnPlateau(_cls_alias):
    def __init__(self,
                 torch_ml_optimizer,
                 reduction_factor,
                 max_num_steps_of_stagnation,
                 improvement_threshold,
                 averaging_window_in_steps):
        cls_alias = torch.optim.lr_scheduler.ReduceLROnPlateau
        kwargs = {"optimizer": torch_ml_optimizer,
                  "mode": "min",
                  "factor": reduction_factor,
                  "patience": max_num_steps_of_stagnation-1,
                  "threshold": improvement_threshold,
                  "threshold_mode": "rel"}
        self._base_torch_lr_scheduler = cls_alias(**kwargs)

        self._averaging_window_in_steps = averaging_window_in_steps

        super().__init__(torch_ml_optimizer)

        return None



    def step(self,
             ml_loss_manager=_default_ml_loss_manager,
             phase=_default_phase,
             epoch=_default_epoch):
        self.last_epoch = self.last_epoch+1 if (epoch is None) else epoch

        averaging_window_in_steps = self._averaging_window_in_steps

        mini_batch_losses = \
            getattr(ml_loss_manager,
                    "_mini_batch_losses",
                    None)
        mini_batch_indices_for_entire_training_session = \
            getattr(ml_loss_manager,
                    "_mini_batch_indices_for_entire_training_session",
                    {phase: 0})

        stop = mini_batch_indices_for_entire_training_session[phase]
        start = max(0, stop-averaging_window_in_steps)
        single_dim_slice = slice(start, stop)

        total_mini_batch_loss_averaged_over_window = \
            (mini_batch_losses[phase]["total"][single_dim_slice].mean()
             if (mini_batch_losses is not None)
             else None)

        kwargs = {"metrics": total_mini_batch_loss_averaged_over_window,
                  "epoch": epoch}
        _ = (self._base_torch_lr_scheduler.step(**kwargs)
             if (stop >= averaging_window_in_steps)
             else None)

        torch_optimizer = self._base_torch_lr_scheduler.optimizer
        self._last_lr = [group['lr'] for group in torch_optimizer.param_groups]

        return None



def _check_and_convert_reduction_factor(params):
    obj_name = "reduction_factor"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    reduction_factor = czekitout.convert.to_positive_float(**kwargs)

    return reduction_factor



def _pre_serialize_reduction_factor(reduction_factor):
    obj_to_pre_serialize = reduction_factor
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_reduction_factor(serializable_rep):
    reduction_factor = serializable_rep

    return reduction_factor



def _check_and_convert_max_num_steps_of_stagnation(params):
    obj_name = "max_num_steps_of_stagnation"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    max_num_steps_of_stagnation = czekitout.convert.to_positive_int(**kwargs)

    return max_num_steps_of_stagnation



def _pre_serialize_max_num_steps_of_stagnation(max_num_steps_of_stagnation):
    obj_to_pre_serialize = max_num_steps_of_stagnation
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_max_num_steps_of_stagnation(serializable_rep):
    max_num_steps_of_stagnation = serializable_rep

    return max_num_steps_of_stagnation



def _check_and_convert_improvement_threshold(params):
    obj_name = "improvement_threshold"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    improvement_threshold = czekitout.convert.to_positive_float(**kwargs)

    return improvement_threshold



def _pre_serialize_improvement_threshold(improvement_threshold):
    obj_to_pre_serialize = improvement_threshold
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_improvement_threshold(serializable_rep):
    improvement_threshold = serializable_rep

    return improvement_threshold



def _check_and_convert_averaging_window_in_steps(params):
    obj_name = "averaging_window_in_steps"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    averaging_window_in_steps = czekitout.convert.to_positive_int(**kwargs)

    return averaging_window_in_steps



def _pre_serialize_averaging_window_in_steps(averaging_window_in_steps):
    obj_to_pre_serialize = averaging_window_in_steps
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_averaging_window_in_steps(serializable_rep):
    averaging_window_in_steps = serializable_rep

    return averaging_window_in_steps



_default_reduction_factor = 0.1
_default_max_num_steps_of_stagnation = 10
_default_improvement_threshold = 0.001
_default_averaging_window_in_steps = 1



class ReduceOnPlateau(BaseLRScheduler):
    r"""A wrapper to a custom PyTorch learning rate scheduler class based on 
    the class :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The aforementioned custom PyTorch learning rate scheduler class behaves just
    like the class :class:`torch.optim.lr_scheduler.ReduceLROnPlateau` except in
    the way that an improvement is determined to have occurred or not. There is
    some freedom in how this is done for the class
    :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`. Generically speaking,
    it is done by comparing some performance metric calculated at the current
    iteration of the learning rate schedule to the best of the same metric
    calculated at the previous iterations. For the custom PyTorch learning rate
    scheduler class, the metric is chosen to be the average of the total losses
    of the ``averaging_window_in_steps`` most recent mini-batches of the phase
    wherein the global learning rate multiplier is updated, which is either the
    "training" or "validation" phase. Here, ``averaging_window_in_steps`` is a
    positive integer chosen by the user as a parameter of the current class.

    The parameters ``mode``, ``threshold_mode``, ``cooldown``, ``min_lr``,
    ``eps``, and ``verbose`` of the custom PyTorch learning rate scheduler
    class, which are the same as those of the class
    :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`, take on the default
    values of the latter.

    Parameters
    ----------
    ml_optimizer : :class:`emicroml.modelling.optimizers.Generic` | `None`, optional
        ``ml_optimizer`` specifies the generic wrapper to the PyTorch optimizer
        class to use in conjunction with the learning rate scheduler. This
        parameter implicitly determines the parameter ``optimizer`` of the
        custom PyTorch learning rate scheduler class, which is the same as that
        of the class :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`. If
        ``ml_optimizer`` is set to ``None``, then the parameter will be
        reassigned to the value ``emicroml.modelling.optimizers.Generic()``.
    total_num_steps : `int`, optional
        The total number of steps in the learning rate
        scheduler. ``total_num_steps`` is equal to the total number of times the
        global learning rate multiplier is updated after initialization. 
    reduction_factor : `float`, optional
        Same as the parameter ``factor`` of the custom PyTorch learning rate
        scheduler class, which is the same as that of the class
        :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`.
    max_num_steps_of_stagnation : `int`, optional
        The maximum number of steps of stagnation, i.e. of no improvement in the
        performance metric. The parameter ``patience`` of the custom PyTorch
        learning rate scheduler class, which is the same as that of the class
        :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`, is equal to
        ``max_num_steps_of_stagnation-1``.
    improvement_threshold : `float`, optional
        Same as the parameter ``threshold`` of the custom PyTorch learning rate
        scheduler class, which is the same as that of the class
        :class:`torch.optim.lr_scheduler.ReduceLROnPlateau`.
    averaging_window_in_steps : `int`, optional
        The number of the most recent mini-batches of the phase wherein the
        global learning rate multiplier is updated that are used to calculate
        the performance metric to determine whether an improvement has occurred 
        or not.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("ml_optimizer",
                        "total_num_steps",
                        "reduction_factor",
                        "max_num_steps_of_stagnation",
                        "improvement_threshold",
                        "averaging_window_in_steps")
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
                 ml_optimizer=\
                 _default_ml_optimizer,
                 total_num_steps=\
                 _default_total_num_steps,
                 reduction_factor=\
                 _default_reduction_factor,
                 max_num_steps_of_stagnation=\
                 _default_max_num_steps_of_stagnation,
                 improvement_threshold=\
                 _default_improvement_threshold,
                 averaging_window_in_steps=\
                 _default_averaging_window_in_steps,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        kwargs = {"torch_ml_optimizer": \
                  self._torch_ml_optimizer,
                  "reduction_factor": \
                  self_core_attrs["reduction_factor"],
                  "max_num_steps_of_stagnation": \
                  self_core_attrs["max_num_steps_of_stagnation"],
                  "improvement_threshold": \
                  self_core_attrs["improvement_threshold"],
                  "averaging_window_in_steps": \
                  self_core_attrs["averaging_window_in_steps"]}
        torch_lr_scheduler = _TorchReduceOnPlateau(**kwargs)
        self._torch_lr_scheduler = torch_lr_scheduler

        return None



_module_alias = emicroml.modelling.optimizers
_default_weight_decay = _module_alias._default_weight_decay



cls_alias = torch.optim.lr_scheduler._LRScheduler
class _TorchCosineAnnealingWithWarmRestarts(cls_alias):
    def __init__(self,
                 torch_ml_optimizer,
                 num_steps_in_first_cycle,
                 cycle_period_scale_factor,
                 min_lr_in_first_cycle,
                 multiplicative_decay_factor):
        cls_alias = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts
        kwargs = {"optimizer": torch_ml_optimizer,
                  "T_0": num_steps_in_first_cycle,
                  "T_mult": cycle_period_scale_factor,
                  "eta_min": min_lr_in_first_cycle}
        self._base_torch_lr_scheduler = cls_alias(**kwargs)

        self._cycle_period_scale_factor = cycle_period_scale_factor
        self._multiplicative_decay_factor = multiplicative_decay_factor
        self._cycle_idx = 0

        super().__init__(torch_ml_optimizer)

        return None



    def step(self,
             ml_loss_manager=_default_ml_loss_manager,
             phase=_default_phase,
             epoch=_default_epoch):
        self.last_epoch = self.last_epoch+1 if (epoch is None) else epoch

        torch_ml_optimizer = self.optimizer
        torch_ml_optimizer_param_group = torch_ml_optimizer.param_groups[-1]

        num_previous_steps_since_last_restart = \
            self._base_torch_lr_scheduler.T_cur
        total_num_steps_in_current_anneal_cycle = \
            self._base_torch_lr_scheduler.T_i
        
        cycle_period_scale_factor = self._cycle_period_scale_factor

        T_current = num_previous_steps_since_last_restart
        T_ith_cycle = total_num_steps_in_current_anneal_cycle

        if self.last_epoch > 0:
            if T_current+1 == T_ith_cycle:
                self._cycle_idx += 1

                key = "weight_decay"
                old_weight_decay = torch_ml_optimizer_param_group.get(key, -1)
                new_weight_decay = (old_weight_decay
                                    / (cycle_period_scale_factor)**0.5)
                torch_ml_optimizer_param_group[key] = new_weight_decay
                _ = (torch_ml_optimizer_param_group.pop(key)
                     if (old_weight_decay == -1)
                     else None)

            self._base_torch_lr_scheduler.step()

            torch_ml_optimizer_param_group["lr"] *= \
                self._multiplicative_decay_factor**self._cycle_idx
            
        self._last_lr = [torch_ml_optimizer_param_group["lr"]]

        return None



def _check_and_convert_num_steps_in_first_cycle(params):
    obj_name = "num_steps_in_first_cycle"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    num_steps_in_first_cycle = czekitout.convert.to_positive_int(**kwargs)

    return num_steps_in_first_cycle



def _pre_serialize_num_steps_in_first_cycle(num_steps_in_first_cycle):
    serializable_rep = num_steps_in_first_cycle
    
    return serializable_rep



def _de_pre_serialize_num_steps_in_first_cycle(serializable_rep):
    num_steps_in_first_cycle = serializable_rep

    return num_steps_in_first_cycle



def _check_and_convert_cycle_period_scale_factor(params):
    obj_name = "cycle_period_scale_factor"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    cycle_period_scale_factor = czekitout.convert.to_positive_int(**kwargs)

    return cycle_period_scale_factor



def _pre_serialize_cycle_period_scale_factor(cycle_period_scale_factor):
    serializable_rep = cycle_period_scale_factor
    
    return serializable_rep



def _de_pre_serialize_cycle_period_scale_factor(serializable_rep):
    cycle_period_scale_factor = serializable_rep

    return cycle_period_scale_factor



def _check_and_convert_min_lr_in_first_cycle(params):
    obj_name = "min_lr_in_first_cycle"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    min_lr_in_first_cycle = czekitout.convert.to_positive_float(**kwargs)

    return min_lr_in_first_cycle



def _pre_serialize_min_lr_in_first_cycle(min_lr_in_first_cycle):
    serializable_rep = min_lr_in_first_cycle
    
    return serializable_rep



def _de_pre_serialize_min_lr_in_first_cycle(serializable_rep):
    min_lr_in_first_cycle = serializable_rep

    return min_lr_in_first_cycle



_default_num_steps_in_first_cycle = 20
_default_cycle_period_scale_factor = 1
_default_min_lr_in_first_cycle = 1e-8



class CosineAnnealingWithWarmRestarts(BaseLRScheduler):
    r"""A wrapper to a custom PyTorch learning rate scheduler class based on 
    the class :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts`.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The aforementioned custom PyTorch learning rate scheduler class behaves just
    like the class
    :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts`, as described
    in the documentation of the latter, except for the following differences:
    
    1. The integer :math:`T_{cur}` introduced in the documentation of the class
    :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts` is redefined
    as the number of steps in the learning rate scheduler that have occurred
    since the beginning of the current annealing cycle.

    2. The integer :math:`T_{i}` introduced in the documentation of the class
    :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts` is redefined
    as the number of steps in the learning rate scheduler between the beginning
    of the current annealing cycle and the beginning of the next annealing
    cycle.

    3. The quantities :math:`\eta_{\min}` and :math:`\eta_{\max}` introduced in
    the documentation of the class
    :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts` are rescaled
    by the same nonnegative number :math:`\gamma`, i.e. :math:`\eta_{\min}
    \leftarrow \gamma \eta_{\min}` and :math:`\eta_{\max} \leftarrow \gamma
    \eta_{\max}`, after every restart.

    4. The weight decay coefficient :math:`\lambda` of the PyTorch optimizer
    being used in conjunction with the learning rate scheduler is rescaled by
    :math:`1/\sqrt{T_{i}}`, i.e. :math:`\lambda \leftarrow \lambda
    /\sqrt{T_{i}}`, after every restart.

    Parameters
    ----------
    ml_optimizer : :class:`emicroml.modelling.optimizers.Generic` | `None`, optional
        ``ml_optimizer`` specifies the generic wrapper to the PyTorch optimizer
        class to use in conjunction with the learning rate scheduler. This
        parameter implicitly determines the parameter ``optimizer`` of the
        custom PyTorch learning rate scheduler class, which is the same as that
        of the class
        :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts`. If
        ``ml_optimizer`` is set to ``None``, then the parameter will be
        reassigned to the value ``emicroml.modelling.optimizers.Generic()``.
    total_num_steps : `int`, optional
        The total number of steps in the learning rate
        scheduler. ``total_num_steps`` is equal to the total number of times the
        global learning rate multiplier is updated after initialization. 
    num_steps_in_first_cycle : `int`, optional
        The number of steps in the learning rate scheduler between the beginning
        of the first annealing cycle and the beginning of the second annealing
        cycle.
    cycle_period_scale_factor : `int`, optional
        Same as the parameter ``T_mult`` of the custom PyTorch learning rate
        scheduler class, which is the same as that of the class
        :class:`torch.optim.lr_scheduler.CosineAnnealingWarmRestarts`.
    min_lr_in_first_cycle : `float`, optional
        The quantity :math:`\eta_{\min}`.
    multiplicative_decay_factor : `float`, optional
        The multiplicative decay factor :math:`\gamma`.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("ml_optimizer",
                        "total_num_steps",
                        "num_steps_in_first_cycle",
                        "cycle_period_scale_factor",
                        "min_lr_in_first_cycle",
                        "multiplicative_decay_factor")
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
                 ml_optimizer=\
                 _default_ml_optimizer,
                 total_num_steps=\
                 _default_total_num_steps,
                 num_steps_in_first_cycle=\
                 _default_num_steps_in_first_cycle,
                 cycle_period_scale_factor=\
                 _default_cycle_period_scale_factor,
                 min_lr_in_first_cycle=\
                 _default_min_lr_in_first_cycle,
                 multiplicative_decay_factor=\
                 _default_multiplicative_decay_factor,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        kwargs = {"torch_ml_optimizer": \
                  self._torch_ml_optimizer,
                  "num_steps_in_first_cycle": \
                  self_core_attrs["num_steps_in_first_cycle"],
                  "cycle_period_scale_factor": \
                  self_core_attrs["cycle_period_scale_factor"],
                  "min_lr_in_first_cycle": \
                  self_core_attrs["min_lr_in_first_cycle"],
                  "multiplicative_decay_factor": \
                  self_core_attrs["multiplicative_decay_factor"]}
        torch_lr_scheduler = _TorchCosineAnnealingWithWarmRestarts(**kwargs)
        self._torch_lr_scheduler = torch_lr_scheduler

        return None



_non_sequential_lr_scheduler_name_to_cls_map = \
    {"constant": Constant,
     "linear": Linear,
     "exponential": Exponential,
     "reduce_on_plateau": ReduceOnPlateau,
     "cosine_annealing_with_warm_restarts": CosineAnnealingWithWarmRestarts}



def _check_and_convert_lr_scheduler_name_v1(params):
    key = "expecting_only_a_non_sequential_lr_scheduler"
    params[key] = True
    
    lr_scheduler_name = _check_and_convert_lr_scheduler_name(params)

    return lr_scheduler_name



def _check_and_convert_lr_scheduler_name(params):
    obj_name = "lr_scheduler_name"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    obj = czekitout.convert.to_str_from_str_like(**kwargs)

    key = "expecting_only_a_non_sequential_lr_scheduler"
    expecting_only_a_non_sequential_lr_scheduler = params[key]
    del params[key]

    # ``_generic_lr_scheduler_name_to_cls_map`` is defined further below.
    accepted_strings = (_non_sequential_lr_scheduler_name_to_cls_map.keys()
                        if expecting_only_a_non_sequential_lr_scheduler
                        else _generic_lr_scheduler_name_to_cls_map.keys())

    kwargs["obj"] = obj
    kwargs["accepted_strings"] = accepted_strings
    czekitout.check.if_one_of_any_accepted_strings(**kwargs)

    lr_scheduler_name = obj

    return lr_scheduler_name



def _pre_serialize_lr_scheduler_name_v1(lr_scheduler_name):
    obj_to_pre_serialize = lr_scheduler_name
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_name_v1(serializable_rep):
    lr_scheduler_name = serializable_rep

    return lr_scheduler_name



def _check_and_convert_lr_scheduler_params_v1(params):
    key = "expecting_only_a_non_sequential_lr_scheduler"
    params[key] = True
    
    lr_scheduler_params = _check_and_convert_lr_scheduler_params(params)

    return lr_scheduler_params



def _check_and_convert_lr_scheduler_params(params):
    obj_name = "lr_scheduler_params"
    obj = params[obj_name]

    key = "expecting_only_a_non_sequential_lr_scheduler"
    expecting_only_a_non_sequential_lr_scheduler = params[key]
    del params[key]
    
    lr_scheduler_name = (_check_and_convert_lr_scheduler_name_v1(params)
                         if expecting_only_a_non_sequential_lr_scheduler
                         else _check_and_convert_lr_scheduler_name_v2(params))    
    lr_scheduler_cls = _generic_lr_scheduler_name_to_cls_map[lr_scheduler_name]

    accepted_types = (dict, type(None))

    current_func_name = "_check_and_convert_lr_scheduler_params"
    
    if isinstance(obj, accepted_types[-1]):
        lr_scheduler_params = lr_scheduler_cls().get_core_attrs(deep_copy=False)
    else:
        kwargs = {"obj": obj,
                  "obj_name": obj_name,
                  "accepted_types": accepted_types}
        czekitout.check.if_instance_of_any_accepted_types(**kwargs)

        try:
            lr_scheduler_cls(**obj)
        except:
            err_msg = globals()[current_func_name+"_err_msg_1"]
            raise ValueError(err_msg)

        lr_scheduler_params = obj

    return lr_scheduler_params



def _pre_serialize_lr_scheduler_params_v1(lr_scheduler_params):
    serializable_rep = dict()
        
    for param_name in lr_scheduler_params:
        if param_name == "non_sequential_lr_schedulers":
            lr_schedulers = lr_scheduler_params[param_name]
            pre_serialized_lr_schedulers = tuple()
                
            for lr_scheduler in lr_schedulers:
                pre_serialized_lr_scheduler = lr_scheduler.pre_serialize()
                pre_serialized_lr_schedulers += (pre_serialized_lr_scheduler,)
                    
            serializable_rep[param_name] = pre_serialized_lr_schedulers
        else:
            param = lr_scheduler_params[param_name]
            serializable_rep[param_name] = (param.pre_serialize()
                                            if (param_name == "ml_optimizer")
                                            else param)
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_params_v1(serializable_rep):
    lr_scheduler_params = dict()
        
    for param_name in serializable_rep:
        if param_name == "non_sequential_lr_schedulers":
            pre_serialized_lr_schedulers = serializable_rep[param_name]
            lr_schedulers = tuple()
                
            for pre_serialized_lr_scheduler in pre_serialized_lr_schedulers:
                module_alias = \
                    emicroml.modelling.lr.schedulers
                lr_scheduler_cls = \
                    module_alias.Nonsequential
                method_alias = \
                    lr_scheduler_cls.de_pre_serialize
                lr_scheduler = \
                    method_alias(pre_serialized_lr_scheduler)
                lr_schedulers += \
                    (lr_scheduler,)
                    
            lr_scheduler_params[param_name] = lr_schedulers
        else:
            serialized_rep_of_param = serializable_rep[param_name]
        
            if param_name == "ml_optimizer":
                module_alias = \
                    emicroml.modelling.optimizers
                lr_scheduler_cls = \
                    module_alias.Generic
                param = \
                    lr_scheduler_cls.de_pre_serialize(serialized_rep_of_param)
            else:
                param = \
                    serialized_rep_of_param
            
            lr_scheduler_params[param_name] = param

    return lr_scheduler_params



_default_lr_scheduler_name = "constant"
_default_lr_scheduler_params = None



class Nonsequential(BaseLRScheduler):
    r"""A wrapper to a nonsequential PyTorch learning rate scheduler class.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The parameters of the current class specify an instance of one of the other
    public classes defined in the module
    :mod:`emicroml.modelling.lr.schedulers`, with the other public class being a
    wrapper to a specific nonsequential PyTorch learning rate scheduler. Let
    ``specific_wrapper_cls`` be the other public class.

    Parameters
    ----------
    lr_scheduler_name : "constant" | "linear" | "reduce_on_plateau" | "cosine_annealing_with_warm_restarts", optional
        The name associated with
        ``specific_wrapper_cls``. ``specific_wrapper_cls`` is determined by the
        value of ``lr_scheduler_name``:

        * If ``lr_scheduler_name`` is set to ``"constant"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.Constant`.

        * If ``lr_scheduler_name`` is set to ``"linear"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.Linear`.

        * If ``lr_scheduler_name`` is set to ``"reduce_on_plateau"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.ReduceOnPlateau`.

        * If ``lr_scheduler_name`` is set to
          ``"cosine_annealing_with_warm_restarts"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.CosineAnnealingWithWarmRestarts`.

    lr_scheduler_params : `dict` | `None`, optional
        ``lr_scheduler_params`` specifies the parameters of
        ``specific_wrapper_cls`` used to construct an instance of itself. If
        ``lr_scheduler_params`` is set to ``None``, then the instance is
        constructed by ``specific_wrapper_cls()``. Otherwise, the instance is
        constructed by ``specific_wrapper_cls(**lr_scheduler_params)``.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    _validation_and_conversion_funcs_ = \
        {"lr_scheduler_name": _check_and_convert_lr_scheduler_name_v1,
         "lr_scheduler_params": _check_and_convert_lr_scheduler_params_v1}

    _pre_serialization_funcs_ = \
        {"lr_scheduler_name": _pre_serialize_lr_scheduler_name_v1,
         "lr_scheduler_params": _pre_serialize_lr_scheduler_params_v1}

    _de_pre_serialization_funcs_ = \
        {"lr_scheduler_name": _de_pre_serialize_lr_scheduler_name_v1,
         "lr_scheduler_params": _de_pre_serialize_lr_scheduler_params_v1}

    

    def __init__(self,
                 lr_scheduler_name=\
                 _default_lr_scheduler_name,
                 lr_scheduler_params=\
                 _default_lr_scheduler_params,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        map_alias = _non_sequential_lr_scheduler_name_to_cls_map
        key = self_core_attrs["lr_scheduler_name"]
        lr_scheduler_cls = map_alias[key]

        kwargs = self_core_attrs["lr_scheduler_params"]
        lr_scheduler = lr_scheduler_cls(**kwargs)

        lr_scheduler._torch_ml_optimizer = self._torch_ml_optimizer

        lr_scheduler._generate_and_store_torch_lr_scheduler()

        self._torch_lr_scheduler = lr_scheduler._torch_lr_scheduler

        return None



    @property
    def total_num_steps(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        lr_scheduler_params = self_core_attrs["lr_scheduler_params"]
        result = lr_scheduler_params["total_num_steps"]
        
        return result



class _TorchSequential(torch.optim.lr_scheduler._LRScheduler):
    def __init__(self, torch_ml_optimizer, non_sequential_lr_schedulers):
        self._base_torch_lr_schedulers = tuple()
        self._milestones = (0,)

        torch_ml_optimizer_param_group = torch_ml_optimizer.param_groups[-1]
        self.base_lr = torch_ml_optimizer_param_group["lr"]

        for lr_scheduler in non_sequential_lr_schedulers:
            torch_ml_optimizer_param_group["lr"] = self.base_lr
            lr_scheduler._torch_ml_optimizer = torch_ml_optimizer

            lr_scheduler._generate_and_store_torch_lr_scheduler()
            
            base_torch_lr_scheduler = lr_scheduler._torch_lr_scheduler
            self._base_torch_lr_schedulers += (base_torch_lr_scheduler,)
            
            milestone = lr_scheduler.total_num_steps + self._milestones[-1] + 1
            self._milestones += (milestone,)

        key = "weight_decay"
        self._initial_weight_decay = (torch_ml_optimizer_param_group[key]
                                      if (key in torch_ml_optimizer_param_group)
                                      else None)

        super().__init__(torch_ml_optimizer)

        return None



    def step(self,
             ml_loss_manager=_default_ml_loss_manager,
             phase=_default_phase,
             epoch=_default_epoch):
        self.last_epoch = self.last_epoch+1 if (epoch is None) else epoch

        for milestone_idx, _ in enumerate(self._milestones[:-1]):
            interval = (self._milestones[milestone_idx],
                        self._milestones[milestone_idx+1])
            
            if interval[0] <= self.last_epoch < interval[1]:
                base_torch_lr_scheduler = \
                    self._base_torch_lr_schedulers[milestone_idx]

                if interval[0] == self.last_epoch:
                    torch_ml_optimizer = \
                        self.optimizer
                    torch_ml_optimizer_param_group = \
                        torch_ml_optimizer.param_groups[-1]
                    torch_ml_optimizer_param_group["lr"] = \
                        base_torch_lr_scheduler.get_last_lr()[-1]

                    key = "weight_decay"
                    initial_weight_decay = self._initial_weight_decay
                    torch_ml_optimizer_param_group[key] = initial_weight_decay
                    _ = (torch_ml_optimizer_param_group.pop(key)
                         if (self._initial_weight_decay is None)
                         else None)
                        
                else:
                    base_step_func = \
                        base_torch_lr_scheduler.step
                    base_step_func_co_varnames = \
                        base_step_func.__code__.co_varnames

                    kwargs = {"ml_loss_manager": ml_loss_manager,
                              "phase": phase,
                              "epoch": None}
                    for key in tuple(kwargs.keys()):
                        if key not in base_step_func_co_varnames:
                            del kwargs[key]

                    base_step_func(**kwargs)
                    break

        self._last_lr = base_torch_lr_scheduler._last_lr

        return None



def _check_and_convert_non_sequential_lr_schedulers(params):
    obj_name = "non_sequential_lr_schedulers"
    obj = params[obj_name]

    accepted_types = (Nonsequential, type(None))

    params["name_of_obj_alias_of_lr_scheduler"] = \
        "non_sequential_lr_scheduler"
    params["accepted_nontrivial_cls_of_obj_alias_of_lr_scheduler"] = \
        accepted_types[0]

    current_func_name = "_check_and_convert_non_sequential_lr_schedulers"

    if isinstance(obj, accepted_types[-1]):
        non_sequential_lr_schedulers = (accepted_types[0](),)
    else:
        try:
            non_sequential_lr_schedulers = tuple()

            for non_sequential_lr_scheduler in obj:
                if non_sequential_lr_scheduler is None:
                    err_msg = globals()[current_func_name+"_err_msg_1"]
                    raise ValueError(err_msg)

                params["lr_scheduler"] = non_sequential_lr_scheduler
                
                lr_scheduler = _check_and_convert_lr_scheduler(params)
                non_sequential_lr_schedulers += (lr_scheduler,)

                del params["lr_scheduler"]

            if len(non_sequential_lr_schedulers) == 0:
                err_msg = globals()[current_func_name+"_err_msg_2"]
                raise ValueError(err_msg)

        except:
            err_msg = globals()[current_func_name+"_err_msg_3"]
            raise ValueError(err_msg)

    del params["name_of_obj_alias_of_lr_scheduler"]
    del params["accepted_nontrivial_cls_of_obj_alias_of_lr_scheduler"]

    return non_sequential_lr_schedulers



def _check_and_convert_lr_scheduler(params):
    obj_name = "lr_scheduler"
    obj = params[obj_name]

    name_of_obj_alias_of_lr_scheduler = \
        params["name_of_obj_alias_of_lr_scheduler"]
    accepted_nontrivial_cls = \
        params["accepted_nontrivial_cls_of_obj_alias_of_lr_scheduler"]
    
    accepted_types = (accepted_nontrivial_cls,)
    
    kwargs = {"obj": obj,
              "obj_name": name_of_obj_alias_of_lr_scheduler,
              "accepted_types": accepted_types}
    czekitout.check.if_instance_of_any_accepted_types(**kwargs)

    kwargs = obj.get_core_attrs(deep_copy=False)
    lr_scheduler = accepted_types[0](**kwargs)
    lr_scheduler._lr_step_idx = obj._lr_step_idx
    lr_scheduler._lr_schedule = obj._lr_schedule
    lr_scheduler._torch_lr_scheduler = obj._torch_lr_scheduler

    return lr_scheduler



def _pre_serialize_non_sequential_lr_schedulers(non_sequential_lr_schedulers):
    obj_to_pre_serialize = non_sequential_lr_schedulers

    serializable_rep = tuple()
    for non_sequential_lr_scheduler in obj_to_pre_serialize:
        serializable_rep += (non_sequential_lr_scheduler.pre_serialize(),)
    
    return serializable_rep



def _de_pre_serialize_non_sequential_lr_schedulers(serializable_rep):
    non_sequential_lr_schedulers = \
        tuple()
    for serialized_non_sequential_lr_scheduler in serializable_rep:
        cls = \
            Nonsequential
        non_sequential_lr_scheduler = \
            cls.de_pre_serialize(serialized_non_sequential_lr_scheduler)
        non_sequential_lr_schedulers += \
            (non_sequential_lr_scheduler,)

    return non_sequential_lr_schedulers



_default_non_sequential_lr_schedulers = None



class Sequential(BaseLRScheduler):
    r"""A wrapper to a sequential PyTorch learning rate scheduler class.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    Parameters
    ----------
    non_sequential_lr_schedulers : `array_like` (:class:`emicroml.modelling.lr.schedulers.Nonsequential`, ndim=1) | `None`, optional
        The sequence of nonsequential learning rate schedulers which defines the
        schedule of the sequential learning rate scheduler. The schedule of the
        sequential scheduler can be described by the following list of
        instructions:

        1. Set ``scheduler_idx`` to ``-1``.

        2. Set ``scheduler_idx`` to ``scheduler_idx+1``.

        3. Set ``non_sequential_lr_scheduler`` to
        ``non_sequential_lr_schedulers[scheduler_idx]``.

        4. Set the current global learning rate multiplier of the sequential
        scheduler to the initial global learning rate multiplier of
        ``non_sequential_lr_scheduler``.

        5. For the next ``non_sequential_lr_scheduler.total_num_steps`` steps,
        update the current global learning rate multiplier of the sequential
        scheduler according to the schedule of ``non_sequential_lr_scheduler``.

        6. If ``scheduler_idx<len(non_sequential_lr_schedulers)-1`` then take
        another step in the sequential scheduler, and go to instruction 2,
        deferring the update of the global learning rate multiplier of the
        sequential scheduler until instruction 4. Otherwise, stop.

    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    ctor_param_names = ("non_sequential_lr_schedulers",)
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
                 non_sequential_lr_schedulers=\
                 _default_non_sequential_lr_schedulers,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_ml_optimizer(self, ml_model_param_group):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        non_sequential_lr_schedulers = \
            self_core_attrs["non_sequential_lr_schedulers"]
        non_sequential_lr_scheduler = \
            non_sequential_lr_schedulers[0]
        non_sequential_lr_scheduler_core_attrs = \
            non_sequential_lr_scheduler.get_core_attrs(deep_copy=False)
        non_sequential_lr_scheduler_params = \
            non_sequential_lr_scheduler_core_attrs["lr_scheduler_params"]
        ml_optimizer = \
            non_sequential_lr_scheduler_params["ml_optimizer"]

        cached_obj = ml_optimizer._torch_ml_optimizer

        kwargs = {"ml_model_param_group": ml_model_param_group}
        ml_optimizer._generate_and_store_torch_ml_optimizer(**kwargs)

        self._torch_ml_optimizer = ml_optimizer._torch_ml_optimizer

        ml_optimizer._torch_ml_optimizer = cached_obj

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        kwargs = {"torch_ml_optimizer": \
                  self._torch_ml_optimizer,
                  "non_sequential_lr_schedulers": \
                  self_core_attrs["non_sequential_lr_schedulers"]}
        self._torch_lr_scheduler = _TorchSequential(**kwargs)

        return None



    @property
    def total_num_steps(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        non_sequential_lr_schedulers = \
            self_core_attrs["non_sequential_lr_schedulers"]

        result = -1
        for non_sequential_lr_scheduler in non_sequential_lr_schedulers:
            result += non_sequential_lr_scheduler.total_num_steps+1
        
        return result



_generic_lr_scheduler_name_to_cls_map = \
    {**_non_sequential_lr_scheduler_name_to_cls_map,
     "sequential": Sequential}



def _check_and_convert_lr_scheduler_name_v2(params):
    key = "expecting_only_a_non_sequential_lr_scheduler"
    params[key] = False
    
    lr_scheduler_name = _check_and_convert_lr_scheduler_name(params)

    return lr_scheduler_name



def _pre_serialize_lr_scheduler_name_v2(lr_scheduler_name):
    obj_to_pre_serialize = lr_scheduler_name
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_name_v2(serializable_rep):
    lr_scheduler_name = _de_pre_serialize_lr_scheduler_name_v1(serializable_rep)

    return lr_scheduler_name



def _check_and_convert_lr_scheduler_params_v2(params):
    key = "expecting_only_a_non_sequential_lr_scheduler"
    params[key] = False
    
    lr_scheduler_params = _check_and_convert_lr_scheduler_params(params)

    return lr_scheduler_params



def _pre_serialize_lr_scheduler_params_v2(lr_scheduler_params):
    serializable_rep = \
        _pre_serialize_lr_scheduler_params_v1(lr_scheduler_params)
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_params_v2(serializable_rep):
    lr_scheduler_params = \
        _de_pre_serialize_lr_scheduler_params_v1(serializable_rep)

    return lr_scheduler_params



class Generic(BaseLRScheduler):
    r"""A generic wrapper to a PyTorch learning rate scheduler class.

    The current class is a subclass of
    :class:`fancytypes.PreSerializableAndUpdatable`.

    The parameters of the current class specify an instance of one of the other
    public classes defined in the module
    :mod:`emicroml.modelling.lr.schedulers`, with the other public class being a
    wrapper to a specific PyTorch learning rate scheduler. Let
    ``specific_wrapper_cls`` be the other public class.

    Parameters
    ----------
    lr_scheduler_name : "constant" | "linear" | "exponential" | "reduce_on_plateau" | "cosine_annealing_with_warm_restarts" | "sequential", optional
        The name associated with
        ``specific_wrapper_cls``. ``specific_wrapper_cls`` is determined by the
        value of ``lr_scheduler_name``:

        * If ``lr_scheduler_name`` is set to ``"constant"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.Constant`.

        * If ``lr_scheduler_name`` is set to ``"linear"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.Linear`.

        * If ``lr_scheduler_name`` is set to ``"reduce_on_plateau"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.ReduceOnPlateau`.

        * If ``lr_scheduler_name`` is set to
          ``"cosine_annealing_with_warm_restarts"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.CosineAnnealingWithWarmRestarts`.

        * If ``lr_scheduler_name`` is set to ``"sequential"``, then
          ``specific_wrapper_cls`` is the class
          :class:`emicroml.modelling.lr.schedulers.Sequential`.

    lr_scheduler_params : `dict` | `None`, optional
        ``lr_scheduler_params`` specifies the parameters of
        ``specific_wrapper_cls`` used to construct an instance of itself. If
        ``lr_scheduler_params`` is set to ``None``, then the instance is
        constructed by ``specific_wrapper_cls()``. Otherwise, the instance is
        constructed by ``specific_wrapper_cls(**lr_scheduler_params)``.
    skip_validation_and_conversion : `bool`, optional
        Let ``validation_and_conversion_funcs`` and ``core_attrs`` denote the
        attributes :attr:`~fancytypes.Checkable.validation_and_conversion_funcs`
        and :attr:`~fancytypes.Checkable.core_attrs` respectively, both of which
        being `dict` objects.

        Let ``params_to_be_mapped_to_core_attrs`` denote the `dict`
        representation of the constructor parameters excluding the parameter
        ``skip_validation_and_conversion``, where each `dict` key ``key`` is a
        different constructor parameter name, excluding the name
        ``"skip_validation_and_conversion"``, and
        ``params_to_be_mapped_to_core_attrs[key]`` would yield the value of the
        constructor parameter with the name given by ``key``.

        If ``skip_validation_and_conversion`` is set to ``False``, then for each
        key ``key`` in ``params_to_be_mapped_to_core_attrs``,
        ``core_attrs[key]`` is set to ``validation_and_conversion_funcs[key]
        (params_to_be_mapped_to_core_attrs)``.

        Otherwise, if ``skip_validation_and_conversion`` is set to ``True``,
        then ``core_attrs`` is set to
        ``params_to_be_mapped_to_core_attrs.copy()``. This option is desired
        primarily when the user wants to avoid potentially expensive deep copies
        and/or conversions of the `dict` values of
        ``params_to_be_mapped_to_core_attrs``, as it is guaranteed that no
        copies or conversions are made in this case.

    """
    _validation_and_conversion_funcs_ = \
        {"lr_scheduler_name": _check_and_convert_lr_scheduler_name_v2,
         "lr_scheduler_params": _check_and_convert_lr_scheduler_params_v2}

    _pre_serialization_funcs_ = \
        {"lr_scheduler_name": _pre_serialize_lr_scheduler_name_v2,
         "lr_scheduler_params": _pre_serialize_lr_scheduler_params_v2}

    _de_pre_serialization_funcs_ = \
        {"lr_scheduler_name": _de_pre_serialize_lr_scheduler_name_v2,
         "lr_scheduler_params": _de_pre_serialize_lr_scheduler_params_v2}

    

    def __init__(self,
                 lr_scheduler_name=\
                 _default_lr_scheduler_name,
                 lr_scheduler_params=\
                 _default_lr_scheduler_params,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        BaseLRScheduler.__init__(self, ctor_params)

        return None



    def _generate_and_store_torch_ml_optimizer(self, ml_model_param_group):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        map_alias = _generic_lr_scheduler_name_to_cls_map
        key = self_core_attrs["lr_scheduler_name"]
        lr_scheduler_cls = map_alias[key]

        kwargs = self_core_attrs["lr_scheduler_params"]
        lr_scheduler = lr_scheduler_cls(**kwargs)

        kwargs = {"ml_model_param_group": ml_model_param_group}
        lr_scheduler._generate_and_store_torch_ml_optimizer(**kwargs)

        self._torch_ml_optimizer = lr_scheduler._torch_ml_optimizer

        return None



    def _generate_and_store_torch_lr_scheduler(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        map_alias = _generic_lr_scheduler_name_to_cls_map
        key = self_core_attrs["lr_scheduler_name"]
        lr_scheduler_cls = map_alias[key]

        kwargs = self_core_attrs["lr_scheduler_params"]
        lr_scheduler = lr_scheduler_cls(**kwargs)

        lr_scheduler._torch_ml_optimizer = self._torch_ml_optimizer

        lr_scheduler._generate_and_store_torch_lr_scheduler()

        self._torch_lr_scheduler = lr_scheduler._torch_lr_scheduler

        return None



    @property
    def total_num_steps(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        lr_scheduler_name = self_core_attrs["lr_scheduler_name"]
        lr_scheduler_params = self_core_attrs["lr_scheduler_params"]

        if lr_scheduler_name == "sequential":
            key = "non_sequential_lr_schedulers"
            non_sequential_lr_schedulers = lr_scheduler_params[key]

            result = 0
            for non_sequential_lr_scheduler in non_sequential_lr_schedulers:
                result += non_sequential_lr_scheduler.total_num_steps
        else:
            result = lr_scheduler_params["total_num_steps"]
        
        return result



def _check_and_convert_lr_schedulers(params):
    obj_name = "lr_schedulers"
    obj = params[obj_name]

    accepted_types = (Generic, type(None))

    params["name_of_obj_alias_of_lr_scheduler"] = \
        "lr_scheduler"
    params["accepted_nontrivial_cls_of_obj_alias_of_lr_scheduler"] = \
        accepted_types[0]

    current_func_name = "_check_and_convert_lr_schedulers"
    
    if isinstance(obj, accepted_types[-1]):
        lr_schedulers = (accepted_types[0](),)
    else:
        try:
            lr_schedulers = tuple()            
            total_num_steps = None

            for lr_scheduler in obj:
                if lr_scheduler is None:
                    err_msg = globals()[current_func_name+"_err_msg_1"]
                    raise ValueError(err_msg)

                params["lr_scheduler"] = lr_scheduler

                lr_scheduler = _check_and_convert_lr_scheduler(params)
                lr_schedulers += (lr_scheduler,)

                total_num_steps = (lr_scheduler.total_num_steps
                                   if (total_num_steps is None)
                                   else total_num_steps)
                if total_num_steps != lr_scheduler.total_num_steps:
                    err_msg = globals()[current_func_name+"_err_msg_2"]
                    raise ValueError(err_msg)

                del params["lr_scheduler"]

            if len(obj) == 0:
                err_msg = globals()[current_func_name+"_err_msg_3"]
                raise ValueError(err_msg)

        except:
            err_msg = globals()[current_func_name+"_err_msg_4"]
            raise ValueError(err_msg)

    del params["name_of_obj_alias_of_lr_scheduler"]
    del params["accepted_nontrivial_cls_of_obj_alias_of_lr_scheduler"]

    return lr_schedulers



def _pre_serialize_lr_schedulers(lr_schedulers):
    serializable_rep = tuple()
    for lr_scheduler in lr_schedulers:
        serializable_rep += (lr_scheduler.pre_serialize(),)
    
    return serializable_rep



def _de_pre_serialize_lr_schedulers(serializable_rep):
    lr_schedulers = tuple()
    for serialized_lr_scheduler in serializable_rep:
        lr_scheduler_cls = \
            Generic
        lr_scheduler = \
            lr_scheduler_cls.de_pre_serialize(serialized_lr_scheduler)
        lr_schedulers += \
            (lr_scheduler,)

    return lr_schedulers



_default_lr_schedulers = None



###########################
## Define error messages ##
###########################

_base_lr_scheduler_err_msg_1 = \
    ("Cannot construct instances of the class "
     "`emicroml.modelling.lr.schedulers.BaseLRScheduler`, only subclasses of "
     "itself defined in the `emicroml.modelling.lr.schedulers` module.")

_check_and_convert_lr_scheduler_params_err_msg_1 = \
    ("The object ``lr_scheduler_params`` does not specify a valid set of "
     "learning scheduler parameters: see traceback for details.")

_check_and_convert_non_sequential_lr_schedulers_err_msg_1 = \
    ("An element in the sequence ``non_sequential_lr_schedulers`` was set to "
     "``None``.")
_check_and_convert_non_sequential_lr_schedulers_err_msg_2 = \
    ("The object ``non_sequential_lr_schedulers`` is an empty sequence.")
_check_and_convert_non_sequential_lr_schedulers_err_msg_3 = \
    ("The object ``non_sequential_lr_schedulers`` must be a nonempty sequence "
     "of `emicroml.modelling.lr.schedulers.Nonsequential` objects.")

_check_and_convert_lr_schedulers_err_msg_1 = \
    ("An element in the sequence ``lr_schedulers`` was set to ``None``.")
_check_and_convert_lr_schedulers_err_msg_2 = \
    ("Each element ``lr_scheduler`` in the object ``lr_schedulers`` must share "
     "the same value of the attribute ``total_num_steps``.")
_check_and_convert_lr_schedulers_err_msg_3 = \
    ("The object ``lr_schedulers`` is an empty sequence.")
_check_and_convert_lr_schedulers_err_msg_4 = \
    ("The object ``lr_schedulers`` must be of the type `NoneType` or be a "
     "nonempty sequence of `emicroml.modelling.lr.schedulers.Generic` objects, "
     "where the value of the attribute ``total_num_steps`` is the same for "
     "each element ``lr_scheduler`` of said sequence.")
