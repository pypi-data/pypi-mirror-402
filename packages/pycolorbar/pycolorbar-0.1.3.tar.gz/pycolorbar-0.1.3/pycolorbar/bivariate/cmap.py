# -----------------------------------------------------------------------------.
# MIT License

# Copyright (c) 2024 pycolorbar developers
#
# This file is part of pycolorbar.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# -----------------------------------------------------------------------------.
"""Module defining BivariateColormap functionalities."""

import base64
import io
import os

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import BoundaryNorm, LogNorm, Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable
from PIL import Image
from PIL.PngImagePlugin import PngInfo

from pycolorbar.norm import CategorizeNorm, CategoryNorm, is_categorical_norm
from pycolorbar.utils.docstring import copy_docstring
from pycolorbar.utils.mpl_legend import add_colorbar_inset

# Import optional packages
try:
    import pandas as pd

    _PANDAS_AVAILABLE = True
except ImportError:
    _PANDAS_AVAILABLE = False


try:
    import geopandas as gpd

    _GEOPANDAS_AVAILABLE = True
except ImportError:
    _GEOPANDAS_AVAILABLE = False

try:
    import xarray as xr

    _XARRAY_AVAILABLE = True
except ImportError:
    _XARRAY_AVAILABLE = False

# Global settings

_BIVAR_REPR_PNG_SIZE = (256, 256)


####----------------------------------------------------------------------------------------------.


def check_n(n, both_integers=True):
    """Check n value validity."""
    # Ensure n is handled as a tuple
    if isinstance(n, (int, type(None))):
        n = (n, n)

    # Check values validity
    n_x, n_y = n
    if isinstance(n_x, int) and n_x < 2:
        raise ValueError("Expected n_x >= 2.")
    if isinstance(n_y, int) and n_y < 2:
        raise ValueError("Expected n_x >= 2.")
    if both_integers and (n_x is None or n_y is None):
        raise ValueError("n_x and n_y must be integers.")
    return n


def ensure_rgba_array(rgba_array):
    """Ensure a RGBA array is returned."""
    # Ensure RGBA array
    if rgba_array.shape[2] == 3:
        alpha_array = np.ones(
            (rgba_array.shape[0], rgba_array.shape[1], 1),
            dtype=rgba_array.dtype,
        )
        rgba_array = np.concatenate([rgba_array, alpha_array], axis=2)
    return rgba_array


def apply_luminance_gradient(image_rgb, luminance_factor=None):
    """
    Apply a bivariate luminance gradient to an RGB image.

    It add a radial whitening/darkening effect.

    Parameters
    ----------
    image_rgb : numpy.ndarray
        An (N, N, 4) or (N, N, 3) array of RGBA or RGB values.
    luminance_factor : float or None
        Radial darkening is obtained with values < 1.
        Radial whitening is obtained with values > 1.
        None or 1 produce no change.

    Returns
    -------
    numpy.ndarray
        The luminance-adjusted image array, same shape as `image_rgb`.
    """
    if luminance_factor is None or luminance_factor == 1:
        return image_rgb  # No change

    height, width = image_rgb.shape[:2]

    # Create a 2D radial pattern from -1..+1 in x and y
    x, y = np.meshgrid(np.linspace(-1, 1, width), np.linspace(-1, 1, height))

    # Compute radial distance
    radial_dist = np.sqrt(x**2 + y**2)

    # Weight to add "white" (like a radial whitening/darkening effect)
    white_term = luminance_factor ** ((np.sqrt(2) - radial_dist) / (2 * np.sqrt(2)))
    white_term = np.expand_dims(white_term, axis=2)  # for broadcasting

    # Add white_term to the first 3 channels (RGB)
    image_rgb[..., :3] = image_rgb[..., :3] + white_term

    # Rescale each channel to [0..1]
    for i in range(3):
        channel = image_rgb[..., i]
        min_val, max_val = np.nanmin(channel), np.nanmax(channel)
        if max_val > min_val:  # Avoid division by zero
            channel = (channel - min_val) / (max_val - min_val)
            image_rgb[..., i] = channel

    return image_rgb


def interpolate_bivariate_cmap_colors(coords, rgba_colors, n_x, n_y, method="cubic"):
    """Interpolate RGBA colors for a bivariate colormap.

    Parameters
    ----------
    coords : array-like, shape (n_points, 2)
        The coordinates of the known data points.
    rgba_colors : array-like, shape (n_points, 4)
        The RGBA color values at the known data points.
    n_x : int
        The number of points along the x-axis for the output grid.
    n_y : int
        The number of points along the y-axis for the output grid.
    method : str, optional
        The interpolation method to use.
        Options are 'linear', 'nearest', and 'cubic'.
        Default is 'cubic'.

    Returns
    -------
    rgba_array : ndarray, shape (n_y, n_x, 4)
        The interpolated RGBA color values on a grid of shape (n_y, n_x).
    """
    # Check if the scipy package is available
    try:
        from scipy.interpolate import griddata
    except ImportError:
        raise ImportError(
            "The 'scipy' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge scipy",
        ) from None

    # Create a mesh for the final NxN image
    x_mesh, y_mesh = np.meshgrid(np.linspace(0, 1, n_x), np.linspace(0, 1, n_y))
    x_req = x_mesh.ravel()
    y_req = y_mesh.ravel()

    # Interpolate each channel separately
    output_rgba = np.ones((n_y * n_x, 4)) * np.nan
    for i in range(4):
        channel_vals = griddata(
            points=coords,
            values=rgba_colors[:, i],
            xi=np.column_stack((x_req, y_req)),
            method=method,
        )
        # Clip channel values to [0..1]
        channel_vals[channel_vals < 0] = 0
        channel_vals[channel_vals > 1] = 1
        output_rgba[:, i] = channel_vals

    # Reshape to 2D
    rgba_array = output_rgba.reshape(n_y, n_x, 4)
    return rgba_array


def resample_rgba_array(rgba_array, n_x=None, n_y=None, interp_method=None):
    """Resample an RGBA array to a new number of colors.

    Parameters
    ----------
    rgba_array : numpy.ndarray
        Input RGBA array of shape (height, width, 4).
    n_x : int, optional
        Desired width of the resampled array. If None, the original width is used.
    n_y : int, optional
        Desired height of the resampled array. If None, the original height is used.
    interp_method : str, optional
        Interpolation method to use.
        If None, 'nearest' is used for downsampling and 'cubic' for upsampling.

    Returns
    -------
    numpy.ndarray
        Resampled RGBA array of shape (n_y, n_x, 4).

    Notes
    -----
    - If both `n_x` and `n_y` are None, the original `rgba_array`
      is returned without resampling.
    - If the desired size (`n_x`, `n_y`) is the same as the input size,
      the original `rgba_array` is returned.
    - The interpolation method defaults to 'nearest' for downsampling
      and 'cubic' for upsampling if not specified.
    """
    # Ensure rgba array
    rgba_array = ensure_rgba_array(rgba_array)

    # Return rgba array without resampling if n_x and n_y not specified
    if n_x is None and n_y is None:
        return rgba_array

    # Initialize n_x and n_y if None
    if n_x is None:
        n_x = rgba_array.shape[1]
    if n_y is None:
        n_y = rgba_array.shape[0]

    # If desired size equal to input size, return array as it is
    if n_x == rgba_array.shape[1] and n_y == rgba_array.shape[0]:
        return rgba_array

    # Define interpolation method
    # - If downsampling, use 'nearest' by default
    # - If upsampling, use 'cubic' by default
    if interp_method is None:
        if n_x < rgba_array.shape[1] and n_y < rgba_array.shape[0]:  # noqa
            interp_method = "nearest"
        else:
            interp_method = "cubic"

    # Define mesh
    x_mesh, y_mesh = np.meshgrid(np.linspace(0, 1, rgba_array.shape[1]), np.linspace(0, 1, rgba_array.shape[0]))

    # Flatten to get coords of shape (self.n_x*self.n_y, 2)
    coords = np.column_stack((x_mesh.ravel(), y_mesh.ravel()))

    # Flatten RGBA array to shape (self.n_x*self.n_y, 4)
    rgba_colors = rgba_array.reshape(-1, 4)

    # Interpolate colors to the new mesh
    rgba_array = interpolate_bivariate_cmap_colors(
        coords=coords,
        rgba_colors=rgba_colors,
        n_x=n_x,
        n_y=n_y,
        method=interp_method,
    )
    return rgba_array


# def interpolate_corners_colors(color_array, n_x, n_y):
#     """
#     Zoom a 2x2 corner color array to an (n_y, n_x) shape.

#     Parameters
#     ----------
#     color_array : numpy.ndarray
#         Shape (2, 2, 4) RGBA color corners.
#     n_x : int
#         Output width.
#     n_y : int
#         Output height.

#     Returns
#     -------
#     numpy.ndarray
#         An (n_y, n_x, 4) array of interpolated RGBA colors.
#     """
#     from scipy.ndimage import zoom
#     zoom_factor_y = n_y / 2.0
#     zoom_factor_x = n_x / 2.0
#     return zoom(color_array, (zoom_factor_y, zoom_factor_x, 1), order=1)   # order=1 => bilinear interpolation


####-----------------------------------------------------------------------------.
##################################
#### Create bivariate palette ####
##################################

# def get_bivariate_cmap_from_corners(
#     colors=("grey", "green", "red", "blue"),
#     n=(3, 3),
#     ):
#     """
#     Create a bivariate colormap from the colors at the four corners.

#     The interpolation is performed into the sRGB colorspace.

