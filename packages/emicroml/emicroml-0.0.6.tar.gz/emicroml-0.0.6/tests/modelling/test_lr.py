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
r"""Contains tests for the module :mod:`emicrocml.lr`.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For operations related to unit tests.
import pytest



# For creating learning rate schedulers.
import emicroml.modelling.lr.schedulers

# For creating learning rate scheduler managers.
import emicroml.modelling.lr



##################################
## Define classes and functions ##
##################################



def test_1_of_LRSchedulerManager():
    module_alias_1 = emicroml.modelling.lr.schedulers
    module_alias_2 = emicroml.modelling.lr

    lr_schedulers = tuple()
    for total_num_steps in (1, 2):
        lr_scheduler_params = {"total_num_steps": total_num_steps}
        kwargs = {"lr_scheduler_name": "constant",
                  "lr_scheduler_params": lr_scheduler_params}
        generic_lr_scheduler = module_alias_1.Generic(**kwargs)
        lr_schedulers += (generic_lr_scheduler,)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"lr_schedulers": lr_schedulers,
                  "phase_in_which_to_update_lr": "training"}
        lr_scheduler_manager = module_alias_2.LRSchedulerManager(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"lr_schedulers": tuple(),
                  "phase_in_which_to_update_lr": "training"}
        lr_scheduler_manager = module_alias_2.LRSchedulerManager(**kwargs)

    with pytest.raises(ValueError) as err_info:
        kwargs = {"lr_schedulers": (None,),
                  "phase_in_which_to_update_lr": "training"}
        lr_scheduler_manager = module_alias_2.LRSchedulerManager(**kwargs)

    return None



###########################
## Define error messages ##
###########################
