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
r"""Contains tests for the module :mod:`emicrocml.lr.schedulers`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For operations related to unit tests.
import pytest



# For creating learning rate schedulers.
import emicroml.modelling.lr.schedulers



##################################
## Define classes and functions ##
##################################



def generate_lr_scheduler_name_set_0():
    lr_scheduler_name_set_0 = ("constant",
                               "linear",
                               "exponential",
                               "reduce_on_plateau",
                               "cosine_annealing_with_warm_restarts")

    return lr_scheduler_name_set_0



def test_1_of_BaseLRScheduler():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.BaseLRScheduler

    with pytest.raises(NotImplementedError) as err_info:
        kwargs = {"ctor_params": dict()}
        _ = cls_alias(**kwargs)

    return None



def test_1_of_Constant():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Constant

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    new_core_attr_subset_candidate = {"total_num_steps": 1}
    lr_scheduler.update(new_core_attr_subset_candidate)

    lr_scheduler.total_num_steps

    return None



def test_1_of_Linear():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Linear

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    return None



def test_1_of_Exponential():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Exponential

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    return None



def test_1_of_ReduceOnPlateau():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.ReduceOnPlateau

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    return None



def test_1_of_CosineAnnealingWithWarmRestarts():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.CosineAnnealingWithWarmRestarts

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    return None



def test_1_of_Nonsequential():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Nonsequential

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    return None



def test_1_of_Sequential():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Sequential

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    with pytest.raises(ValueError) as err_info:
        kwargs = {"non_sequential_lr_schedulers": (None,)}
        _ = cls_alias(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"non_sequential_lr_schedulers": tuple()}
        _ = cls_alias(**kwargs)

    return None



def test_1_of_Generic():
    module_alias = emicroml.modelling.lr.schedulers
    cls_alias = module_alias.Generic

    lr_scheduler = cls_alias()

    kwargs = {"serializable_rep": lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    lr_scheduler.total_num_steps

    lr_scheduler_name_set = generate_lr_scheduler_name_set_0()

    for lr_scheduler_name in lr_scheduler_name_set:
        kwargs = {"lr_scheduler_name": lr_scheduler_name,
                  "lr_scheduler_params": None}
        lr_scheduler = cls_alias(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"lr_scheduler_name": lr_scheduler_name,
                  "lr_scheduler_params": {"foo": "bar"}}
        lr_scheduler = cls_alias(**kwargs)

    kwargs = \
        {"lr_scheduler_name": "cosine_annealing_with_warm_restarts",
         "lr_scheduler_params": None}
    non_sequential_lr_scheduler = \
        module_alias.Nonsequential(**kwargs)

    lr_scheduler_params = {"non_sequential_lr_schedulers": \
                           (non_sequential_lr_scheduler,)}

    kwargs = {"lr_scheduler_name": "sequential",
              "lr_scheduler_params": lr_scheduler_params}
    generic_lr_scheduler = module_alias.Generic(**kwargs)

    kwargs = {"serializable_rep": generic_lr_scheduler.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    return None



###########################
## Define error messages ##
###########################