#     Parameters
#     ----------
#     colors : list or tuple
#         Four color recognized by matplotlib (e.g. 'red', '#RRGGBB', etc.).
#         The order correspond to [top_left, top_right, bottom_right, bottom_left]
#     n : int or tuple
#         Either a single integer or a (n_x, n_y) tuple specifying the number of colormap colors
#         on the x and y axis.

#     Returns
#     -------
#     numpy.ndarray
#         A 2D array of shape (n_y, n_x, 4) representing RGBA colors.
#     """
#     # Check 4 colors are specified
#     if len(colors) != 4:
#         raise ValueError("The BivariateColormap definition from corners requires the specification of 4 colors.")

#     # Retrieve number of colors per axis
#     n_x, n_y = check_n(n)

#     # Convert corner colors into an RGBA 2x2 matrix
#     rgba_corners = np.array([
#         [mpl.colors.to_rgba(colors[0]),
#          mpl.colors.to_rgba(colors[1])],
#         [mpl.colors.to_rgba(colors[3]),
#          mpl.colors.to_rgba(colors[2])],
#     ])

#     # Zoom up to desired (n_y, n_x)
#     rgba_array = interpolate_corners_colors(rgba_corners, n_x=n_x, n_y=n_y)
#     return rgba_array


def get_bivariate_cmap_from_colors(colors, n=5, interp_method=None):
    """
    Create a bivariate colormap from a set of color points.

    This function takes a set of RGBA (or named) colors arranged in a clockwise layout
    (plus an optional center color if 5 or 9 points), and interpolates them over an
    (n_y, n_x) grid in sRGB colorspace.

    Parameters
    ----------
    colors : list or tuple
        A list or array of color specifications recognized by Matplotlib
        (e.g., ['red', 'blue', 'green', 'black']) or an array of shape (N, 4) in RGBA format.
        The length of `colors` must be one of {4, 5, 8, 9}. See the Notes below.
    n : int or tuple
        Either a single integer or a (n_x, n_y) tuple specifying the number of colormap colors
        on the x and y axis.
    interp_method : str, optional
        The interpolation method to use for generating the colormap.
        The default is 'cubic'.

    Notes
    -----
    - The color points are assumed to be laid out clockwise, with optional
      center colors for 5 or 9 entries. Specifically:
    - For 4 colors: [top_left, top_right, bottom_right, bottom_left].
    - For 5 or 9 colors: the extra point(s) become center row (or center cell).
    - For 8 colors: midpoints along each side plus corners.

    Returns
    -------
    numpy.ndarray
        Shape (n_y, n_x, 4) array of interpolated RGBA.
    """
    # Check interp_method
    if interp_method is None:
        interp_method = "cubic"

    # Check number of colors
    colors = np.array(colors)
    n_colors = colors.shape[0]
    if n_colors not in [4, 5, 8, 9]:
        raise ValueError("You must specify either 4, 5, 8 or 9 colors.")

    # Retrieve number of colors per axis
    n_x, n_y = check_n(n)

    # Convert list of color specs to RGBA
    rgba_colors = mpl.colors.to_rgba_array(colors)

    dict_coords = {
        4: np.column_stack(([0, 1, 1, 0], [1, 1, 0, 0])),
        5: np.column_stack(([0, 1, 1, 0, 0.5], [1, 1, 0, 0, 0.5])),
        8: np.column_stack(([0, 0.5, 1, 1, 1, 0.5, 0, 0.5], [1, 1, 1, 0.5, 0, 0, 0, 0.5])),
        9: np.column_stack(([0, 0.5, 1, 1, 1, 0.5, 0, 0.5, 0.5], [1, 1, 1, 0.5, 0, 0, 0, 0.5, 0.5])),
    }
    coords = dict_coords[n_colors]

    rgba_array = interpolate_bivariate_cmap_colors(coords, rgba_colors, n_x=n_x, n_y=n_y, method=interp_method)
    return rgba_array


def get_bivariate_cmap_from_two_cmaps(cmap_x=plt.cm.Blues, cmap_y=plt.cm.Reds, n=256):
    """
    Construct a bivariate colormap by blending two univariate colormaps along x and y axes.

    Parameters
    ----------
    cmap_x : matplotlib.colors.Colormap or str
        Univariate colormap for the x axis.
    cmap_y : matplotlib.colors.Colormap or str
        Univariate colormap for the y axis.
    n : int or tuple
        Either a single integer or a (n_x, n_y) tuple specifying the number of colormap colors
        on the x and y axis.

    Returns
    -------
    numpy.ndarray
        Shape (n_y, n_x, 4) array of RGBA representing the combined colormap.
    """
    import pycolorbar

    cmap_x = pycolorbar.get_cmap(cmap_x)
    cmap_y = pycolorbar.get_cmap(cmap_y)

    # Retrieve number of colors per axis
    n_x, n_y = check_n(n)

    # Generate a mesh grid in [0..1]
    x_mesh, y_mesh = np.meshgrid(np.linspace(0, 1, n_x), np.linspace(0, 1, n_y))

    # Evaluate each colormap along its axis
    x_rgba = cmap_x(x_mesh)  # shape (n_y, n_x, 4)
    y_rgba = cmap_y(y_mesh)  # shape (n_y, n_x, 4)

    # Blending by average
    rgba_array = np.mean([x_rgba, y_rgba], axis=0)
    return rgba_array


####-----------------------------------------------------------------------------.
################################
#### Load bivariate palette ####
################################


#### BIVARIATE_CMAPS_DICT
BIVARIATE_CMAPS_DICT = {
    # -------------------------------
    #### - N=3
    # Transparency
    "brewer.qualseq": [
        ["#cce8d7", "#cedced", "#fbb4d9"],
        ["#80c39b", "#85a8d0", "#f668b3"],
        ["#008837", "#0a50a1", "#d60066"],
    ],
    "brewer.blueyellow": [
        ["#efd100", "#4eb87b", "#007fc4"],
        ["#fef3a9", "#bedebc", "#a1c8ea"],
        ["#fffdef", "#e6f1df", "#d2e4f6"],
    ],
    # Sequentials
    "brewer.seqseq1": [
        ["#e8e6f2", "#b5d3e7", "#4fadd0"],
        ["#e5b4d9", "#b8b3d8", "#3983bb"],
        ["#de4fa6", "#b03598", "#2a1a8a"],
    ],
    "brewer.seqseq2": [
        ["#f3f3f3", "#b4d3e1", "#509dc2"],
        ["#f3e6b3", "#b3b3b3", "#376387"],
        ["#f3b300", "#b36600", "#000000"],
    ],
    "stevens.greenblue": [
        ["#e8e8e8", "#b5c0da", "#6c83b5"],
        ["#b8d6be", "#90b2b3", "#567994"],
        ["#73ae80", "#5a9178", "#2a5a5b"],
    ],
    "stevens.bluered": [
        ["#e8e8e8", "#e4acac", "#c85a5a"],
        ["#b0d5df", "#ad9ea5", "#985356"],
        ["#64acbe", "#627f8c", "#574249"],
    ],
    "stevens.pinkgreen": [
        ["#f3f3f3", "#c2f1ce", "#8be2af"],
        ["#eac5dd", "#9ec6d3", "#7fc6b1"],
        ["#e6a3d0", "#bc9fce", "#7b8eaf"],
    ],
    "stevens.purplegold": [
        ["#e8e8e8", "#e4d9ac", "#c8b35a"],
        ["#cbb8d7", "#c8ada0", "#af8e53"],
        ["#9972af", "#976b82", "#804d36"],
    ],
    "stevens.pinkblue": [
        ["#e8e8e8", "#ace4e4", "#5ac8c8"],
        ["#dfb0d6", "#a5add3", "#5698b9"],
        ["#be64ac", "#8c62aa", "#3b4994"],
    ],
    "tolochko.redblue": [
        ["#dddddd", "#7bb3d1", "#016eae"],
        ["#dd7c8a", "#8d6c8f", "#4a4779"],
        ["#cc0024", "#8a274a", "#4b264d"],
    ],
    # Divergents
    "brewer.divdiv": [
        ["#f37300", "#cce88b", "#008837"],
        ["#fe9aa6", "#e6e6e6", "#9ac9d5"],
        ["#f0047f", "#cd9acc", "#5a4da4"],
    ],
    "teuling.choro3": [
        ["#F4843A", "#F16879", "#A63F96"],
        ["#BCD85E", "#F0F0F0", "#5C6AB1"],
        ["#00AC51", "#00B18A", "#18B3E5"],
    ],
    # Divergent-sequentials
    "brewer.divseq": [
        ["#c3b3d8", "#e6e6e6", "#ffcc80"],
        ["#7b67ab", "#bfbfbf", "#f35926"],
        ["#240d5e", "#7f7f7f", "#b30000"],
    ],
    # -------------------------------
    #### - N=4
    "arc.bluepink": [
        ["#ffffff", "#ffe6fe", "#ffbdff", "#ff80fe"],
        ["#e7ffff", "#d7dafd", "#d8a6ff", "#c065fe"],
        ["#c0fcfd", "#a7caff", "#8d7efd", "#7f65fe"],
        ["#74feff", "#64c0ff", "#5873fe", "#4b4cff"],
    ],
    # -------------------------------
    #### - N=5
    "teuling.choro5": [
        ["#F4843A", "#F37C57", "#F16879", "#EE4497", "#A63F96"],
        ["#FCB73D", "#F9B381", "#F9B381", "#C980B5", "#8054A1"],
        ["#BCD85E", "#D4E6A3", "#F0F0F0", "#A9A4D0", "#5C6AB1"],
        ["#5C6AB1", "#80C99C", "#78CDCE", "#49B5E7", "#2477BC"],
        ["#00AC51", "#00B18A", "#00B18A", "#18B3E5", "#18B3E5"],
    ],
    #### - FROM NPY
    "bremm": "bremm.npy",
    "cubediagonal": "cubediagonal.npy",
    "schumann": "schumann.npy",
    "steiger": "steiger.npy",
    "ziegler": "ziegler.npy",
    "teuling2": "teuling2.npy",
}

