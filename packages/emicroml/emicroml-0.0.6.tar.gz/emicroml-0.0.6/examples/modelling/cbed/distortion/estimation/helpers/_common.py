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
"""This module contains helper functions for the Jupyter notebooks stored in the
directory at ``<root>/examples/modelling/cbed/distortion/estimation/notebooks``,
where ``<root>`` is the root of the ``emicroml`` repository.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For general array handling.
import numpy as np

# For creating and plotting figures.
import matplotlib.pyplot as plt
import matplotlib.ticker



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = []



_title_font_size = 15



def _visualize_flow_field(sampling_grid, flow_field):
    sampling_grid = (sampling_grid[0].numpy(force=True),
                     sampling_grid[1].numpy(force=True))
    flow_field = (flow_field[0].numpy(force=True),
                  flow_field[1].numpy(force=True))

    slice_step = 16
    quiver_kwargs = {"angles": "uv", "pivot": "middle", "scale_units": "width"}

    X = sampling_grid[0][::slice_step, ::slice_step]
    Y = sampling_grid[1][::slice_step, ::slice_step]

    fig, ax = plt.subplots()

    U = flow_field[0][::slice_step, ::slice_step]
    V = flow_field[1][::slice_step, ::slice_step]

    kwargs = quiver_kwargs
    ax.quiver(X, Y, U, V, **kwargs)

    _update_quiver_plot_title_and_axes(ax)
            
    plt.gca().set_aspect('equal')
    plt.tight_layout()
    plt.show()

    return None



def _update_quiver_plot_title_and_axes(ax):
    _update_quiver_plot_title_and_axes_labels(ax)
    _update_quiver_plot_axes_ticks_and_spines(ax)

    return None



def _update_quiver_plot_title_and_axes_labels(ax):
    kwargs = {"label": "Flow Field Of Coordinate Transformation",
              "fontsize": _title_font_size}
    ax.set_title(**kwargs)

    kwargs = {"ax": ax,
              "x_label": "fractional horizontal coordinate",
              "y_label": "fractional vertical coordinate"}
    _update_axes_labels(**kwargs)

    return None



def _update_axes_labels(ax, x_label, y_label):
    axis_label_font_size = _title_font_size

    kwargs = {"xlabel": x_label, "fontsize": axis_label_font_size}
    ax.set_xlabel(**kwargs)

    kwargs = {"ylabel": y_label, "fontsize": axis_label_font_size}
    ax.set_ylabel(**kwargs)

    return None



def _update_quiver_plot_axes_ticks_and_spines(ax):
    kwargs = {"axis": "x",
              "which": "both",
              "bottom": False,
              "top": False,
              "labelbottom": False}
    ax.tick_params(**kwargs)

    kwargs = {"axis": "y",
              "which": "both",
              "left": False,
              "right": False,
              "labelleft": False}
    ax.tick_params(**kwargs)

    _update_axes_spines(ax)

    return None



def _update_axes_spines(ax):
    for side in ['top','bottom','left','right']:
        linewidth = 1.5
        ax.spines[side].set_linewidth(linewidth)

    return



def _plot_multiple_cdf_curves(x_set,
                              legend_label_set,
                              color_set,
                              title):
    fig, ax = plt.subplots()

    x_max_to_plot = 0.04

    for legend_label_idx, legend_label in enumerate(legend_label_set):
        kwargs = {"x": x_set[legend_label_idx],
                  "bins": np.linspace(0, x_max_to_plot, 100),
                  "histtype": "bar",
                  "ec": "black",
                  "cumulative": True,
                  "density": True,
                  "log": False,
                  "color": color_set[legend_label_idx],
                  "label": legend_label}
        ax.hist(**kwargs)

    kwargs = {"ax": ax, "legend_location": "lower right"}
    _update_legend(**kwargs)

    kwargs = {"ax": ax,
              "x_label": "EPE of adjusted distortion field (image width)",
              "y_label": "portion of images",
              "expressing_y_as_percentage": True}
    _update_non_quiver_plot_axes_labels_ticks_and_spines(**kwargs)

    kwargs = {"label": title, "fontsize": _title_font_size}
    ax.set_title(title, fontsize=_title_font_size)

    plt.tight_layout()
    plt.show()

    return None



def _update_legend(ax, legend_location):
    legend_label_font_size = _title_font_size

    kwargs = {"loc": legend_location, "fontsize": legend_label_font_size}
    ax.legend(**kwargs)

    return None



def _update_non_quiver_plot_axes_labels_ticks_and_spines(
        ax,
        x_label,
        y_label,
        expressing_y_as_percentage):
    kwargs = {"ax": ax,
              "x_label": x_label,
              "y_label": y_label}
    _update_axes_labels(**kwargs)

    kwargs = {"ax": ax,
              "expressing_y_as_percentage": expressing_y_as_percentage}
    _update_non_quiver_plot_axes_ticks_and_spines(**kwargs)

    return None



def _update_non_quiver_plot_axes_ticks_and_spines(ax,
                                                  expressing_y_as_percentage):
    for spatial_dim in ("x", "y"):
        major_tick_width = 1.5
        major_tick_length = 8
        minor_tick_width = major_tick_width
        minor_tick_length = major_tick_length//2
        tick_label_size = _title_font_size

        kwargs = {"axis": spatial_dim,
                  "which": "major",
                  "direction": "in",
                  "left": True,
                  "right": True,
                  "width": major_tick_width,
                  "length": major_tick_length,
                  "labelsize": tick_label_size}
        ax.tick_params(**kwargs)

        kwargs["which"] = "minor"
        kwargs["width"] = minor_tick_width
        kwargs["length"] = minor_tick_length
        ax.tick_params(**kwargs)

    if expressing_y_as_percentage:
        ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1))

    _update_axes_spines(ax)

    return None



###########################
## Define error messages ##
###########################
