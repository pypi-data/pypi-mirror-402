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
"""Implementation of pydantic validator for univariate colormap YAML files."""
import itertools
import re

import numpy as np
from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from pycolorbar.colors.colors_io import check_valid_external_data_range, check_valid_internal_data_range
from pycolorbar.utils.mpl import get_mpl_named_colors


def get_valid_color_space():
    """Get list of valid color spaces."""
    return [
        "hex",
        "name",
        "rgb",
        "rgba",
        "hcl",
        "lch",
        "hsv",
        "cieluv",
        "cielab",
        "ciexyz",
        "cmyk",
    ]


def check_color_space(color_space):
    """Check color space validity."""
    valid_names = get_valid_color_space()
    if color_space.lower() not in valid_names:
        raise ValueError(f"Invalid color_space '{color_space}'. The supported color spaces are {valid_names}.")
    return color_space.lower()


def is_monotonically_increasing(values):
    """Check if a list of values is monotonically increasing."""
    return all(x <= y for x, y in itertools.pairwise(values))


class ColormapValidator(BaseModel):
    """
    A validator for colormap configurations using Pydantic.

    Validates the fields of a colormap configuration, including the type of colormap,
    the color space, the colors themselves, and the alpha transparency settings.

    Attributes
    ----------
    colors_decoded: bool
        If ``True``, assumes that the colors have been already decoded (internal representation).
        If ``False``, assumes that the colors have not been decoded (external representation).
        The default is ``True``.
    colormap_type : str
        The type of the colormap (e.g., ``ListedColormap``, ``LinearSegmentedColormap``).
    color_space : str
        The color space of the colormap (e.g., ``rgb``, ``hsv``).
    color_palette : numpy.ndarray
        The array of colors defined for the colormap.

    Methods
    -------
    validate_colormap_type(cls, v):
        Validates the colormap_type field.
    validate_color_space(cls, v):
        Validates the color_space field.
    validate_colors(cls, v, values):
        Validates the colors field.
    validate_segmentdata(cls, v, values)
        Validates the segmentdata field.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    # NOTE: The order here governs the call and validation order of below methods

    # Internal flag
    colors_decoded: bool | None = True

    # Mandatory colormap fields
    colormap_type: str
    color_space: str

    # Optional colormap fields
    color_palette: np.ndarray | list | None = None  # mandatory if segmentdata not provided !
    segmentdata: dict | None = None  # LinearSegmentedColormap
    # gamma: Optional[float] = None   # LinearSegmentedColormap

    n: int | None = None  # None for ListedColormap, 256 for LinearSegmentedColormap
    auxiliary: dict | None = {}  # auxiliary information of the colormap (not checked !)

    # --------------------------------------------------
    # TODO:
    # - interpolation_space? 'rgb', ...
    # - add gamma option
    # - correctly support segmentdata

    @field_validator("colormap_type")
    def validate_colormap_type(cls, v):
        """Validate the ``colormap_type`` field."""
        valid_colormap_types = [
            "ListedColormap",
            "LinearSegmentedColormap",
        ]
        assert isinstance(v, str), "'colormap_type' must be a string."
        assert v in valid_colormap_types, f"'colormap_type' must be one of {valid_colormap_types}"
        return v

    @field_validator("color_space")
    def validate_color_space(cls, v):
        """Validate the ``color_space`` field."""
        check_color_space(color_space=v)
        return v

    @field_validator("colors_decoded")
    def validate_colors_decoded(cls, v):
        """Validate the ``colors_decoded`` flag."""
        assert isinstance(v, bool), "colors_decoded must be a boolean."
        return v

    @field_validator("color_palette")
    def validate_color_palette(cls, v, values):
        """Validate the ``color_palette`` array."""
        if v is not None:
            v = np.asanyarray(v)
            color_space = values.data.get("color_space", "")
            assert len(v) > 0, "The 'color_palette' array must not be empty."
            assert len(v) > 1, "The 'color_palette' array must have at least 2 colors."
            validate_colors_values(v, color_space=color_space, decoded_colors=values.data.get("colors_decoded"))
        return v

    @field_validator("segmentdata")
    def validate_segmentdata(cls, v, values):
        """Validate the ``segmentdata`` dictionary."""
        if v is not None:
            assert (
                values.data.get("colormap_type") == "LinearSegmentedColormap"
            ), "'segmentdata' requires the 'colormap_type' 'LinearSegmentedColormap'."

            # Check the keys
            # - alpha can also be provided
            required_keys = ["red", "green", "blue"]
            if any(key not in v for key in required_keys):
                raise ValueError(f"'segmentdata' dictionary must contain keys: {required_keys}.")

            # Check only valid keys
            valid_keys = ["red", "green", "blue", "alpha"]
            if any(key not in valid_keys for key in v):
                raise ValueError(f"'segmentdata' dictionary can contain only keys: {valid_keys}.")

            # Validate structure
            for key in required_keys:
                if not all(isinstance(item, (list, tuple)) and len(item) == 3 for item in v[key]):
                    raise ValueError(f"Each item in '{key}' must be a tuple of three floats.")
                # Positions must be monotonically increasing
                positions = [item[0] for item in v[key]]
                if not is_monotonically_increasing(positions):
                    raise ValueError(f"Positions in '{key}' must be monotonically increasing.")

            # Ensure positions and color values are float and list is used instead of tuple
            v = {k: [[float(value) for value in triplet] for triplet in list_values] for k, list_values in v.items()}

            # TODO:
            # - Currently support only rgb and rgba and does not encode/decode!
            # - Support encoding/decoding of the dictionary (with keys having different sizes ...)
            # - Allow for all color spaces !

        return v

    @model_validator(mode="after")
    def validate_colors_inputs(self):
        """Validate ``segmentdata`` and ``color_palette``."""
        segmentdata = self.segmentdata
        color_palette = self.color_palette
        # Check segmentadata or color_palette is specified
        if segmentdata is None and color_palette is None:
            raise ValueError("Specify 'color_palette' or 'segmentdata'")
        # Check only one between segmentadata and color_palette is specified
        if segmentdata is not None and color_palette is not None:
            raise ValueError("Either specify 'color_palette' or 'segmentdata'")
        return self


def _set_default_n(cmap_dict):
    # If 'n' is specified, set as integer
    if cmap_dict["n"] is not None:
        cmap_dict["n"] = int(cmap_dict["n"])

    # Set default value for LinearSegmentedColormap.from_list
    if (
        cmap_dict["n"] is None
        and cmap_dict["segmentdata"] is None
        and cmap_dict["colormap_type"] == "LinearSegmentedColormap"
    ):
        cmap_dict["n"] = 256

    return cmap_dict


def validate_cmap_dict(cmap_dict: dict, decoded_colors=True):
    """
    Check the validity of a colormap dictionary.

    Parameters
    ----------
    cmap_dict : dict
        Colormap dictionary.
    decoded_colors : bool, optional
        Whether the colors are decoded (internal representation) or not. The default is True.

    Returns
    -------
    cmap_dict : dict
        Validated colormap dictionary.

    """
    # TODO: currently assumes that colors are already decoded (i.e. in 0-1 range for RGB)]
    # TODO: currently do not check segmentadata colors
    # TODO: set defaults with pydantic?
    # --> Return what ColormapValidator returns?

    # Set flag for color validation
    cmap_dict["colors_decoded"] = decoded_colors

    # Validate dictionary
    cmap_dict = ColormapValidator(**cmap_dict).model_dump()
    cmap_dict = _set_default_n(cmap_dict)

    # Remove flag for color validation
    _ = cmap_dict.pop("colors_decoded")

    # Return dictionary
    return cmap_dict


####-------------------------------------------------------------------------------------------------------------------.


def _check_ndim(colors: np.ndarray, expected_ndim: int):
    """
    Checks if the colors array has the expected number of dimensions.

    Parameters
    ----------
    colors : numpy.ndarray
        The array of colors to validate.
    expected_ndim : int
        The expected number of dimensions for the colors array.

    Raises
    ------
    ValueError
        If the colors array does not have the expected number of dimensions.
    """
    if colors.ndim != expected_ndim:
        raise ValueError(f"Colors array must be {expected_ndim}-D.")


def _check_type(colors: np.ndarray, expected_type: type):
    """
    Checks if the color values in the colors array are of the expected type.

    Parameters
    ----------
    colors : numpy.ndarray
        The array of colors to validate.
    expected_type : type
        The expected data type(s) of the color values.

    Raises
    ------
    ValueError
        If the color values are not of the expected type.
    """
    if not issubclass(colors.dtype.type, expected_type):
        str_type = str(expected_type)
        raise ValueError(f"Color values must be of type {str_type}.")


def validate_hex_colors(colors: np.ndarray) -> bool:
    """
    Validates the array of HEX colors.

    Parameters
    ----------
    colors : numpy.ndarray
        The array of colors to validate.

    Raises
    ------
    ValueError
        If the colors array is not 1-D or if any color is not a valid hex string.
    """
    _check_ndim(colors, 1)
    _check_type(colors, np.str_)
    hex_color_pattern = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    if not all(hex_color_pattern.match(color) for color in colors):
        raise ValueError(
            "Invalid color format for 'hex'. "
            "Colors should be strings starting with '#' and followed by 3 or 6 hex digits.",
        )


def validate_name_colors(colors: np.ndarray) -> bool:
    """
    Validates the array of named colors.

    For more info on named colors, see https://matplotlib.org/stable/gallery/color/named_colors.html

    Parameters
    ----------
    colors : numpy.ndarray
        The array of colors to validate.

    Raises
    ------
    ValueError
        If the colors array is not 1-D, if color values are not strings,
        or if any color name is not a valid named color.
    """
    _check_ndim(colors, 1)
    _check_type(colors, np.str_)
    valid_named_colors = get_mpl_named_colors()
    invalid_colors = colors[~np.isin(colors, valid_named_colors)]
    if len(invalid_colors) > 0:
        raise ValueError(f"Invalid named colors: {invalid_colors}.")


def validate_colors_values(colors, color_space, decoded_colors=True):
    """
    Validates the colors array based on the specified color space.

    Parameters
    ----------
    colors : numpy.ndarray
        The array of colors to validate.
    color_space : str
        The color space of the colors array (e.g., "hex", "rgb", "rgba", etc.).
    decoded_colors: bool
        If True, assumes that the colors are decoded (internal representation).
        If False, assumes that the colors are not decoded (external representation).

    Raises
    ------
    ValueError
        If the color_space is not supported or if the colors array fails
        validation checks for the specified color space.
    """
    # Check valid color space
    color_space = check_color_space(color_space)
    # Check valid color values
    if color_space == "name":
        validate_name_colors(colors)
    elif color_space == "hex":
        validate_hex_colors(colors)
    elif decoded_colors:
        check_valid_internal_data_range(colors, color_space=color_space.upper())
    else:
        check_valid_external_data_range(colors, color_space=color_space.upper())


####-------------------------------------------------------------------------------------------------------------------.