#### TEULING_CMAPS
TEULING_CMAPS = ["teuling.GRMB", "teuling.YGBR", "teuling.RBCG"]


def available_bivariate_colormaps():
    """Get the list of the predefined available bivariate colormaps."""
    names = list(BIVARIATE_CMAPS_DICT) + TEULING_CMAPS + ["LABspace"]
    return sorted(names)


def check_name(name):
    """Check name validity."""
    if not isinstance(name, str):
        raise TypeError("'name' must be a string.")

    valid_names = available_bivariate_colormaps()
    if name not in valid_names:
        raise ValueError(f"Invalid 'name' {name}. Available names are {valid_names}")
    return name


def load_bivariate_palette(name, n, interp_method=None):
    """Load predefined bivariate palette."""
    from pycolorbar import _root_path

    colors_array_or_filename = BIVARIATE_CMAPS_DICT[name]
    if isinstance(colors_array_or_filename, str):
        filepath = os.path.join(_root_path, "pycolorbar", "bivariate", "data", colors_array_or_filename)
        rgba_array = np.load(filepath) / 255

    else:
        colors_array = np.array(colors_array_or_filename)
        rgba_array = mpl.colors.to_rgba_array(colors_array.ravel()).reshape(*((*colors_array.shape, 4)))

    # Ensure rgba array
    rgba_array = ensure_rgba_array(rgba_array)

    # Resample if asked
    n_x, n_y = check_n(n, both_integers=False)
    rgba_array = resample_rgba_array(rgba_array, n_x=n_x, n_y=n_y, interp_method=interp_method)
    return rgba_array


def _get_teuling_colors(name="teuling_GRMB", diagonal_tilt=0.8, offdiag_tilt=1):
    dt = diagonal_tilt
    odt = offdiag_tilt
    color_dict = {
        "teuling.GRMB": np.array(
            [dt, 1, dt, odt, 0.5, 1 - odt, 1 - dt, 0, 1 - dt, 1 - odt, 0.5, odt, 0.5, 0.5, 0.5],
        ).reshape(5, 3),
        "teuling.YGBR": np.array(
            [dt, dt, 1, odt, 1 - odt, 0.5, 1 - dt, 1 - dt, 0, 1 - odt, odt, 0.5, 0.5, 0.5, 0.5],
        ).reshape(5, 3),
        "teuling.RBCG": np.array(
            [1, dt, dt, 0.5, odt, 1 - odt, 0, 1 - dt, 1 - dt, 0.5, 1 - odt, odt, 0.5, 0.5, 0.5],
        ).reshape(5, 3),
    }
    return color_dict[name]


def get_bivariate_cmap_teuling(name, n, diagonal_tilt, offdiag_tilt, interp_method=None):
    """Generate a bivariate colormap using the Teuling method.

    Parameters
    ----------
    name : str
        The name of the colormap.
    n : int
        The number of colors in the colormap.
    diagonal_tilt : float
        The tilt angle for the diagonal colors.
    offdiag_tilt : float
        The tilt angle for the off-diagonal colors.
    interp_method : str, optional
        The interpolation method to use for generating the colormap.

    Returns
    -------
    rgba_array : numpy.ndarray
        An array of RGBA colors representing the bivariate colormap.
    """
    colors = _get_teuling_colors(name=name, diagonal_tilt=diagonal_tilt, offdiag_tilt=offdiag_tilt)
    rgba_array = get_bivariate_cmap_from_colors(colors=colors, n=n, interp_method=interp_method)
    return rgba_array


def get_bivariate_cmap_labspace(n):
    """Generate a bivariate colormap in CIELAB space.

    This function creates a 2D grid of (L, a, b) values, applies non-linear
    transformations to the 'a' and 'b' channels, and converts the result to
    an RGB image.

    Parameters
    ----------
    n : int or tuple
        - If int, produce an (n, n) 2D grid.
        - If tuple (n_x, n_y), produce a (n_y, n_x) 2D grid.

    Returns
    -------
    rgb_array : numpy.ndarray
        A 3D array of shape (n_y, n_x, 3), representing the RGB image.
        Pixel values lie in [0, 1].

    Notes
    -----
    - LAB color space is perceptually uniform, so small changes in L, a, b
      correspond to relatively uniform changes in visual perception.
    - The tanh scaling on 'a' and 'b' compresses large values, preventing
      extreme color shifts.
    """
    # Check if the colorspacious package is available
    try:
        from colorspacious import cspace_convert
    except ImportError:
        raise ImportError(
            "The 'colorspacious' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge colorspacious",
        ) from None

    # Check argument
    n_x, n_y = check_n(n)

    # Create a grid in the range [-100, 100] for both a and b dimensions.
    spacing_x = np.linspace(-100, 100, n_x)
    spacing_y = np.linspace(-100, 100, n_y)

    # Create a meshgrid with shape (n_y, n_x)
    a, b = np.meshgrid(spacing_x, spacing_y)

    # Define the L channel
    # - Center L at 75
    # - Perturb with a linear combination of 'a' and 'b'
    l = np.ones_like(a) * 75 + b * 0.15 - a * 0.3  # noqa: E741

    # Create the LAB array
    lab_array = np.dstack([l, a, b])

    # Compress the a and b channels using tanh, to prevent extreme color shifts.
    lab_array[:, :, 1] = np.tanh(lab_array[:, :, 1] / 130) * 100  # a
    lab_array[:, :, 2] = np.tanh(lab_array[:, :, 2] / 190) * 100  # b

    # Convert from LAB to RGB
    # - a and b in [-128, 127]
    lab_array[:, :, 0] = np.clip(lab_array[:, :, 0], 0, 100)
    lab_array[:, :, 1] = np.clip(lab_array[:, :, 1], -128, 127)
    lab_array[:, :, 2] = np.clip(lab_array[:, :, 2], -128, 127)
    rgba_array = cspace_convert(lab_array, "CIELab", "sRGB1")
    rgba_array = np.clip(rgba_array, 0, 1)
    return rgba_array


def get_bivariate_cmap_from_name(name, n, diagonal_tilt=0.8, offdiag_tilt=1, interp_method=None):
    """Retrieve a bivariate colormap based on the specified name and parameters.

    Parameters
    ----------
    name : str
        The name of the bivariate colormap to retrieve.
        See available_biviariate_colormaps().
    n : int
        The number of colors in the colormap.
    diagonal_tilt : float, optional
        The tilt of the diagonal in the colormap, by default 0.8.
        Used only for Teuling colormaps.
    offdiag_tilt : float, optional
        The tilt of the off-diagonal in the colormap, by default 1.
        Used only for Teuling colormaps.
    interp_method : str or None, optional
        The interpolation method to use, by default None.

    Returns
    -------
    rgba_array : numpy.ndarray
        An array of RGBA values representing the colormap.

    """
    # Check arguments
    n = check_n(n)
    name = check_name(name)

    ##------------------------------------------------------------------------.
    # Retrieve Teuling bivariate cmap
    if name in TEULING_CMAPS:
        rgba_array = get_bivariate_cmap_teuling(
            name=name,
            n=n,
            diagonal_tilt=diagonal_tilt,
            offdiag_tilt=offdiag_tilt,
            interp_method=interp_method,
        )
        return rgba_array

    ##------------------------------------------------------------------------.
    # Retrieve LABspace cmap
    if name == "LABspace":
        rgba_array = get_bivariate_cmap_labspace(n)
        return rgba_array

    ##------------------------------------------------------------------------.
    # Retrieve bivariate cmap from file or dictionary
    # if name in BIVARIATE_CMAPS_DICT:
    rgba_array = load_bivariate_palette(name=name, n=n, interp_method=interp_method)
    return rgba_array


####------------------------------------------------------------------------.
#### Color Mapping


def _map_colors(x_normalized, y_normalized, n_x, n_y, rgba_array, interp_method="nearest", origin="lower"):
    # Check if the colorspacious package is available
    try:
        from scipy.interpolate import RegularGridInterpolator
    except ImportError:
        raise ImportError(
            "The 'scipy' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge scipy",
        ) from None

    # Define LUT indices
    cols = np.linspace(0, 1, n_x)
    rows = np.linspace(1, 0, n_y) if origin == "lower" else np.linspace(0, 1, n_y)
    # Define interpolators
    interpolators = [
        RegularGridInterpolator(
            (rows, cols),
            rgba_array[:, :, i],
            method=interp_method,
            bounds_error=False,  # Do not raise error if out of grid. It extrapolate
            fill_value=np.nan,  # Extrapolate if None.
        )
        for i in range(4)
    ]

    # Define (y,x) points to map
    data_shape = x_normalized.shape
    pts = np.column_stack([y_normalized.ravel(), x_normalized.ravel()])

    # Map colors
    rgba_mapped = np.stack([interpolators[i](pts).reshape(data_shape) for i in range(4)], axis=-1)

    # Ensure RGBA values in [0..1] after interpolation
    rgba_mapped = np.clip(rgba_mapped, 0.0, 1.0)
    return rgba_mapped


