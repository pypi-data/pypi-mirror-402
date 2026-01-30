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
"""Implementation of pydantic validator for univariate colorbar YAML files."""

import re

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from pycolorbar.norm import check_boundaries, check_categories
from pycolorbar.utils.mpl import get_mpl_colormaps, get_mpl_named_colors

####---------------------------------------------------------------------------------------------------------.
#### Colormap Settings


class ColormapSettings(BaseModel):
    """Pydantic model for colormap settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str | list[str]
    n: int | list[int] | None = None
    bad_color: str | list | tuple | None = None
    bad_alpha: float | None = None
    over_color: str | list | tuple | None = None
    over_alpha: float | None = None
    under_color: str | list | tuple | None = None
    under_alpha: float | None = None

    @field_validator("name")
    def validate_name(cls, v):
        """Validate colormap ``name``.

        Check if colormap ``name`` a registered ``matplotlib`` or ``pycolorbar`` colormap.
        """
        import pycolorbar

        if isinstance(v, str):
            valid_names = get_mpl_colormaps() + pycolorbar.colormaps.names
            assert v in valid_names, f"'{v}' is not a recognized colormap name."
        elif isinstance(v, list):
            for name in v:
                valid_names = get_mpl_colormaps() + pycolorbar.colormaps.names
                assert name in valid_names, f"'{name}' is not a recognized colormap name."
        return v

    @field_validator("n")
    def validate_n(cls, v, values):
        """Validate ``n`` values."""
        if v is not None:
            validated_settings = values.data
            # Single colormap
            if isinstance(validated_settings.get("name"), str):
                assert isinstance(v, int), "'n' must be an integer."
                assert v > 0, "'n' must be a positive integer."
            # Multiple colormaps
            if isinstance(validated_settings.get("name"), list):
                assert len(validated_settings.get("name")) == len(
                    v,
                ), "'n' must match the number of color maps in 'name'."
                for n in v:
                    assert isinstance(n, int), "'n' must be an integer."
                    assert n > 0, "'n' values must be positive integers."
        return v

    @field_validator("bad_color", "over_color", "under_color")
    def validate_colors(cls, v):
        """Validate ``colors`` values."""
        if v is not None:
            if isinstance(v, str):
                if v == "none":
                    return v
                # Check if it's a named color
                if v in get_mpl_named_colors():
                    return v
                # Check if it's a hex color
                hex_color_pattern = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")
                if not hex_color_pattern.match(v):
                    raise ValueError(
                        'Invalid color format. Expected hex string like "#RRGGBB" or "#RRGGBBAA", or a named color.',
                    )
            elif isinstance(v, (list, tuple)) and len(v) in [3, 4]:
                # Check if it's an RGB or RGBA tuple
                if not all(
                    isinstance(color_component, (int, float)) and 0 <= color_component <= 1 for color_component in v
                ):
                    raise ValueError("Invalid RGB/RGBA format. Expected tuple with values between 0 and 1.")
                v = tuple(v)
            else:
                raise ValueError("Invalid color format. Expected a named color, hex string, or RGB/RGBA tuple.")
        return v

    @field_validator("bad_alpha", "under_alpha", "over_alpha")
    def validate_bad_alpha(cls, v):
        """Validate ``bad_alpha`` values."""
        if v is not None:
            assert 0 <= v <= 1, "bad_alpha must be between 0 and 1"
        return v


####-------------------------------------------------------------------------------------------------------------------.
#### Norm Settings


def _check_norm_invalid_args(norm_name, args, valid_args):
    invalid_keys = set(args) - set(valid_args)
    if invalid_keys:
        raise ValueError(f"Invalid parameters {invalid_keys} for normalization type '{norm_name}'.")


def _check_vmin_vcenter_vmax(vmin, vcenter, vmax, norm_name):
    if vmin is not None and vcenter is not None:
        assert vmin < vcenter, f"'vmin' must be less than 'vcenter' for '{norm_name}'."
    if vmax is not None and vcenter is not None:
        assert vcenter < vmax, f"'vmax' must be larger than 'vcenter' '{norm_name}'."


def _check_vmin_vmax(vmin, vmax):
    assert isinstance(vmin, (int, float, type(None))), "'vmin' must be an integer, float or None."
    assert isinstance(vmax, (int, float, type(None))), "'vmax' must be an integer, float or None."
    if vmin is not None and vmax is not None:
        assert vmin < vmax, "vmin must be less than vmax."


def _check_clip(clip):
    assert isinstance(clip, bool), "'clip' must be either True or False."


def _check_extend(extend):
    valid_extends = ["neither", "both", "min", "max"]
    assert extend in valid_extends, f"Invalid extend option '{extend}'. Valid options are {valid_extends}."


def _get_boundary_norm_expected_ncolors(norm_settings):
    boundaries = norm_settings.get("boundaries", [])
    extend = norm_settings.get("extend", "neither")
    if extend == "neither":
        required_ncolors = len(boundaries) - 1
    elif extend in ["min", "max"]:
        required_ncolors = len(boundaries)
    else:  #  extend == 'both':
        required_ncolors = len(boundaries) + 1
    return required_ncolors


class NormalizeSettings(BaseModel):
    """Pydanctic model for ``Normalize`` settings."""

    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``Normalize``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for ``Normalize``."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``Normalize``."""
        valid_args = {"vmin", "vmax", "clip"}
        _check_norm_invalid_args(norm_name="Normalize", args=values.keys(), valid_args=valid_args)
        return values


