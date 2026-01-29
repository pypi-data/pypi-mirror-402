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
"""For creating and managing learning rate schedulers.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For validating and converting objects.
import czekitout.check
import czekitout.convert

# For defining classes that support enforced validation, updatability,
# pre-serialization, and de-serialization.
import fancytypes



# For reusing module-wide constants.
import emicroml.modelling.optimizers

# For validating, pre-serializing, and de-pre-serializing learning rate
# schedulers.
import emicroml.modelling.lr.schedulers



##################################
## Define classes and functions ##
##################################

# List of public objects in subpackage.
__all__ = ["schedulers",
           "LRSchedulerManager"]



def _check_and_convert_lr_schedulers(params):
    module_alias = emicroml.modelling.lr.schedulers
    func_alias = module_alias._check_and_convert_lr_schedulers
    lr_schedulers = func_alias(params)

    return lr_schedulers



def _pre_serialize_lr_schedulers(lr_schedulers):
    module_alias = emicroml.modelling.lr.schedulers
    func_alias = module_alias._pre_serialize_lr_schedulers
    serializable_rep = func_alias(lr_schedulers)
    
    return serializable_rep



def _de_pre_serialize_lr_schedulers(serializable_rep):
    module_alias = emicroml.modelling.lr.schedulers
    func_alias = module_alias._de_pre_serialize_lr_schedulers
    lr_schedulers = func_alias(serializable_rep)

    return lr_schedulers



def _check_and_convert_phase_in_which_to_update_lr(params):
    obj_name = "phase_in_which_to_update_lr"
    kwargs = {"obj": params[obj_name], "obj_name": obj_name}
    obj = czekitout.convert.to_str_from_str_like(**kwargs)

    accepted_strings = ("training", "validation")

    kwargs["obj"] = obj
    kwargs["accepted_strings"] = accepted_strings
    czekitout.check.if_one_of_any_accepted_strings(**kwargs)

    phase_in_which_to_update_lr = obj

    return phase_in_which_to_update_lr



def _pre_serialize_phase_in_which_to_update_lr(phase_in_which_to_update_lr):
    obj_to_pre_serialize = phase_in_which_to_update_lr
    serializable_rep = obj_to_pre_serialize
    
    return serializable_rep



def _de_pre_serialize_phase_in_which_to_update_lr(serializable_rep):
    phase_in_which_to_update_lr = serializable_rep

    return phase_in_which_to_update_lr



_module_alias_1 = \
    schedulers
_module_alias_2 = \
    emicroml.modelling.optimizers
_default_lr_schedulers = \
    _module_alias_1._default_lr_schedulers
_default_phase_in_which_to_update_lr = \
    "validation"
_default_skip_validation_and_conversion = \
    _module_alias_2._default_skip_validation_and_conversion



class LRSchedulerManager(fancytypes.PreSerializableAndUpdatable):
    r"""A learning rate scheduler manager.

    Users may want to subject different subsets of machine learning model (ML)
    fitting parameters to different learning rate schedulers. This can be
    achieved using a learning rate scheduler manager, which specifies a set of
    learning rate schedulers, with each one affecting a different subset of ML
    model fitting parameters.

    A learning rate scheduler manager also specifies whether the global learning
    rate multiplier of each learning rate scheduler is updated in the training
    or validation phase of each training-validation cycle, except the last. If
    the former, then each learning rate scheduler performs a single learning
    rate step/update at the end of each global optimization step, except the
    last. Otherwise, if the latter, then each learning rate scheduler performs a
    single learning rate step/update at the end of each validation phase, except
    the last. By global optimization step, we mean a single update applied to
    each ML model fitting parameter that is subject to updates during
    optimization.

    Parameters
    ----------
    lr_schedulers : `array_like` (:class:`emicroml.modelling.lr.schedulers.Generic`, ndim=1) | `None`, optional
        The set of learning rate schedulers. The total number of steps in each
        learning rate scheduler must be the same.
    phase_in_which_to_update_lr : "training" | "validation", optional
        This parameter specifies whether the global learning rate multiplier of
        each learning rate scheduler is updated in the training or validation
        phase of each training-validation cycle, except the last. If
        ``phase_in_which_to_update_lr`` is set to ``"training"`` then it is the
        former, otherwise it is the latter.
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
    ctor_param_names = ("lr_schedulers",
                        "phase_in_which_to_update_lr")
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
                 lr_schedulers=\
                 _default_lr_schedulers,
                 phase_in_which_to_update_lr=\
                 _default_phase_in_which_to_update_lr,
                 skip_validation_and_conversion=\
                 _default_skip_validation_and_conversion):
        ctor_params = {key: val
                       for key, val in locals().items()
                       if (key not in ("self", "__class__"))}
        kwargs = ctor_params
        kwargs["skip_cls_tests"] = True
        fancytypes.PreSerializableAndUpdatable.__init__(self, **kwargs)

        self.execute_post_core_attrs_update_actions()

        return None



    def execute_post_core_attrs_update_actions(self):
        self_core_attrs = self.get_core_attrs(deep_copy=False)

        self._lr_step_idx = \
            0
        self._lr_schedulers = \
            self_core_attrs["lr_schedulers"]
        self._phase_in_which_to_update_lr = \
            self_core_attrs["phase_in_which_to_update_lr"]
        self._total_num_steps = \
            self._lr_schedulers[0].total_num_steps

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



    def _generate_and_store_torch_ml_optimizers(self, ml_model_param_groups):
        for lr_scheduler_idx, lr_scheduler in enumerate(self._lr_schedulers):
            lr_scheduler._clear_torch_ml_optimizer()

            ml_model_param_group = ml_model_param_groups[lr_scheduler_idx]
            kwargs = {"ml_model_param_group": ml_model_param_group}
            lr_scheduler._generate_and_store_torch_ml_optimizer(**kwargs)

        return None



    def _generate_and_store_torch_lr_schedulers(self):
        for lr_scheduler in self._lr_schedulers:
            lr_scheduler._clear_torch_lr_scheduler()
            
            lr_scheduler._generate_and_store_torch_lr_scheduler()

        return None



    def _initialize_lr_schedules(self):
        self._lr_step_idx = 0
        for lr_scheduler in self._lr_schedulers:
            lr_scheduler._initialize_lr_schedule()

        return None



    @property
    def total_num_steps(self):
        r"""`int`: The total number of steps in each learning rate scheduler.

        ``total_num_steps`` is equal to the total number of times the global
        learning rate multiplier of the first learning rate scheduler is updated
        after its initialization, which is the same for every other learning
        rate scheduler specified by the manager. See also the documentation for
        the attribute
        :attr:`emicroml.modelling.lr.schedulers.Generic.total_num_steps`.

        Note that ``total_num_steps`` should be considered **read-only**.

        """
        result = self._total_num_steps
        
        return result



    def _step(self, ml_loss_manager):
        self._lr_step_idx += 1

        for lr_scheduler in self._lr_schedulers:
            kwargs = {"ml_loss_manager": ml_loss_manager,
                      "phase": self._phase_in_which_to_update_lr}
            lr_scheduler._step(**kwargs)

        return None



    def _save_lr_schedules(self, filename):
        for lr_scheduler_idx, lr_scheduler in enumerate(self._lr_schedulers):
            lr_schedule_idx = lr_scheduler_idx
            path_in_file = "lr_schedules/lr_schedule_{}".format(lr_schedule_idx)
            
            kwargs = {"filename": \
                      filename,
                      "path_in_file": \
                      path_in_file,
                      "phase_in_which_lr_steps_are_performed": \
                      self._phase_in_which_to_update_lr}
            lr_scheduler._save_lr_schedule(**kwargs)

        return None



def _check_and_convert_lr_scheduler_manager(params):
    obj_name = "lr_scheduler_manager"
    obj = params[obj_name]

    accepted_types = (LRSchedulerManager, type(None))
    
    if isinstance(obj, accepted_types[-1]):
        lr_scheduler_manager = accepted_types[0]()
    else:
        kwargs = {"obj": obj,
                  "obj_name": obj_name,
                  "accepted_types": accepted_types}
        czekitout.check.if_instance_of_any_accepted_types(**kwargs)

        kwargs = obj.get_core_attrs(deep_copy=False)
        lr_scheduler_manager = accepted_types[0](**kwargs)

    return lr_scheduler_manager



def _pre_serialize_lr_scheduler_manager(lr_scheduler_manager):
    obj_to_pre_serialize = lr_scheduler_manager
    serializable_rep = obj_to_pre_serialize.pre_serialize()
    
    return serializable_rep



def _de_pre_serialize_lr_scheduler_manager(serializable_rep):
    lr_scheduler_manager = LRSchedulerManager.de_pre_serialize(serializable_rep)

    return lr_scheduler_manager



_default_lr_scheduler_manager = None



###########################
## Define error messages ##
###########################