def map_colors(
    x_normalized,
    y_normalized,
    n_x,
    n_y,
    rgba_array,
    mask,
    bad_color=(0.0, 0.0, 0.0, 0.0),
    interp_method="nearest",
    origin="lower",
):
    """
    Map normalized (x,y) data in [0..1] to RGBA by interpolating in the 2D colormap RGBA array.

    Parameters
    ----------
    x_normalized : numpy.ndarray
        Values in [0..1], same shape as y_normalized.
    y_normalized : numpy.ndarray
        Values in [0..1], same shape as x_normalized.
        Note y=0 corresponds to the bottom row, y=1 to the top row.
    n_x, n_y : int
        Number of columns (x-axis) and rows (y-axis) in the colormap.
    rgba_array : numpy.ndarray
        The bivariate colormap RGBA array of shape (n_y, n_x, 4).
    mask : numpy.ndarray
        Boolean mask of shape (n_y, n_x) where True indicates NaN or invalid data.
    bad_color : tuple of float
        RGBA color to assign to invalid points or out-of-bounds values.
    interp_method : str
        Interpolation method ("nearest", "linear", "cubic"). Default "nearest".
    origin : str
        Either "upper" or "lower". The default is "lower".
        When "lower", the axis origin is on the bottom left and values (0,0) and (0,1) are
        mapped respectively to rgba_array[-1, 0, :] and rgba_array[0, 0, :]

    Returns
    -------
    rgba_mapped : numpy.ndarray
        An RGBA array with out-of-range values or masked points set to `bad_color`.
    """
    # Map colors
    rgba_mapped = _map_colors(
        x_normalized=x_normalized,
        y_normalized=y_normalized,
        n_x=n_x,
        n_y=n_y,
        rgba_array=rgba_array,
        interp_method=interp_method,
        origin=origin,
    )
    # Assign bad color for NaNs or out-of-bounds
    bad_mask = mask | (x_normalized < 0) | (x_normalized > 1) | (y_normalized < 0) | (y_normalized > 1)
    rgba_mapped[bad_mask] = bad_color
    return rgba_mapped


def define_norm(arr):
    """
    Define a matplotlib.Normalize object based on array's values.

    Parameters
    ----------
    arr : array-like
        Input array to be normalized.

    Returns
    -------
    Normalize or None
        A Normalize object with the minimum and maximum values of the array,
        or None if the array contains non-numeric data.

    Raises
    ------
    ValueError
        If the array has all identical values or contains only NaNs.

    Notes
    -----
    If the array contains non-numeric data, it returns None.
    """
    arr = np.asanyarray(arr)
    if not np.issubdtype(arr.dtype, np.number):  # edge case for category dtype
        return None

    vmin, vmax = np.nanmin(arr), np.nanmax(arr)
    if vmin == vmax or np.isnan(vmin):
        raise ValueError(f"Please specify the norm because all array values are {vmin}.")
    return Normalize(vmin=vmin, vmax=vmax)


def check_expected_number_categories(n, n_categories, dim_name, obj="norm"):
    """Check that number of color matches the number of categories."""
    if n_categories != n:
        msg = (
            f"The colormap has {n} colors on {dim_name}, but the {obj} indicates {n_categories} categories. "
            + "Please adapt the bivariate colormap to the number of expected categories."
        )
        raise ValueError(msg)


def check_cmap_ncolors(norm, n, dim_name):
    """Check for the number of colors for categorical norms."""
    if norm is not None and is_categorical_norm(norm):
        n_categories = norm.Ncmap
        check_expected_number_categories(n, n_categories, dim_name=dim_name)


def create_pandas_category_norm(series):
    """Create a CategoryNorm object for a pandas Categorical series.

    Parameters
    ----------
    series : pandas.Series or geopandas.GeoSeries
        A pandas or geopandas Series with categorical data.

    Returns
    -------
    pycolorbar.norm.CategoryNorm
        A CategoryNorm object that maps category integer indices to category names.

    Notes
    -----
    This function assumes that the input series is of categorical dtype.
    It creates a dictionary mapping category integer indices to category names and
    uses this dictionary to initialize a CategoryNorm object.
    """
    indices = np.arange(0, len(series.cat.categories)).astype(int).tolist()
    categories = list(series.cat.categories)
    categories_dict = dict(zip(indices, categories, strict=False))
    norm = CategoryNorm(categories_dict)
    return norm


def normalize_array(arr, norm):
    """
    Normalize a numeric numpy array to [0..1] using either a Matplotlib norm or min-max scaling.

    If `norm` is a BoundaryNorm, we also scale the resulting integer bin indices from [0..(N-1)] to [0..1].

    Parameters
    ----------
    arr : array-like
        Numeric array (possibly containing NaNs).
    norm : None or matplotlib.colors.Normalize
        If not None, `norm(arr)` is called.
        If it's a BoundaryNorm, we further scale the integer output to [0..1].

    Returns
    -------
    numpy.ndarray
        Array of same shape as `arr` with values in [0..1], except for NaNs in `arr`,
        which propagate as NaNs here.
    """
    # Deal with case if all NaN values
    if np.all(np.isnan(arr)):
        return np.ones_like(arr) * np.nan

    # If norm not provided, normalize based on min/max values of data
    # --> TODO: This does not happen anymore
    # if norm is None:
    #     vmin, vmax = np.nanmin(arr), np.nanmax(arr)
    #     rng = vmax - vmin
    #     if rng > 0:
    #         arr_normed = (arr - vmin) / rng
    #      return arr_normed

    # Normalize using provided norm to [0-1]
    # - The norm typically normalize values to [0-1]
    arr_normed = norm(arr)
    # - If norm scaled to integer indices instead of 1
    # --> (i.e. Boundary Norm, CategoryNorm, CategorizeNorm), scale to [0-1]
    if hasattr(norm, "Ncmap"):
        arr_normed = arr_normed.data / norm.Ncmap
    return arr_normed


def normalize_pandas_series(series, norm):
    """
    Normalize or encode a pandas Series to [0..1].

    - If it's categorical, we map category indices -> [0..1].
    - Otherwise, it relies on `normalize_array`.

    Parameters
    ----------
    series : pandas.Series or geopandas.GeoSeries
        The data series to normalize.
    norm : None or matplotlib.colors.Normalize
        Same as in `normalize_array`.

    Returns
    -------
    numpy.ndarray
        Array of float in [0..1] (except for NaNs).
    """
    if isinstance(series.dtype, pd.CategoricalDtype):
        # Scale category indices to [0-1]
        cat_indices = series.cat.codes.to_numpy(float)
        n_categories = len(series.cat.categories)
        normed_values = cat_indices / max(n_categories - 1, 1)
        return normed_values
    return normalize_array(series.to_numpy(float), norm=norm)


def map_array_data(x, y, norm_x, norm_y, rgba_array, bad_color=(0.0, 0.0, 0.0, 0.0), interp_method="nearest"):
    """
    Map two numeric arrays (x, y) to a bivariate colormap.

    Parameters
    ----------
    x : array-like
        Numeric array for the x dimension.
    y : array-like
        Numeric array for the y dimension. Must match shape of x.
    norm_x : None or matplotlib.colors.Normalize
        Normalization for x dimension. If None, do min-max scaling.
    norm_y : None or matplotlib.colors.Normalize
        Normalization for y dimension. If None, do min-max scaling.
    rgba_array : numpy.ndarray
        The base bivariate colormap of shape (n_y, n_x, 4).
    bad_color : tuple
        RGBA color for invalid points.
    interp_method : str, optional
        Interpolation method for RegularGridInterpolator. Default "nearest".

    Returns
    -------
    numpy.ndarray
        Mapped RGBA array of shape = x.shape + (4,).
    """
    # Retrieve number of x and y colors
    n_y, n_x, _ = rgba_array.shape

    # Ensure numpy arrays (i.e. put dask array into memory)
    x = np.asanyarray(x, dtype=float)
    y = np.asanyarray(y, dtype=float)

    # Check same shape
    if x.shape != y.shape:
        raise ValueError("x and y must have the same shape.")

    # Check number of colors if categorical norm
    check_cmap_ncolors(norm_y, n=n_y, dim_name="y")
    check_cmap_ncolors(norm_x, n=n_x, dim_name="x")

    # Build a mask for NaNs
    mask = np.isnan(x) | np.isnan(y)

    # Normalize arrays to [0-1]
    x_normalized = normalize_array(x, norm_x)
    y_normalized = normalize_array(y, norm_y)

    # Map values to colors
    rgba_mapped = map_colors(
        x_normalized=x_normalized,
        y_normalized=y_normalized,
        n_x=n_x,
        n_y=n_y,
        rgba_array=rgba_array,
        mask=mask,
        bad_color=bad_color,
        interp_method=interp_method,
    )
    return rgba_mapped