class CategoryNormSettings(BaseModel):
    """Pydantic model for ``CategoryNorm`` settings."""

    categories: dict = Field(..., description="A dictionary encoding values and category labels.")

    @field_validator("categories")
    def validate_categories(cls, v):
        """Validate ``categories`` dictionary for ``CategoryNorm``."""
        categories = check_categories(categories=v)
        return categories

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``CategoryNorm``."""
        valid_args = {"categories"}
        _check_norm_invalid_args(norm_name="CategoryNorm", args=values.keys(), valid_args=valid_args)
        return values


class CategorizeNormSettings(BaseModel):
    """Pydantic model for ``CategorizeNorm`` settings."""

    boundaries: list[float] = Field(..., description="A list of boundary values.")
    labels: list[str] = Field(..., description="A list of labels corresponding to the categories.")

    @field_validator("boundaries")
    def validate_boundaries(cls, v):
        """Validate ``labels`` for ``CategorizeNorm``."""
        boundaries = check_boundaries(boundaries=v)
        return boundaries

    @field_validator("labels")
    def validate_labels(cls, v):
        """Validate ``first_value`` for ``CategorizeNorm``."""
        assert all(isinstance(label, (str)) for label in v), "'labels' must be a list of string."
        return v

    @model_validator(mode="after")
    def validate_boundaries_label_size(self):
        """Validate ``boundaries`` and ``labels`` size for ``CategorizeNorm``."""
        boundaries = self.boundaries
        labels = self.labels
        n_categories = len(labels)
        expected_n = len(boundaries) - 1
        if n_categories != expected_n:
            raise ValueError(f"'labels' size must be {expected_n} given the size of 'boundaries'.")
        return self

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``CategorizeNorm``."""
        valid_args = {"labels", "boundaries"}
        _check_norm_invalid_args(norm_name="CategorizeNorm", args=values.keys(), valid_args=valid_args)
        return values


