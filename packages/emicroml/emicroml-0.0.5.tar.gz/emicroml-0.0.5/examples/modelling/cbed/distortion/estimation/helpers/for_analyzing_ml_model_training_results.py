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
``<root>/examples/modelling/cbed/distortion/estimation/notebooks/for_analyzing_ml_model_training_results.ipynb``,
where ``<root>`` is the root of the ``emicroml`` repository.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For creating and plotting figures.
import matplotlib.pyplot as plt



# For helper functions that are also used in other modules.
from . import _common



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = ["plot_single_xy_curve",
           "plot_multiple_xy_curves_with_error_bars",
           "plot_multiple_cdf_curves",
           "visualize_flow_field"]



_color_set = ("yellow", "green")



def plot_single_xy_curve(x, y, x_label, y_label):
    fig, ax = plt.subplots()

    ax.plot(x, y)

    kwargs = {"ax": ax,
              "x_label": x_label,
              "y_label": y_label,
              "expressing_y_as_percentage": False}
    _common._update_non_quiver_plot_axes_labels_ticks_and_spines(**kwargs)

    ax.set_yscale('log')

    plt.tight_layout()
    plt.show()

    return None



def plot_multiple_xy_curves_with_error_bars(
        x_set, y_set, y_err_set, legend_label_set, x_label, y_label):
    fig, ax = plt.subplots()

    for legend_label_idx, legend_label in enumerate(legend_label_set):
        kwargs = {"x": x_set[legend_label_idx],
                  "y": y_set[legend_label_idx],
                  "yerr": y_err_set[legend_label_idx],
                  "label": legend_label,
                  "marker": "o",
                  "markersize": 3,
                  "color": _color_set[legend_label_idx],
                  "mfc": _color_set[legend_label_idx],
                  "ecolor": (_color_set[legend_label_idx], 0.3)}
        ax.errorbar(**kwargs)

    kwargs = {"ax": ax, "legend_location": "upper right"}
    _common._update_legend(**kwargs)

    kwargs = {"ax": ax,
              "x_label": x_label,
              "y_label": y_label,
              "expressing_y_as_percentage": False}
    _common._update_non_quiver_plot_axes_labels_ticks_and_spines(**kwargs)

    ax.set_yscale('log')

    plt.tight_layout()
    plt.show()

    return None



def plot_multiple_cdf_curves(x_set, legend_label_set):
    kwargs = locals()
    kwargs["color_set"] = _color_set
    kwargs["title"] = ""
    _common._plot_multiple_cdf_curves(**kwargs)

    return None



def visualize_flow_field(sampling_grid, flow_field):
    _common._visualize_flow_field(sampling_grid, flow_field)

    return None



###########################
## Define error messages ##
###########################