def map_pandas_data(x, y, norm_x, norm_y, rgba_array, bad_color=(0.0, 0.0, 0.0, 0.0), interp_method="nearest"):
    """
    Map two pandas Series (x, y) to a bivariate colormap.

    Supports categorical Series and geopandas.GeoSeries.

    Parameters
    ----------
    x : pandas.Series or geopandas.Series
        Data for the x dimension.
    y : pandas.Series  or geopandas.Series
        Data for the y dimension. Must match shape of x.
    norm_x : None or matplotlib.colors.Normalize
        Normalization for x dimension. If None, do min-max or categorical scaling.
    norm_y : None or matplotlib.colors.Normalize
        Normalization for y dimension.
    rgba_array : numpy.ndarray
        The bivariate colormap, shape (n_y, n_x, 4).
    bad_color : tuple
        RGBA color for invalid or out-of-bounds points.
    interp_method : str, optional
        Interpolation method. Default "nearest".

    Returns
    -------
    numpy.ndarray
        Mapped RGBA array of shape = x.shape + (4,).
    """
    # Check same shape
    if x.shape != y.shape:
        raise ValueError("x and y must have the same shape.")

    # Retrieve number of x and y colors
    n_y, n_x, _ = rgba_array.shape

    # Check for categorical pd.Series
    if isinstance(x.dtype, pd.CategoricalDtype):
        check_expected_number_categories(
            n=n_x,
            n_categories=len(x.cat.categories),
            dim_name="x",
            obj="categorical pd.Series",
        )
    if isinstance(y.dtype, pd.CategoricalDtype):
        check_expected_number_categories(
            n=n_y,
            n_categories=len(y.cat.categories),
            dim_name="y",
            obj="categorical pd.Series",
        )

    # Build initial mask for NaNs
    mask = x.isna() | y.isna()
    mask = mask.to_numpy()

    # Normalize series to [0-1]
    x_normalized = normalize_pandas_series(x, norm_x)
    y_normalized = normalize_pandas_series(y, norm_y)

    # Map values to colors
    rgba_mapped = map_colors(
        x_normalized=x_normalized,
        y_normalized=y_normalized,
        n_x=n_x,
        n_y=n_y,
        rgba_array=rgba_array,
        mask=mask,
        bad_color=bad_color,
        interp_method=interp_method,
    )
    return rgba_mapped


def map_xarray_data(x, y, norm_x, norm_y, rgba_array, bad_color=(0.0, 0.0, 0.0, 0.0), interp_method="nearest"):
    """
    Map two xarray DataArrays (x, y) to a bivariate colormap.

    Broadcasts x and y if needed, then returns an xarray DataArray with a new "rgba" dimension.

    Parameters
    ----------
    x : xarray.DataArray
        Data for x dimension.
    y : xarray.DataArray
        Data for y dimension.
    norm_x : None or matplotlib.colors.Normalize
        Normalization for x dimension.
    norm_y : None or matplotlib.colors.Normalize
        Normalization for y dimension.
    rgba_array : numpy.ndarray
        Bivariate colormap of shape (n_y, n_x, 4).
    bad_color : tuple
        RGBA color for invalid points.
    interp_method : str, optional
        Interpolation method. Default "nearest".

    Returns
    -------
    xarray.DataArray
        Same shape as x,y plus a final "rgba" dimension of size 4.
    """
    # Broadcast x,y if they differ in dimension but are broadcastable
    x, y = xr.broadcast(x, y)

    # Retrieve RGBA numpy array
    rgba_arr = map_array_data(
        x.data,
        y.data,
        norm_x=norm_x,
        norm_y=norm_y,
        rgba_array=rgba_array,
        bad_color=bad_color,
        interp_method=interp_method,
    )

    # Convert back to xarray
    new_dims = (*x.dims, "rgba")
    coords_dict = dict(x.coords)  # copy original coords if desired
    coords_dict["rgba"] = ["R", "G", "B", "A"]
    da_rgba = xr.DataArray(rgba_arr, coords=coords_dict, dims=new_dims)
    return da_rgba


####------------------------------------------------------------------------.
#### Plotting


def plot_bivariate_palette(
    rgba_array,
    ax=None,
    *,
    xlim=None,
    ylim=None,
    disable_axis=False,
    origin="upper",
    aspect="auto",
    **imshow_kwargs,
):
    """Plot the bivariate colormap.

    Parameters
    ----------
    rgba_array : numpy.ndarray
        A 2D array of RGBA values representing the bivariate colormap.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot the colormap. If None, a new figure and axes will be created.
    xlim : list or tuple, optional
        The x-axis limits for the plot. If None, defaults to [0, n_x - 1].
    ylim : list or tuple, optional
        The y-axis limits for the plot. If None, defaults to [0, n_y - 1].
    disable_axis : bool, optional
        If True, the axis will be turned off. Default is False.
    origin : {'upper', 'lower'}, optional
        The origin of the colormap. Default is 'upper'.
    aspect: str or float
        Either 'equal' or 'auto' or float.
        Controls the axes scaling (y/x-scale).
        If 'auto' fill the Axes position rectangle with data.
        If 'equal', ensure same scaling between x and y axis.
        The default is 'auto'.
    **imshow_kwargs : dict, optional
        Additional keyword arguments to pass to `imshow`.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object created by `imshow` representing the bivariate colormap.

    Notes
    -----
    If no axes are provided, a new figure and axes are created.
    The x and y limits can be specified, and the axis can be disabled if desired.
    The origin parameter determines the placement of the origin axis.

    """
    # Retrieve n_y and n_x
    n_y, n_x = rgba_array.shape[0:2]

    # Define xlim and ylim
    if xlim is None:
        xlim = [0 - 0.5, n_x - 1 + 0.5]
    xlim = list(xlim)
    if ylim is None:
        ylim = [0 - 0.5, n_y - 1 + 0.5]
    ylim = list(ylim)

    # Initialize plot if necessary
    axis_not_provided = ax is None
    if axis_not_provided:
        fig, ax = plt.subplots(1, 1)  # noqa: RUF059

    # Define extent (at pixel outer corners)
    extent = xlim + ylim

    # Flip RGBA 2D array on y axis depending on the origin
    # --> origin is used to specify where the origin axis is located
    # --> BUT the image is always displayed from top to bottom
    if origin == "upper":
        extent = (extent[0], extent[1], extent[3], extent[2])
    else:
        rgba_array = rgba_array[::-1, ...]

    # Plot bivariate colormap
    p = ax.imshow(rgba_array, origin=origin, extent=extent, **imshow_kwargs)

    # Set axis off
    if disable_axis:
        ax.axis("off")

    # Set aspect
    ax.set_aspect(aspect)

    # Return
    return p


def get_log_ticks(vmin, vmax):
    """Return log ticks."""
    return np.power(10, np.arange(np.floor(np.log10(vmin)), np.ceil(np.log10(vmax)) + 1))


def set_log_axis(ax, major_ticks, axis):
    """
    Set logarithmic-like ticks on a linear axis for imshow plots.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes object to modify
    major_ticks : array-like
        The positions for major ticks in data coordinates.
    axis : str, optional
        The axis to modify ("x" or "y").
    """
    # Get the image extent
    extent = ax.get_images()[0].get_extent()

    # Generate minor ticks
    minor_ticks = []
    for i in range(len(major_ticks) - 1):
        current_major = major_ticks[i]
        minor_ticks.extend(np.arange(2, 10) * current_major)

    # Convert to arrays
    major_ticks = np.array(major_ticks)
    minor_ticks = np.array(minor_ticks)

    # Get axis limits
    axis_min, axis_max = major_ticks[0], major_ticks[-1]

    # Get relevant dimension for pixel conversion
    if axis.lower() == "y":
        extent_min, extent_max = extent[2], extent[3]
    else:
        extent_min, extent_max = extent[0], extent[1]

    # Convert to pixel positions
    major_data_pos = extent_min + (extent_max - extent_min) * (np.log10(major_ticks) - np.log10(axis_min)) / (
        np.log10(axis_max) - np.log10(axis_min)
    )

    minor_data_pos = extent_min + (extent_max - extent_min) * (np.log10(minor_ticks) - np.log10(axis_min)) / (
        np.log10(axis_max) - np.log10(axis_min)
    )

    # Create tick labels
    major_tick_labels = [f"{x:.0f}" for x in major_ticks]

    # Set ticks based on axis
    if axis.lower() == "y":
        ax.set_yticks(major_data_pos)
        ax.set_yticklabels(major_tick_labels)
        ax.set_yticks(minor_data_pos, minor=True)
        ax.yaxis.set_tick_params(which="minor", length=4)
        ax.yaxis.set_tick_params(which="major", length=8)

    else:
        ax.set_xticks(major_data_pos)
        ax.set_xticklabels(major_tick_labels)
        ax.set_xticks(minor_data_pos, minor=True)
        ax.xaxis.set_tick_params(which="minor", length=4)
        ax.xaxis.set_tick_params(which="major", length=8)


def get_axis_defaults(norm):
    """Return a tuple ((axis_min, axis_max), ticks, ticklabels) from a matplotlib norm."""
    if isinstance(norm, (CategoryNorm, CategorizeNorm)):
        value_lims = (0, norm.Ncmap)
        ticks = np.arange(0, norm.Ncmap) + 0.5
        ticklabels = norm.ticklabels.copy()
        return (value_lims, ticks, ticklabels)
    if isinstance(norm, BoundaryNorm):
        value_lims = norm.boundaries[0], norm.boundaries[-1]
        ticks = norm.boundaries.copy()
        ticklabels = None  # ticklabels = _dynamic_formatting_floats(ticks)
        return (value_lims, ticks, ticklabels)
    if hasattr(norm, "vmin") and hasattr(norm, "vmax"):
        value_lims = norm.vmin, norm.vmax
        if isinstance(norm, LogNorm):
            ticks = get_log_ticks(vmin=norm.vmin, vmax=norm.vmax)
            ticklabels = None
        # TODO: SymmetricLogNorm,
        else:
            # For e.g. Normalize, CenterNorm etc.
            value_lims = norm.vmin, norm.vmax
            # Define some default ticks
            ticks = np.linspace(norm.vmin, norm.vmax, 3)
            ticklabels = None
        return (value_lims, ticks, ticklabels)
    # If we can't detect boundaries or vmin/vmax
    raise NotImplementedError(f"Unsupported {type(norm).__name__!s} norm.")