class BoundaryNormSettings(BaseModel):
    """Pydantic model for ``BoundaryNorm`` settings."""

    boundaries: list[float] = Field(..., description="A list of boundary values.")
    clip: bool | None = False
    extend: str | None = "neither"
    ncolors: int | None = None  # "ncolors" if not specified is determined based on len(boundaries) and extend

    @field_validator("boundaries")
    def validate_boundaries(cls, v):
        """Validate ``boundaries`` list for ``BoundaryNorm``."""
        boundaries = check_boundaries(boundaries=v)
        return boundaries

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``BoundaryNorm``."""
        _check_clip(v)
        return v

    @field_validator("extend")
    def validate_extend(cls, v):
        """Validate ``extend`` option for ``BoundaryNorm``."""
        if v is not None:
            _check_extend(v)
        return v

    @model_validator(mode="before")
    def validate_ncolors(self):
        """Validate ``ncolors`` for ``BoundaryNorm``."""
        validated_settings = self
        ncolors = validated_settings.get("ncolors")
        extend = validated_settings.get("extend")
        if ncolors is not None:
            assert isinstance(ncolors, int), "'ncolors' must be an integer for 'BoundaryNorm'."
            assert ncolors >= 2, "'ncolors' must be equal or larger than 2."
            # - If extend is "neither" (default) there must be equal or larger than len(boundaries) - 1 colors.
            # - If extend is "min" or "max" ncolors must be equal or larger than len(boundaries)
            # - If extend is "both"  ncolors must be equal or larger than len(boundaries) + 1
            required_ncolors = _get_boundary_norm_expected_ncolors(norm_settings=validated_settings)
            if extend == "neither":
                assert (
                    ncolors >= required_ncolors
                ), f"'ncolors' must be equal or larger than len('boundaries') - 1 ({required_ncolors})."
            elif extend in ["min", "max"]:
                assert (
                    ncolors >= required_ncolors
                ), f"'ncolors' must be equal or larger than len('boundaries') ({required_ncolors})."
            elif extend == "both":
                assert (
                    ncolors >= required_ncolors
                ), f"'ncolors' must be equal or larger than len('boundaries') + 1 ({required_ncolors})."
        else:
            ncolors = _get_boundary_norm_expected_ncolors(norm_settings=validated_settings)
        self.update({"ncolors": ncolors})
        return self

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``BoundaryNorm``."""
        valid_args = {"boundaries", "ncolors", "clip", "extend"}
        _check_norm_invalid_args(norm_name="BoundaryNorm", args=values.keys(), valid_args=valid_args)
        return values


class NoNormSettings(BaseModel):
    """Pydanctic model for ``NoNorm`` settings."""

    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``NoNorm``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for ``NoNorm``."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``NoNorm``."""
        valid_args = {"vmin", "vmax", "clip"}
        _check_norm_invalid_args(norm_name="NoNorm", args=values.keys(), valid_args=valid_args)
        return values


class CenteredNormSettings(BaseModel):
    """Pydantic model for ``CenteredNorm`` settings."""

    vcenter: int | float | None = 0
    halfrange: int | float | None = None
    clip: bool | None = False

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``CenteredNorm``."""
        _check_clip(v)
        return v

    @field_validator("vcenter")
    def validate_vcenter(cls, v):
        """Validate ``vcenter`` for ``CenteredNorm``."""
        assert isinstance(v, (int, float)), "'vcenter' must be an integer or float."
        return v

    @field_validator("halfrange")
    def validate_halfrange(cls, v):
        """Validate ``halfrange`` for ``CenteredNorm``."""
        if v is not None:
            assert isinstance(v, (int, float)), "'halfrange' must be an integer, float or None."
        return v

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``CenteredNorm``."""
        valid_args = {"vcenter", "halfrange", "clip"}
        _check_norm_invalid_args(norm_name="CenteredNorm", args=values.keys(), valid_args=valid_args)
        return values


