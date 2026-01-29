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
"""This module contains helper functions for the Jupyter notebook located at
``<root>/examples/modelling/cbed/distortion/estimation/notebooks/for_analyzing_ml_model_testing_results.ipynb``,
where ``<root>`` is the root of the ``emicroml`` repository.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For helper functions that are also used in other modules.
from . import _common



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = ["plot_multiple_cdf_curves"]



def plot_multiple_cdf_curves(x_set, legend_label_set, title):
    legend_label_to_color_map = {"DL approach": "red", "RGM approach": "blue"}

    color_set = tuple(legend_label_to_color_map[legend_label]
                      for legend_label
                      in legend_label_set)

    kwargs = {"x_set": x_set,
              "legend_label_set": legend_label_set,
              "color_set": color_set,
              "title": title}
    _common._plot_multiple_cdf_curves(**kwargs)

    return None



###########################
## Define error messages ##
###########################