def add_bivariate_colorbar(
    *,
    bivariate_cmap,
    cax,
    origin="lower",
    aspect="auto",
    # Options
    xlabel=None,
    ylabel=None,
    title=None,
    title_kwargs=None,
    xlabel_kwargs=None,
    ylabel_kwargs=None,
    xticks_kwargs=None,
    yticks_kwargs=None,
    **imshow_kwargs,
):
    """Add a bivariate colorbar to the specified axis.

    Parameters
    ----------
    bivariate_cmap : pycolorbar.BivariateColormap
        The bivariate colormap object containing the color mapping and norms.
    cax : matplotlib.axes.Axes
        The axis on which to draw the colorbar.
    origin : {'lower', 'upper'}, optional
        The origin of the colorbar. Default is 'lower'.
    aspect: str, optional
        Either 'equal' or 'auto'.
        If 'auto' fill the Axes position rectangle with data.
        If 'equal', ensure same scaling between x and y axis.
        The default is 'auto'.
    xlabel : str, optional
        The label for the x-axis. Default is None.
    ylabel : str, optional
        The label for the y-axis. Default is None.
    title : str, optional
        The title for the colorbar. Default is None.
    title_kwargs : dict, optional
        Additional keyword arguments for the title. Default is None.
    xlabel_kwargs : dict, optional
        Additional keyword arguments for the x-axis label. Default is None.
    ylabel_kwargs : dict, optional
        Additional keyword arguments for the y-axis label. Default is None.
    xticks_kwargs : dict, optional
        Additional keyword arguments for the x-axis ticks. Default is None.
    yticks_kwargs : dict, optional
        Additional keyword arguments for the y-axis ticks. Default is None.
    **imshow_kwargs : dict, optional
        Additional keyword arguments for the `imshow` function.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object representing the bivariate colorbar.

    Raises
    ------
    ValueError
        If the norms for the bivariate colormap are not defined.
        It occurs when the bivariate colormaps has not yet been used to
        map some values to RGBA colors.

    """
    # Initialize arguments
    xticks_kwargs = {} if xticks_kwargs is None else xticks_kwargs
    yticks_kwargs = {} if yticks_kwargs is None else yticks_kwargs
    xlabel_kwargs = {} if xlabel_kwargs is None else xlabel_kwargs
    ylabel_kwargs = {} if ylabel_kwargs is None else ylabel_kwargs
    title_kwargs = {} if title_kwargs is None else title_kwargs

    # Retrieve norms
    norm_x = bivariate_cmap.norm_x
    norm_y = bivariate_cmap.norm_y
    if norm_x is None or norm_y is None:
        raise ValueError("You first need to map some values before plotting the colorbar.")

    # Define default axis options
    xlim, x_ticks, x_ticklabels = get_axis_defaults(norm_x)
    ylim, y_ticks, y_ticklabels = get_axis_defaults(norm_y)

    # Display the bivariate colormap as an image
    rgba_array = bivariate_cmap.rgba_array
    p = plot_bivariate_palette(
        rgba_array,
        ax=cax,
        xlim=xlim,
        ylim=ylim,
        disable_axis=False,
        origin="lower",
        aspect=aspect,
        **imshow_kwargs,
    )

    # Deal with log axis
    log_axis_x = isinstance(norm_x, LogNorm)
    log_axis_y = isinstance(norm_y, LogNorm)

    # Add ticks and ticklabels
    xticks_kwargs.setdefault("ticks", x_ticks)
    xticks_kwargs.setdefault("labels", x_ticklabels)
    yticks_kwargs.setdefault("ticks", y_ticks)
    yticks_kwargs.setdefault("labels", y_ticklabels)
    if xticks_kwargs.get("ticks", None) is not None:
        if log_axis_x:
            set_log_axis(ax=cax, major_ticks=xticks_kwargs["ticks"], axis="x")
        else:
            cax.set_xticks(**xticks_kwargs)
    if yticks_kwargs.get("ticks", None) is not None:
        if log_axis_y:
            set_log_axis(ax=cax, major_ticks=yticks_kwargs["ticks"], axis="y")
        else:
            cax.set_yticks(**yticks_kwargs)

    # Add labels and title
    if title is not None:
        cax.set_title(title, **title_kwargs)

    if xlabel is not None:
        cax.set_xlabel(xlabel, **xlabel_kwargs)

    if ylabel is not None:
        cax.set_ylabel(ylabel, **ylabel_kwargs)

    # Invert axis origin if specified as "upper"
    if origin == "upper":
        cax.invert_yaxis()

    return p


def add_bivariate_legend(
    *,
    bivariate_cmap,
    ax,
    # Inset options
    box_aspect=1,
    height=0.2,
    pad=0.005,
    loc="upper right",
    inside_figure=True,
    optimize_layout=True,
    # Fancybox options
    fancybox=False,
    fancybox_pad=0,
    fancybox_fc="white",
    fancybox_ec="none",
    fancybox_lw=0.5,
    fancybox_alpha=0.4,
    fancybox_shape="square",
    # Colorbar options
    **kwargs,
):
    """
    Add the bivariate colorbar legend to a plot.

    Parameters
    ----------
    bivariate_cmap : pycolorbar.BivariateColormap
        The bivariate colormap to be used for the legend.
    ax : matplotlib.axes.Axes
        The axes to which the bivariate legend will be added.
    box_aspect : float, optional
        Aspect ratio of the inset Axes. Default is 1.
    height : float, optional
        Height of the inset as a fraction [0-1] of the main Axes. Default is 0.2.
    pad : float, optional
        Padding between the inset and main Axes in figure coordinates. Default is 0.005.
    loc : str or tuple, optional
        Location of the inset. Default is 'upper right'.
    inside_figure : bool, optional
        Whether inset is inside the figure region. Default is True.
    optimize_layout : bool, optional
        Whether to auto-adjust the inset position for ticklabels. Default is True.
        NOTE: If True, do not call `fig.tight_layout()` afterwards.
    fancybox : bool, optional
        Whether to draw a fancy box behind the inset. Default is False.
    fancybox_pad : float, optional
        Padding of the fancy box in figure coordinates. Default is 0.
    fancybox_fc : str, optional
        Face color of the fancy box. Default is 'white'.
    fancybox_ec : str, optional
        Edge color of the fancy box. Default is 'none'.
    fancybox_lw : float, optional
        Line width of the fancy box. Default is 0.5.
    fancybox_alpha : float, optional
        Alpha of the fancy box. Default is 0.4.
    fancybox_shape : {'circle', 'square'}, optional
        Shape of the fancy box. Default is 'square'.
    **kwargs : dict
        Additional keyword arguments passed to the bivariate colorbar.
        See the add_bivariate_colorbar documentation.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object representing the bivariate colorbar.

    """
    # The actual colorbar plotting function
    colorbar_func = add_bivariate_colorbar
    colorbar_func_kwargs = dict(
        bivariate_cmap=bivariate_cmap,
        **kwargs,
    )
    p_cbar = add_colorbar_inset(
        ax=ax,
        colorbar_func=colorbar_func,
        colorbar_func_kwargs=colorbar_func_kwargs,
        # Inset options
        projection=None,
        box_aspect=box_aspect,
        height=height,
        pad=pad,
        loc=loc,
        inside_figure=inside_figure,
        optimize_layout=optimize_layout,
        fancybox=fancybox,
        fancybox_pad=fancybox_pad,
        fancybox_fc=fancybox_fc,
        fancybox_ec=fancybox_ec,
        fancybox_lw=fancybox_lw,
        fancybox_alpha=fancybox_alpha,
        fancybox_shape=fancybox_shape,
    )
    return p_cbar


def plot_bivariate_colorbar(
    *,
    bivariate_cmap,
    ax=None,
    cax=None,
    origin="lower",
    location="right",
    size="30%",
    pad=0.45,
    box_aspect=1,
    **kwargs,
):
    """
    Plot a bivariate colorbar.

    This function plots a 2D colorbar representing the specified
    bivariate colormap. You can either provide:

    - An existing Axes (`ax`) in which to place the colorbar (the colorbar will
      be appended to one of its sides).
    - A dedicated Axes object (`cax`) for direct drawing of the colorbar
      on the specified `cax`.
    - Or no Axes at all, in which case a new figure and Axes are created.

    If both `ax` and `cax` are given, `ax` is ignored !.

    Parameters
    ----------
    bivariate_cmap : pycolorbar.BivariateColormap
        The colormap to be used for the bivariate colorbar.
    ax : matplotlib.axes.Axes or cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        The Axes to which the colorbar should be appended. Ignored if
        `cax` is provided. If both `ax` and `cax` are None, a new figure
        and Axes are created.
    cax : matplotlib.axes.Axes, optional
        The Axes in which to directly draw the colorbar. If provided,
        `ax` is ignored.
    origin : {'lower', 'upper'}, optional
        Indicates where to locate the origin in the colorbar Axes.
        Default is 'lower'.
    location : {'right', 'left', 'top', 'bottom'}, optional
        The side of the plot where the colorbar should be placed
        (when `ax` is used). Default is 'right'.
    size : float or str, optional
        The size of the colorbar relative to the parent Axes when using
        `append_axes`. For instance, `'30%'` means 30% of the parent Axes
        width (or height, depending on `location`). Default is `'30%'`.
    pad : float, optional
        The padding between the parent Axes and the colorbar, in inches.
        Default is 0.45.
    box_aspect : float, optional
        The aspect ratio of the colorbar Axes box. Default is 1.
    **kwargs : dict
        Additional keyword arguments passed to the internal
        ``add_bivariate_colorbar`` function, which is responsible for
        actually rendering the colorbar content.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object representing the bivariate colorbar.
    """
    # Determine colorbar axis
    if cax is not None:
        pass
    elif ax is not None:  # and cax is None
        divider = make_axes_locatable(ax)
        cax = divider.append_axes(location, size=size, pad=pad, axes_class=plt.Axes)
        cax.set_box_aspect(box_aspect)
    else:
        fig, cax = plt.subplots()  # noqa: RUF059

    # Add the 2D colorbar with custom ticks
    p = add_bivariate_colorbar(
        cax=cax,
        bivariate_cmap=bivariate_cmap,
        origin=origin,
        **kwargs,
    )
    return p