class TwoSlopeNormSettings(BaseModel):
    """Pydantic model for ``TwoSlopeNorm`` settings."""

    vcenter: float = Field(..., description="Value over which to center the colormap.")
    vmin: float | None = None
    vmax: float | None = None

    @field_validator("vcenter")
    def validate_vcenter(cls, v):
        """Validate ``vcenter`` for ``TwoSlopeNorm``."""
        assert isinstance(v, (int, float)), "'vcenter' must be an integer or float."
        return v

    @model_validator(mode="before")
    def check_vmin_vcenter_vmax(cls, values):
        """Check ``vmin`, ``vcenter``, and ``vmax`` for  ``TwoSlopeNorm``."""
        vmin, vcenter, vmax = values.get("vmin"), values.get("vcenter"), values.get("vmax")
        _check_vmin_vcenter_vmax(vmin=vmin, vcenter=vcenter, vmax=vmax, norm_name="TwoSlopeNorm")
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``TwoSlopeNorm``."""
        valid_args = {"vcenter", "vmin", "vmax"}
        _check_norm_invalid_args(norm_name="TwoSlopeNorm", args=values.keys(), valid_args=valid_args)
        return values


class LogNormSettings(BaseModel):
    """Pydantic model for ``LogNorm`` settings."""

    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``LogNorm``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for ``LogNorm``."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        if vmin is not None and vmin <= 0:
            raise ValueError("LogNorm vmin should be a positive value.")
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``LogNorm``."""
        valid_args = {"vmin", "vmax", "clip"}
        _check_norm_invalid_args(norm_name="LogNorm", args=values.keys(), valid_args=valid_args)
        return values


class SymLogNormSettings(BaseModel):
    """Pydanctic model for ``SymLogNorm`` settings."""

    linthresh: float = Field(..., description="SymLogNorm linthres value.")
    linscale: float | None = 1.0
    base: float | None = 10
    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("linthresh")
    def validate_linthresh(cls, v):
        """Validate ``linthresh`` for SymLogNorm."""
        assert v > 0, "'linthresh' must be positive for 'SymLogNorm'."
        return v

    @field_validator("linscale", "base")
    def validate_linscale_base(cls, v, field):
        """Validate ``linscale`` and `base` for ``SymLogNorm``."""
        if v is not None:
            assert v > 0, f"'{field.name}' must be positive for 'SymLogNorm'."
        return v

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``SymLogNorm``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for ``SymLogNorm``."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``SymLogNorm``."""
        valid_args = ["linthresh", "linscale", "vmin", "vmax", "clip", "base"]
        _check_norm_invalid_args(norm_name="SymLogNorm", args=values.keys(), valid_args=valid_args)
        return values


class PowerNormSettings(BaseModel):
    """Pydantic model for ``PowerNorm`` settings."""

    gamma: float = Field(..., description="PowerNorm gamma value.")
    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("gamma")
    def validate_gamma(cls, v):
        """Validate ``gamma`` for ``PowerNorm``."""
        assert isinstance(v, (int, float)), "'gamma' must be an integer or float."
        return v

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``PowerNorm``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for PowerNorm."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``PowerNorm``."""
        valid_args = ["gamma", "vmin", "vmax", "clip"]
        _check_norm_invalid_args(norm_name="PowerNorm", args=values.keys(), valid_args=valid_args)
        return values


class AsinhNormSettings(BaseModel):
    """Pydantic model for ``AsinhNorm`` settings."""

    linear_width: int | float | None = 1
    vmin: float | None = None
    vmax: float | None = None
    clip: bool | None = False

    @field_validator("linear_width")
    def validate_linear_width(cls, v):
        """Validate ``linear_width`` for ``AsinhNorm``."""
        assert isinstance(v, (int, float)), "'linear_width' must be an integer or float."
        return v

    @field_validator("clip")
    def validate_clip(cls, v):
        """Validate ``clip`` option for ``AsinhNorm``."""
        _check_clip(v)
        return v

    @model_validator(mode="before")
    def check_vmin_vmax(cls, values):
        """Check ``vmin`` and ``vmax`` for ``AsinhNorm``."""
        vmin, vmax = values.get("vmin"), values.get("vmax")
        _check_vmin_vmax(vmin, vmax)
        return values

    @model_validator(mode="before")
    def check_valid_args(cls, values):
        """Check for no excess parameters in ``AsinhNorm``."""
        valid_args = ["linear_width", "vmin", "vmax", "clip"]
        _check_norm_invalid_args(norm_name="AsinhNorm", args=values.keys(), valid_args=valid_args)
        return values


