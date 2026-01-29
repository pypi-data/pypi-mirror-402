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
r"""Contains tests for the module :mod:`emicrocml.modelling.optimizers`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For operations related to unit tests.
import pytest



# For creating wrappers to PyTorch optimizer classes.
import emicroml.modelling.optimizers



##################################
## Define classes and functions ##
##################################



def test_1_of_BaseMLOptimizer():
    module_alias = emicroml.modelling.optimizers
    cls_alias = module_alias.BaseMLOptimizer

    with pytest.raises(NotImplementedError) as err_info:
        kwargs = {"ctor_params": dict()}
        _ = cls_alias(**kwargs)

    return None



def test_1_of_AdamW():
    module_alias = emicroml.modelling.optimizers
    cls_alias = module_alias.AdamW

    ml_optimizer = cls_alias()

    kwargs = {"serializable_rep": ml_optimizer.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    return None



def test_1_of_SGD():
    module_alias = emicroml.modelling.optimizers
    cls_alias = module_alias.SGD

    ml_optimizer = cls_alias()

    kwargs = {"serializable_rep": ml_optimizer.pre_serialize()}
    cls_alias.de_pre_serialize(**kwargs)

    return None



def test_1_of_Generic():
    module_alias = emicroml.modelling.optimizers
    cls_alias = module_alias.Generic

    ml_optimizer = cls_alias()

    new_core_attr_subset_candidate = {"ml_optimizer_name": "adam_w",
                                      "ml_optimizer_params": None}
    ml_optimizer.update(new_core_attr_subset_candidate)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"ml_optimizer_name": "adam_w",
                  "ml_optimizer_params": {"foo": "bar"}}
        _ = cls_alias(**kwargs)

    return None



###########################
## Define error messages ##
###########################