####------------------------------------------------------------------------.
class BivariateColormap:
    """Class representing a bivariate colormap."""

    def __init__(self, rgba_array, *, luminance_factor=None, n=None, interp_method=None):
        """
        Initialize the bivariate colormap with an RGBA array of shape (n_y, n_x, 4).

        Parameters
        ----------
        rgba_array : numpy.ndarray
            2D RGBA array (n_y, n_x, 4) providing colors from top to bottom.
            The (x, 0) values are mapped to the corresponding color in the bottom row of the 2D RGBA array.
            The (x, 1) values are mapped to the corresponding color in the top row of the 2D RGBA array.
        n : int or tuple, optional
            Either a single integer or a (n_y, n_x) tuple specifying the number of colormap colors.
        luminance_factor : float or None, optional
            If set, apply radial-based luminance gradient.
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.
        interp_method : str, optional
            The interpolation method to use for generating the colormap.
            The default is 'cubic'.
        """
        # Ensure rgba array
        rgba_array = ensure_rgba_array(rgba_array)

        # Resample rgb array if n is specified
        n_x, n_y = check_n(n, both_integers=False)
        rgba_array = resample_rgba_array(rgba_array, n_x=n_x, n_y=n_y, interp_method=interp_method)

        # Apply luminance gradient if specified
        self.rgba_array = apply_luminance_gradient(rgba_array, luminance_factor=luminance_factor)

        # Initialize attributes
        self.shape = self.rgba_array.shape
        self.n_x = self.shape[1]
        self.n_y = self.shape[0]

        # Default “under” and “over” colors as fully transparent
        # self._under = (0.0, 0.0, 0.0, 0.0)
        # self._over = (0.0, 0.0, 0.0, 0.0)
        self._bad = (0.0, 0.0, 0.0, 0.0)

        # Initialize other arguments
        self.norm_x = None
        self.norm_y = None

    @classmethod
    def from_corners(cls, colors, n, *, luminance_factor=None, interp_method=None):
        """
        Generate a bivariate colormap from the colors at four corners.

        Parameters
        ----------
        color_list : list of color specs
            E.g. ['red', 'blue', 'green', 'black'] or precomputed array of RGBA.
        n : int or tuple
            Either a single integer or a (n_y, n_x) tuple specifying the number of colormap colors.
        luminance_factor : float or None, optional
            If set, apply radial-based luminance gradient.
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.
        interp_method : str, optional
            The interpolation method to use for generating the colormap.
            The default is 'cubic'.

        Returns
        -------
        pycolorbar.BiviariateColormap
        """
        return cls.from_colors(colors=colors, n=n, luminance_factor=luminance_factor, interp_method=interp_method)

    @classmethod
    def from_colors(cls, colors, n, *, luminance_factor=None, interp_method=None):
        """
        Generate a bivariate colormap from a set of color points interpolated onto an 2D (n_y, n_x) grid.

        Parameters
        ----------
        color_list : list of color specs
            E.g. ['red', 'blue', 'green', 'black'] or precomputed array of RGBA.
        n : int or tuple
            Either a single integer or a (n_y, n_x) tuple specifying the number of colormap colors.
        luminance_factor : float or None, optional
            If set, apply radial-based luminance gradient.
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.
        interp_method : str, optional
            The interpolation method to use for generating the colormap.
            The default is 'cubic'.

        Returns
        -------
        pycolorbar.BiviariateColormap
        """
        rgba_array = get_bivariate_cmap_from_colors(colors, n=n, interp_method=interp_method)
        return cls(rgba_array, luminance_factor=luminance_factor)

    @classmethod
    def from_cmaps(cls, cmap_x=plt.cm.Blues, cmap_y=plt.cm.Reds, n=256, *, luminance_factor=None):
        """
        Generate a bivariate colormap by blending two univariate colormaps along x and y axes.

        Parameters
        ----------
        cmap_x : matplotlib.colors.Colormap or str
            Univariate colormap for the x axis.
        cmap_y : matplotlib.colors.Colormap or str
            Univariate colormap for the y axis.
        n : int or tuple, optional
            Either a single integer or a (n_x, n_y) tuple specifying
            the number of colormap colors on the x and y axis.
            Default is 256.
        luminance_factor : float or None, optional
            If set, apply radial-based luminance gradient.
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.

        Returns
        -------
        pycolorbar.BiviariateColormap
        """
        rgba_array = get_bivariate_cmap_from_two_cmaps(cmap_x=cmap_x, cmap_y=cmap_y, n=n)
        return cls(rgba_array, luminance_factor=luminance_factor)

    @classmethod
    def from_name(cls, name, n, *, diagonal_tilt=0.8, offdiag_tilt=1.0, luminance_factor=None, interp_method=None):
        """Load a predefined bivariate colormap.

        Parameters
        ----------
        name : str
            The name of the predefined bivariate colormap to load.
            See available_biviariate_colormaps().
        n : int
            The number of colors in the colormap.
        diagonal_tilt : float, optional
            The tilt of the diagonal in the colormap, by default 0.8.
            Used only for Teuling colormaps.
        offdiag_tilt : float, optional
            The tilt of the off-diagonal in the colormap, by default 1.
            Used only for Teuling colormaps.
        interp_method : str or None, optional
            The interpolation method to use, by default None.
        luminance_factor : float or None, optional
            If set, apply radial-based luminance gradient.
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.

        Returns
        -------
        pycolorbar.BiviariateColormap
        """
        rgba_array = get_bivariate_cmap_from_name(
            name=name,
            n=n,
            diagonal_tilt=diagonal_tilt,
            offdiag_tilt=offdiag_tilt,
            interp_method=interp_method,
        )
        return cls(rgba_array, luminance_factor=luminance_factor)

    def __getitem__(self, key):
        """Retrieve a subset of the colormap."""
        if not isinstance(key, tuple) or len(key) != 2:
            raise ValueError("Exactly two slices (for y,x) are required.")

        y_slice, x_slice = key
        if not isinstance(x_slice, slice) or not isinstance(y_slice, slice):
            raise ValueError("Subset both dimensions with slice objects.")

        # Check slice length >= 2 for x dimension
        start_x, stop_x, step_x = x_slice.indices(self.rgba_array.shape[1])
        if ((stop_x - start_x) // step_x) < 2:
            raise ValueError("x slice must include at least 2 elements.")

        # Check slice length >= 2 for y dimension
        start_y, stop_y, step_y = y_slice.indices(self.rgba_array.shape[0])
        if ((stop_y - start_y) // step_y) < 2:
            raise ValueError("y slice must include at least 2 elements.")

        rgba_array = self.rgba_array.copy()[y_slice, x_slice, :]
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def __eq__(self, other):
        """Check equality of two BivariateColormap instances."""
        if not isinstance(other, BivariateColormap):
            return False
        return np.all(self.rgba_array == other.rgba_array) and self._bad == other._bad

    def __hash__(self):
        """Return a hash value for the BivariateColormap instance."""
        # TODO: also hash norm?
        return hash((self.rgba_array.tobytes(), self._bad))

    def copy(self):
        """Create a copy of the BivariateColormap instance."""
        rgba_array = self.rgba_array.copy()
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def _copy_attributes(self, new_instance):
        new_instance._bad = self._bad
        return new_instance

    def __setitem__(self, key, value):
        """Modify the colormap palette."""
        self.rgba_array[key] = value
        self.shape = self.rgba_array.shape
        self.n_x = self.shape[1]
        self.n_y = self.shape[0]

    def adapt_interval(self, interval_x=None, interval_y=None):
        """
        Subset the bivariate colormap based on the  specified interval fractions.

        Parameters
        ----------
        interval_x : tuple
            A tuple of two float values between 0 and 1, indicating the fraction of the colors to retain on the x axis.
            If None, no subsetting is performed.
        interval_y : tuple
            A tuple of two float values between 0 and 1, indicating the fraction of the colors to retain on the y axis.
            If None, no subsetting is performed.

        Returns
        -------
        pycolorbar.BiviariateColormap
        """
        from pycolorbar.univariate.cmap import check_interval

        # Check intervals
        interval_x = check_interval(interval_x)
        interval_y = check_interval(interval_y)

        # Define indexing
        n_x = self.n_x
        n_y = self.n_y
        x_start, x_end = int(interval_x[0] * n_x), int(interval_x[1] * n_x)
        y_start, y_end = int(interval_y[0] * n_y), int(interval_y[1] * n_y)
        x_indices = slice(x_start, x_end)
        y_indices = slice(y_start, y_end)
        return self[y_indices, x_indices]

    def set_bad(self, color, alpha=None):
        """
        Set the color for bad (masked) values.

        Parameters
        ----------
        color : color spec
            The color to use for bad values.
        """
        self._bad = mpl.colors.to_rgba(color, alpha=alpha)

    def set_alpha(self, alpha):
        """
        Set the alpha (transparency) value for the entire colormap.

        Parameters
        ----------
        alpha : float
            The alpha value to set, where 0 is fully transparent and 1 is fully opaque.
        """
        self.rgba_array[:, :, 3] = alpha

    def change_luminance_gradient(self, luminance_factor=None):
        """Change the luminance gradient of the colormap.

        It add a radial whitening/darkening effect.

        Parameters
        ----------
        luminance_factor : float or None
            Radial darkening is obtained with values < 1.
            Radial whitening is obtained with values > 1.
            None or 1 produce no change.

        Returns
        -------
        pycolorbar.BiviariateColormap
            The colormap with the new luminance gradient.
        """
        rgba_array = apply_luminance_gradient(self.rgba_array, luminance_factor=luminance_factor)
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def rot90(self, *, clockwise=True):
        """Rotate the colormap by 90 degrees.

        Parameters
        ----------
        clockwise : bool, optional
            If True, rotate clockwise.
            If False, rotate counterclockwise.
            Default is True.

        Returns
        -------
        pycolorbar.BiviariateColormap
            The colormap rotated by 90 degrees.
        """
        if clockwise:
            rgba_array = np.rot90(self.rgba_array, k=-1, axes=(0, 1))
        else:
            rgba_array = np.rot90(self.rgba_array, k=1, axes=(0, 1))
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def rot180(self, *, clockwise=True):
        """Rotate the colormap by 180 degrees.

        Parameters
        ----------
        clockwise : bool, optional
            If True, rotate clockwise.
            If False, rotate counterclockwise.
            Default is True.

        Returns
        -------
        pycolorbar.BiviariateColormap
            The colormap rotated by 180 degrees.
        """
        return self.rot90(clockwise=clockwise).rot90(clockwise=clockwise)

    def fliplr(self):
        """Flip the colormap array in the left/right direction.

        This method flips the RGBA array of the colormap horizontally,
        creating a mirror image along the vertical axis.
        """
        rgba_array = np.fliplr(self.rgba_array)
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def flipud(self):
        """Flip the colormap array in the up/down direction.

        This method flips the RGBA array of the colormap in the vertical direction,
        effectively reversing the order of the rows.
        """
        rgba_array = np.flipud(self.rgba_array)
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def resampled(self, *, n_x=None, n_y=None, interp_method="linear"):
        """
        Create a new BivariateColormap instance with the desired number of colors.

        Parameters
        ----------
        n_x : int, optional
            The desired number of colormap colors along the x axis.
            If None, the original number of colors is kept.
        n_y : int, optional
            The desired number of colormap colors along the y axis.
            If None, the original number of colors is kept.
        interp_method : str
            Interpolation method (e.g. "nearest", "linear", "cubic").
            The default method is "nearest".

        Returns
        -------
        BivariateCmap
            A new BivariateCmap instance resampled to have an rgba_array of shape (n_y, n_x).
        """
        rgba_array = resample_rgba_array(self.rgba_array, n_x=n_x, n_y=n_y, interp_method=interp_method)
        return self._copy_attributes(BivariateColormap(rgba_array=rgba_array))

    def __call__(self, x, y, *, norm_x=None, norm_y=None, interp_method="nearest"):
        """
        Map (x, y) data to RGBA colors based on this bivariate colormap.

        Parameters
        ----------
        x, y : array-like, pd.Series, or xarray.DataArray
            Data arrays to be mapped. Must be of the same type and shape.
        norm_x : None or mpl.colors.Normalize or BoundaryNorm
            Normalization for the x dimension. If None, default 0-1 scaling is used or computed from data.
        norm_y : None or mpl.colors.Normalize or BoundaryNorm
            Normalization for the y dimension. If None, default 0-1 scaling is used or computed from data.
        interp_method : str
            Interpolation method (e.g. "nearest", "linear", "cubic").
            The default method is "nearest".

        Returns
        -------
        Mapped result:
            - A numpy.ndarray with shape = x.shape + (4,) if x is a numpy array or pd.Series
            - An xarray.DataArray with shape = x.shape + ("rgba",) if x is an xarray.DataArray
        """
        # Check inputs
        if type(x) is not type(y):
            raise TypeError("`x` and `y` must be of the same type.")

        # Define norm if None or update with the specified
        if norm_x is None:
            self.norm_x = define_norm(x)
        else:
            self.norm_x = norm_x
        if norm_y is None:
            self.norm_y = define_norm(y)
        else:
            self.norm_y = norm_y

        # Dispatch to methods
        if (_PANDAS_AVAILABLE and isinstance(x, pd.Series)) or (_GEOPANDAS_AVAILABLE and isinstance(x, gpd.GeoSeries)):
            # Define special norm for category series
            # - The norm is ignored for remapping but it used for plotting the colorbar !
            if isinstance(x.dtype, pd.CategoricalDtype):
                self.norm_x = create_pandas_category_norm(x)
            if isinstance(y.dtype, pd.CategoricalDtype):
                self.norm_y = create_pandas_category_norm(y)
            # Map data
            return map_pandas_data(
                x,
                y,
                norm_x=self.norm_x,
                norm_y=self.norm_y,
                rgba_array=self.rgba_array,
                bad_color=self._bad,
                interp_method=interp_method,
            )
        if _XARRAY_AVAILABLE and isinstance(x, xr.DataArray):
            return map_xarray_data(
                x,
                y,
                norm_x=self.norm_x,
                norm_y=self.norm_y,
                rgba_array=self.rgba_array,
                bad_color=self._bad,
                interp_method=interp_method,
            )
        return map_array_data(
            x,
            y,
            norm_x=self.norm_x,
            norm_y=self.norm_y,
            rgba_array=self.rgba_array,
            bad_color=self._bad,
            interp_method=interp_method,
        )

    # Alias
    map = __call__

    @copy_docstring(plot_bivariate_palette)
    def plot(self, ax=None, disable_axis=True, **kwargs):  # noqa: D102
        # Plot colormap
        return plot_bivariate_palette(self.rgba_array, ax=ax, disable_axis=disable_axis, **kwargs)

    @copy_docstring(plot_bivariate_colorbar)
    def plot_colorbar(self, ax=None, cax=None, **kwargs):  # noqa: D102
        # Plot colorbar
        return plot_bivariate_colorbar(bivariate_cmap=self, ax=ax, cax=cax, **kwargs)

    @copy_docstring(add_bivariate_legend)
    def add_legend(self, ax, **kwargs):  # noqa: D102
        # Add bivariate colorbar as a legend to the plot.
        return add_bivariate_legend(bivariate_cmap=self, ax=ax, **kwargs)

    def _repr_png_(self):
        """
        Generate a PNG representation of the 2D RGBA array for this bivariate colormap.

        Returns
        -------
        bytes
            PNG-encoded bytes of the RGBA array.
        """
        import pycolorbar

        # Convert float RGBA -> 8-bit RGBA
        # shape = (height, width, 4)
        img_8bit = (self.rgba_array * 255).astype(np.uint8)

        # Create a PIL Image from the array
        image = Image.fromarray(img_8bit, mode="RGBA")

        # Resize to a constant display size
        image = image.resize(_BIVAR_REPR_PNG_SIZE, resample=Image.NEAREST)  # Image.BICUBIC)

        # Encode as PNG in memory
        png_bytes = io.BytesIO()
        pnginfo = PngInfo()
        author = f"pycolorbar v{pycolorbar.__version__}, https://github.com/ghiggi/pycolorbar"
        pnginfo.add_text("Author", author)

        image.save(png_bytes, format="png", pnginfo=pnginfo)
        return png_bytes.getvalue()

    def _repr_html_(self):
        """Generate an HTML representation of the bivariate colormap with an embedded PNG.

        This function allows to display the colormap in the IPython terminal
        and JupyterNotebook cells.
        """
        # Convert the PNG bytes to base64
        png_bytes = self._repr_png_()
        png_base64 = base64.b64encode(png_bytes).decode("ascii")
        html = (
            # Display just the 2D colormap image, no title
            f'<div class="cmap" style="border: 1px solid #555;">'
            f'  <img src="data:image/png;base64,{png_base64}" />'
            "</div>"
        )
        return html


def get_bivariate_transparancy_rgba_array(cmap, n_x, n_y, alpha_min=0.1, alpha_max=1):
    """Create the RGBA array for the bivariate transparency colormap."""
    import pycolorbar

    cmap = pycolorbar.get_cmap(cmap)

    # Generate the base colormap
    base_colors = cmap(np.linspace(0, 1, n_x))

    # Generate the alpha values
    alphas = np.linspace(alpha_max, alpha_min, n_y)

    # Create the RGBA array
    rgba_array = np.ones((n_y, n_x, 4))
    for i in range(n_y):
        rgba_array[i, :, :3] = base_colors[:, :3]
        rgba_array[i, :, 3] = alphas[i]

    return rgba_array


class BivariateTransparencyColormap(BivariateColormap):
    """Class representing a bivariate transparency colormap."""

    def __init__(self, cmap, alpha_min=0.2, alpha_max=1, n=None):
        """
        Initialize the bivariate colormap with transparency.

        Parameters
        ----------
        cmap : matplotlib.colors.Colormap or str
            The colormap to be used.
        alpha_min : float, optional
            The minimum alpha (transparency) value, by default 0.2.
        alpha_max : float, optional
            The maximum alpha (transparency) value, by default 1.
        n : int or tuple of int, optional
            The number of discrete colors in the colormap. If an integer is provided,
            it is used for both dimensions. If a tuple is provided, it should be of
            the form (n_x, n_y), where n_x is the number of colors in the x dimension
            and n_y is the number of colors in the y dimension. If None, a default
            value is used.

        Notes
        -----
        The y dimension corresponds to the transparency levels.
        """
        n_x, n_y = check_n(n)
        rgba_array = get_bivariate_transparancy_rgba_array(
            cmap=cmap,
            n_x=n_x,
            n_y=n_y,
            alpha_min=alpha_min,
            alpha_max=alpha_max,
        )
        super().__init__(rgba_array)
        self.alpha_min = alpha_min
        self.alpha_max = alpha_max