def _check_valid_norm_name(name):
    """Check if the norm name is valid."""
    valid_names = [
        "Norm",
        "NoNorm",
        "BoundaryNorm",
        "TwoSlopeNorm",
        "CenteredNorm",
        "LogNorm",
        "SymLogNorm",
        "PowerNorm",
        "AsinhNorm",
        "CategoryNorm",
        "CategorizeNorm",
    ]
    if name not in valid_names:
        raise ValueError(f"Invalid norm '{name}'. Valid options are {valid_names}.")


def check_norm_settings(norm_settings):
    """Validate norm settings."""
    # Check valid *Norm name
    norm_settings = norm_settings.copy()
    name = norm_settings.pop("name", "Norm")
    _check_valid_norm_name(name)
    # Define *Norm validators
    norm_settings_mapping = {
        "Norm": NormalizeSettings,
        "NoNorm": NoNormSettings,
        "BoundaryNorm": BoundaryNormSettings,
        "TwoSlopeNorm": TwoSlopeNormSettings,
        "CenteredNorm": CenteredNormSettings,
        "LogNorm": LogNormSettings,
        "SymLogNorm": SymLogNormSettings,
        "PowerNorm": PowerNormSettings,
        "AsinhNorm": AsinhNormSettings,
        "CategoryNorm": CategoryNormSettings,
        "CategorizeNorm": CategorizeNormSettings,
    }
    # Retrieve NormSettings Validator
    validator = norm_settings_mapping[name]
    # Validate settings
    norm_settings = validator(**norm_settings).model_dump()
    # Return validated settings (adding back the name !)
    norm_settings["name"] = name
    return norm_settings


####-------------------------------------------------------------------------------------------------------------------.


