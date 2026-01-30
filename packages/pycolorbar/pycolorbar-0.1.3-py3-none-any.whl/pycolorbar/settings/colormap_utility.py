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
"""Define functions to build colormaps in multiple color spaces."""

# import numpy as np
# import matplotlib as mpl
# import matplotlib.pyplot as plt
import matplotlib.colors
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

IMPLEMENTED_COLOR_SPACE = ["name", "rgb", "rgba", "hex", "hsv"]


def convert_colors(colors, color_space):
    """Convert colors to the RGB color space."""
    #  TODO: IMPLEMENT !
    if color_space.lower() not in IMPLEMENTED_COLOR_SPACE:
        raise NotImplementedError(f"Color space '{color_space}' not yet implemented.")
    if color_space == "hsv":  # noqa SIM108
        colors = matplotlib.colors.hsv_to_rgb(colors)
    # elif
    #   IMPLEMENT
    else:  # rgb, rgba, name, hex
        colors = matplotlib.colors.to_rgba_array(colors)
    return colors


def create_cmap(cmap_dict, name):
    """Create a colormap from the colormap dictionary."""
    cmap_type = cmap_dict["colormap_type"]
    color_space = cmap_dict["color_space"]

    n = cmap_dict.get("n", None)
    colors = cmap_dict.get("color_palette", None)
    segmentdata = cmap_dict.get("segmentdata", None)
    gamma = cmap_dict.get("gamma", 1.0)

    # Convert colors to interpolation space
    # - if ListedColormap --> RGBA
    # - if LinearSegmentedColormap --> interpolation_space (default RGBA)
    # --> TODO: or create Colormap Classes interpolating in the <interpolation_space>
    if colors is not None:
        colors = convert_colors(colors, color_space)

    # Create Colormap
    if cmap_type == "ListedColormap":
        return ListedColormap(colors, name=name, N=n)
    # LinearSegmentedColormap from list
    if segmentdata is None:
        if n is None:
            n = 256  # matplotlib default

        # Retrieve n colors in 'interpolation_space' (when type=LinearSegmentedColormap)
        # TODO

        # Retrieve colormap
        return LinearSegmentedColormap.from_list(name=name, colors=colors, N=n, gamma=gamma)
    # LinearSegmentedColormap with segmentdata
    segmentdata = cmap_dict["segmentdata"]
    return LinearSegmentedColormap(name=name, segmentdata=segmentdata, gamma=gamma)
