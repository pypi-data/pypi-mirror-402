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
"""Define functions to read and write colormap YAML files."""

import numpy as np

from pycolorbar.colors.colors_io import decode_colors, encode_colors
from pycolorbar.settings.colormap_validator import validate_cmap_dict
from pycolorbar.utils.directories import remove_file_if_exists
from pycolorbar.utils.yaml import read_yaml, write_yaml


def _check_presence_required_keys(cmap_dict):
    required_params = ["color_palette", "segmentdata"]
    required_params_present = np.isin(required_params, list(cmap_dict))
    # if np.all(required_params_present):
    #     raise KeyError("The colormap dictionary must contain either the 'color_palette' or 'segmentdata' keys.")
    if not np.any(required_params_present):
        raise KeyError("The colormap dictionary must contain the 'color_palette' or 'segmentdata' keys.")
    if "color_palette" in cmap_dict and "color_space" not in cmap_dict:
        raise KeyError("The colormap dictionary does not contain the 'color_space' key.")


def _ensure_colors_array(colors):
    """Ensure the colors object is a numpy array."""
    return np.asanyarray(colors)


def _ensure_color_palette_list(colors):
    """Ensure the colors object is a list to properly save it to YAML."""
    if isinstance(colors, np.ndarray):
        if colors.ndim in [1, 2]:
            colors = colors.tolist()
        else:
            raise ValueError("Invalid 'color_palette' numpy array. Should be either 1D or 2D.")
    return colors


def _ensure_segmentdata_list(segmentdata):
    """Ensure positions and color values are float and list is used instead of tuple."""
    return {
        k: [[float(value) for value in triplet] for triplet in list_values] for k, list_values in segmentdata.items()
    }


def read_cmap_dict(filepath, decode=True, validate=True):
    """Read a pycolorbar colormap YAML file.

    By default, the colormap YAML file are validated at read-time.
    Set `validate=False` to not validate the dictionary at read-time.
    """
    cmap_dict = read_yaml(filepath)

    # Check required keys
    _check_presence_required_keys(cmap_dict)

    # Preprocess color_palette
    if cmap_dict.get("color_palette", None) is not None:
        # Ensure color_palette is a numpy array
        cmap_dict["color_palette"] = _ensure_colors_array(cmap_dict["color_palette"])
        # By default, convert colors to internal representation  (i.e. rgb: 0-255 --> 0-1)
        if decode:
            cmap_dict["color_palette"] = decode_colors(
                colors=cmap_dict["color_palette"],
                color_space=cmap_dict["color_space"],
            )
    # By default, validate colors
    if validate:
        cmap_dict = validate_cmap_dict(cmap_dict, decoded_colors=decode)
    return cmap_dict


def write_cmap_dict(cmap_dict, filepath, force=False, encode=True, validate=True):
    """Write a pycolorbar colormap YAML file.

    By default, the colormap YAML file are validated before writing it.
    It assumes that the specified colors are in the internal representation (decoded).
    """
    # Make a copy of the dictionary (before validation and encoding) !
    cmap_dict = cmap_dict.copy()
    # Check required keys
    _check_presence_required_keys(cmap_dict)
    # Remoe file if exists and force=True
    remove_file_if_exists(filepath, force=force)
    # By default, validate colors (assuming internal representation)
    if validate:
        cmap_dict = validate_cmap_dict(cmap_dict=cmap_dict, decoded_colors=True)
    # By default, convert color_palette colors to external representation (i.e. rgb: 0-1 --> 0-255)
    # - segmentdata is currently not encoded/decoded
    if cmap_dict.get("color_palette", None) is not None:
        if encode:
            cmap_dict["color_palette"] = encode_colors(
                colors=cmap_dict["color_palette"],
                color_space=cmap_dict["color_space"],
            )
        # Ensure colors is a list of list
        cmap_dict["color_palette"] = _ensure_color_palette_list(cmap_dict["color_palette"])
    else:
        # Ensure segmentdata values are floats within lists
        cmap_dict["segmentdata"] = _ensure_segmentdata_list(cmap_dict["segmentdata"])

    # Write file
    write_yaml(cmap_dict, filepath, sort_keys=False)