class ColorbarSettings(BaseModel):
    """Pydantic model for colorbar settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    extend: str | None = "neither"
    extendfrac: float | list[float] | str | None = "auto"
    extendrect: bool | None = False
    label: str | None = None  # title of colorbar
    ticklabels: list[str] | None = None
    ticks: list[int | float] | None = None  # title of colorbar
    ticklocation: str | None = "auto"
    spacing: str | None = "uniform"  # or proportional
    drawedges: bool | None = False
    shrink: float | None = 1

    @field_validator("extend")
    def validate_extend(cls, v):
        """Validate extend option."""
        if v is not None:
            _check_extend(v)
        return v

    @field_validator("extendfrac")
    def validate_extendfrac(cls, v):
        """Validate extend fraction."""
        if v is not None:
            if isinstance(v, list):
                assert all(
                    isinstance(frac, (float, int)) and 0 <= frac <= 1 for frac in v
                ), "Each extendfrac in the list must be a float or int between 0 and 1."
            elif isinstance(v, str):
                assert v == "auto", "'extendfrac' must not be a string."
            else:
                assert isinstance(v, (float, int)), "extendfrac must be a float or int"
                assert 0 <= v <= 1, "extendfrac must be between 0 and 1."
        return v

    @field_validator("extendrect")
    def validate_extendrect(cls, v):
        """Validate extend rectangle option."""
        if v is not None:
            assert isinstance(v, bool), "extendrect must be a boolean value."
        return v

    @field_validator("label")
    def validate_label(cls, v):
        """Validate label as string."""
        if v is not None:
            assert isinstance(v, str), "label must be a string."
        return v


####-------------------------------------------------------------------------------------------------------------------.


def resolve_colorbar_reference(cbar_dict, name, checked_references=None):
    """Resolve a colorbar reference in a colorbar dictionary."""
    import pycolorbar

    keys = list(cbar_dict)
    if len(keys) > 1 and np.any(np.isin(keys, ["auxiliary", "reference"], invert=True)):
        raise ValueError("If referencing another colorbar, only 'reference' and 'auxiliary' keys are allowed.")

    # Retrieve reference
    reference_name = cbar_dict["reference"]

    # Check reference is available
    if reference_name not in pycolorbar.colorbars.names:
        raise ValueError(f"The '{reference_name}' colorbar is not registered in pycolorbar. Invalid reference !")

    # Check for circular references
    if checked_references is None:
        checked_references = []
    if reference_name in checked_references:
        raise ValueError(f"Circular reference detected with '{reference_name}'.")

    # Retrieve new dictionary
    cbar_ref_dict = pycolorbar.colorbars.get_cbar_dict(reference_name, validate=False)

    # If another reference, visit recursively the references
    if "reference" in cbar_ref_dict:
        checked_references.append(name)
        return resolve_colorbar_reference(cbar_ref_dict, name=reference_name, checked_references=checked_references)

    # Return the original colorbar dictionary
    return cbar_ref_dict


def _check_discrete_norm_cmap_settings(cmap_settings, norm_settings):
    """Validate or set the 'n' default value for discrete colormaps."""
    norm = norm_settings.get("name", "Norm")
    if norm not in ["BoundaryNorm", "CategoryNorm", "CategorizeNorm"]:
        return cmap_settings, norm_settings

    # Retrieve expected number of colors
    if norm in ["CategorizeNorm"]:
        expected_ncolors = len(norm_settings["labels"])
    elif norm == "CategoryNorm":
        expected_ncolors = len(norm_settings["categories"])
    else:  # "BoundaryNorm"
        expected_ncolors = _get_boundary_norm_expected_ncolors(norm_settings=norm_settings)

    n = cmap_settings.get("n", None)
    # If n is specified, check is consistent
    if n is not None:
        # Check it match expectations
        # - Single Colormap
        if isinstance(n, int):
            assert (
                n == expected_ncolors
            ), f"'n' is optional and must be {expected_ncolors} for the specified discrete norm."
        # - Multiple colormaps
        else:
            assert (
                sum(n) == expected_ncolors
            ), f"The sum of 'n' must be {expected_ncolors} for the specified discrete norm."
    # Else specify the expected value
    else:
        n = expected_ncolors
    cmap_settings["n"] = n
    return cmap_settings, norm_settings


def validate_cbar_dict(cbar_dict: dict, name: str, resolve_reference=False):
    """Validate a colorbar dictionary."""
    # Raise error for empty dictionary or wrong type
    if not isinstance(cbar_dict, dict):
        raise TypeError("The colorbar dictionary must be a dictionary.")
    if len(cbar_dict) == 0:
        raise ValueError("The colorbar dictionary can not be empty.")
    # Copy the dictionary before modifying it
    cbar_dict = cbar_dict.copy()
    # Check if cbar_dict reference to another colorbar settings
    if "reference" in cbar_dict:
        referenced_cbar_dict = resolve_colorbar_reference(cbar_dict, name=name)
        if resolve_reference:
            cbar_dict = referenced_cbar_dict
        else:
            return cbar_dict

    # Retrieve cmap, norm and cbar settings
    cmap_settings = cbar_dict["cmap"]
    norm_settings = cbar_dict.get("norm", {})
    cbar_settings = cbar_dict.get("cbar", {})

    # Test validity
    invalid_configuration = False

    try:
        cmap_settings = ColormapSettings(**cmap_settings).model_dump()
    except Exception as e:
        invalid_configuration = True
        print(f"Colormap validation error: {e}")

    try:
        norm_settings = check_norm_settings(norm_settings)
    except Exception as e:
        invalid_configuration = True
        print(f"Norm validation error: {e}")

    try:
        cbar_settings = ColorbarSettings(**cbar_settings).model_dump()
    except Exception as e:
        invalid_configuration = True
        print(f"Colorbar validation error: {e}")

    # Consistency checks
    try:
        cmap_settings, norm_settings = _check_discrete_norm_cmap_settings(
            cmap_settings=cmap_settings,
            norm_settings=norm_settings,
        )
    except Exception as e:
        invalid_configuration = True
        print(f"Categorical Colormap validation error: {e}")

    if invalid_configuration:
        raise ValueError("Invalid configuration")

    # Return the validated dictionary
    cbar_dict["cmap"] = cmap_settings
    cbar_dict["norm"] = norm_settings
    cbar_dict["cbar"] = cbar_settings
    return cbar_dict
