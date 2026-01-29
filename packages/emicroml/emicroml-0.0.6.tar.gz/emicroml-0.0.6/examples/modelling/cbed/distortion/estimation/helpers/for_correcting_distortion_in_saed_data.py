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
``<root>/examples/modelling/cbed/distortion/estimation/notebooks/correcting_distortion_in_saed_data.ipynb``,
where ``<root>`` is the root of the ``emicroml`` repository.

"""



#####################################
## Load libraries/packages/modules ##
#####################################

# For general array handling.
import numpy as np

# For creating and plotting figures.
import hyperspy.api as hs

# For minimizing objective functions.
import scipy.optimize



# For helper functions that are also used in other modules.
from . import _common



##################################
## Define classes and functions ##
##################################

# List of public objects in module.
__all__ = ["visualize_flow_field",
           "find_visible_zolz_reflections",
           "fit_visible_zolz_reflections_to_square_lattice"]



def visualize_flow_field(sampling_grid, flow_field):
    _common._visualize_flow_field(sampling_grid, flow_field)

    return None



def find_visible_zolz_reflections(saed_pattern_signal):
    # Specify a mask that only reveals the visible ZOLZ reflections.
    kwargs = {"saed_pattern_signal": saed_pattern_signal}
    rectangular_mask_signal = _generate_rectangular_mask_signal(**kwargs)

    # Apply the mask to the SAED pattern and then apply the Difference of
    # Gaussian peak-finding method to find candidate peaks that may be located
    # at visible ZOLZ reflection locations.
    masked_saed_pattern_signal = saed_pattern_signal*rectangular_mask_signal
    kwargs = {"masked_saed_pattern_signal": \
              saed_pattern_signal*rectangular_mask_signal}
    candidate_peak_locations = _find_candidate_peaks(masked_saed_pattern_signal)

    # Some ZOLZ reflections have satelite peaks that get picked up by the above
    # peak-finding algorithm, hence we need to remove them.
    visible_zolz_reflections = _remove_satelite_peaks(candidate_peak_locations)

    # Plot the SAED pattern with markers at the locations of the visible ZOLZ
    # reflections.
    kwargs = {"saed_pattern_signal": saed_pattern_signal,
              "marker_positions": visible_zolz_reflections}
    _plot_saed_pattern_signal_with_markers(**kwargs)

    return visible_zolz_reflections



def _generate_rectangular_mask_signal(saed_pattern_signal):
    N_x, N_y = saed_pattern_signal.data.shape[::-1]

    L = 30
    R = N_x-345
    B = N_y-455
    T = 110

    rectangular_mask_image = np.zeros((N_y, N_x), dtype=bool)
    rectangular_mask_image[T:N_y-B, L:N_x-R] = True

    rectangular_mask_signal = hs.signals.Signal2D(data=rectangular_mask_image)

    return rectangular_mask_signal



def _find_candidate_peaks(masked_saed_pattern_signal):
    kwargs = {"method": "difference_of_gaussian",
              "overlap": 0,
              "threshold": 0.0025,
              "min_sigma": 1,
              "max_sigma": 2,
              "interactive": False,
              "show_progressbar": False}
    find_peaks_result = masked_saed_pattern_signal.find_peaks(**kwargs)
    candidate_peak_locations = find_peaks_result.data[0][:, ::-1]

    return candidate_peak_locations



def _remove_satelite_peaks(candidate_peak_locations):
    selection = tuple()
    num_candidate_peaks = len(candidate_peak_locations)
    ref_distance = None
    num_iterations = 2

    for iteration_idx in range(num_iterations):
        nearest_neighbour_distances = tuple()

        for candidate_peak_idx in range(num_candidate_peaks):
            candidate_peak_location = \
                candidate_peak_locations[candidate_peak_idx]
            
            displacements = candidate_peak_locations-candidate_peak_location
            distances = np.sort(np.linalg.norm(displacements, axis=(1,)))[1:]

            nearest_neighbour_distance = distances[0]
            nearest_neighbour_distances += (nearest_neighbour_distance,)

            if ref_distance is not None:
                if 2*nearest_neighbour_distance >= ref_distance:
                    selection += \
                        (candidate_peak_idx,)
                else:
                    lattice_spacing_estimate = \
                        distances[2*distances > ref_distance][0]

                    abs_diff = np.abs(lattice_spacing_estimate-ref_distance)
                    rel_diff = abs_diff / ref_distance
                    tol = 0.06

                    if rel_diff < tol:
                        selection += (candidate_peak_idx,)
                        
        if ref_distance is None:
            nn_distances = nearest_neighbour_distances
            nn_distances = np.array(nearest_neighbour_distances)

            outlier_threshold = 2
            outlier_registry = (np.abs(nn_distances - nn_distances.mean())
                                > outlier_threshold*nn_distances.std())

            ref_distance = nn_distances[~outlier_registry].mean()

    visible_zolz_reflections = \
        tuple(candidate_peak_locations[(selection,)].tolist())

    return visible_zolz_reflections



def _plot_saed_pattern_signal_with_markers(saed_pattern_signal,
                                           marker_positions):
    kwargs = {"axes_off": True,
              "scalebar": False,
              "colorbar": False,
              "gamma": 0.2,
              "cmap": "plasma",
              "title": ""}
    saed_pattern_signal.plot(**kwargs)

    for marker_position in marker_positions:
        kwargs = {"color": "black", "sizes": 3, "offsets": marker_position}
        marker = hs.plot.markers.Points(**kwargs)
        saed_pattern_signal.add_marker(marker, permanent=False)

    return None



def _objective(x, visible_zolz_reflections, N_x):
    u_O_x, u_O_y, b, theta = x

    # u_0_x: fractional horizontal coordinate of origin of square lattice fit.
    # u_0_y: fractional vertical coordinate of origin of square lattice fit.
    # b: length of primitive lattice vector.
    # theta: rotation applied to lattice.
    # N_x: Number of pixels across SAED pattern.

    N = N_x

    result = 0.0

    for (k_x, k_y) in visible_zolz_reflections:
        to_round = ((k_x-u_O_x)*np.cos(theta) + (k_y-u_O_y)*np.sin(theta)) / b
        rounded = np.round(to_round)
        result += (to_round-rounded)**2

        to_round = (-(k_x-u_O_x)*np.sin(theta) + (k_y-u_O_y)*np.cos(theta)) / b
        rounded = np.round(to_round)
        result += (to_round-rounded)**2

    result *= ((b/N)**2) / len(visible_zolz_reflections)
    result = np.sqrt(result)

    return result



def fit_visible_zolz_reflections_to_square_lattice(visible_zolz_reflections,
                                                   saed_pattern_signal):
    visible_zolz_reflections = np.array(visible_zolz_reflections)

    N_x, N_y = saed_pattern_signal.data.shape[::-1]

    kwargs = \
        {"visible_zolz_reflections": visible_zolz_reflections,
         "saed_pattern_signal": saed_pattern_signal}
    initial_guesses, bounds = \
        _generate_initial_guesses_and_bounds_for_fitting_alg(**kwargs)

    kwargs = {"fun": _objective,
              "args": (visible_zolz_reflections, N_x),
              "x0": initial_guesses,
              "bounds": bounds}
    minimization_result = scipy.optimize.minimize(**kwargs)

    kwargs = {"minimization_result": minimization_result,
              "visible_zolz_reflections": visible_zolz_reflections}
    lattice_position_subset = _generate_lattice_position_subset(**kwargs)

    kwargs = {"saed_pattern_signal": saed_pattern_signal,
              "marker_positions": lattice_position_subset}
    _plot_saed_pattern_signal_with_markers(**kwargs)

    fitting_error = minimization_result.fun
    unformatted_msg = ("The error of the fit is: {}, "
                       "in units of the image width.")
    msg = unformatted_msg.format(fitting_error)
    print(msg)

    return fitting_error



def _generate_initial_guesses_and_bounds_for_fitting_alg(
        visible_zolz_reflections, saed_pattern_signal):
    saed_pattern_image = saed_pattern_signal.data
    N_x, N_y = saed_pattern_signal.data.shape[::-1]

    ref_point = np.array((236, 242))
    u_O_guess = None

    for zolz_reflection in visible_zolz_reflections:
        if u_O_guess is None:
            u_O_guess = zolz_reflection
        else:
            distance_1 = np.linalg.norm(ref_point-u_O_guess)
            distance_2 = np.linalg.norm(ref_point-zolz_reflection)
            if distance_2 < distance_1:
                u_O_guess = zolz_reflection

    u_O_x_guess, u_O_y_guess = u_O_guess

    displacements = visible_zolz_reflections-u_O_guess
    b_guess = np.sort(np.linalg.norm(displacements, axis=(1,)))[1]

    for zolz_reflection in visible_zolz_reflections:
        displacement = zolz_reflection-u_O_guess
        distance = np.linalg.norm(displacement)
        if 1.1*b_guess > distance > 0:
            if displacement[1] > displacement[0] > 0:
                theta_guess = np.arctan2(displacement[1], displacement[0])

    initial_guesses = (u_O_x_guess,
                       u_O_y_guess,
                       b_guess,
                       theta_guess)
    
    u_O_x_bounds = (0, N_x)
    u_O_y_bounds = (0, N_y)
    b_bounds = (0.5*b_guess, 1.5*b_guess)
    theta_bounds = (0.75*theta_guess, 1.25*theta_guess)
    
    bounds = (u_O_x_bounds,
              u_O_y_bounds,
              b_bounds,
              theta_bounds)

    return initial_guesses, bounds



def _generate_lattice_position_subset(minimization_result,
                                      visible_zolz_reflections):
    u_O_x, u_O_y, b, theta = minimization_result.x
    
    u_O = np.array((u_O_x, u_O_y))
    b_1 = b*np.array((np.cos(theta), np.sin(theta)))
    b_2 = b*np.array((-np.sin(theta), np.cos(theta)))

    M = 10

    lattice_position_subset = tuple()
    for m_1 in range(-M, M+1):
        for m_2 in range(-M, M+1):
            lattice_position = (u_O + m_1*b_1 + m_2*b_2)
            displacements = visible_zolz_reflections-lattice_position
            distance = np.sort(np.linalg.norm(displacements, axis=(1,)))[0]
            if 2*distance < b:
                lattice_position_subset += (tuple(lattice_position.tolist()),)

    return lattice_position_subset



###########################
## Define error messages ##
###########################
