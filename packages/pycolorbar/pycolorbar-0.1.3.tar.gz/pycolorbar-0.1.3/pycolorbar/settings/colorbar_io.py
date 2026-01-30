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
"""Define functions to read and write colorbar YAML files."""
import os

import numpy as np

from pycolorbar.settings.colorbar_validator import validate_cbar_dict
from pycolorbar.utils.directories import remove_file_if_exists
from pycolorbar.utils.yaml import read_yaml, write_yaml


def is_single_colorbar_settings(dictionary):
    """Determine if a dictionary is a single colorbar settings."""
    return np.any(np.isin(["cmap", "norm", "cbar", "auxiliary"], list(dictionary)))


def read_cbar_dict(filepath, name=None, validate=False):
    """Read colorbar YAML file with single colorbar settings.

    This is an helper function and is not used by the ColorbarRegistry.

    By default, the colorbar YAML file are not validated at read-time.
    Set `validate=True` to validate the dictionary at read-time.
    """
    cbar_dict = read_yaml(filepath)
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    if validate:
        cbar_dict = validate_cbar_dict(cbar_dict, name=name)
    return cbar_dict


def read_cbar_dicts(filepath):
    """Read colorbar YAML file with a single or multiple colorbar settings.

    By default, the colorbar YAML file are not validated at read time !
    """
    dictionary = read_yaml(filepath)
    # If not single colorbar settings, returns the cbar_dicts
    if not is_single_colorbar_settings(dictionary):
        return dictionary
    # Otherwise retrieve colorbar name from filename
    filename = os.path.basename(filepath)
    name = os.path.splitext(filename)[0]
    # Return the setting in the cbar_dicts format
    return {name: dictionary}


def write_cbar_dict(cbar_dict, name, filepath, force=False, validate=True):
    """Write a single colorbar settings dictionary to a YAML file.

    By default, the colorbar YAML file are validated before writing to disk !
    """
    # Check if file exist
    remove_file_if_exists(filepath, force=force)
    # Validate fields
    if validate:
        cbar_dict = validate_cbar_dict(cbar_dict=cbar_dict, name=name)
    # Write file
    write_yaml(cbar_dict, filepath, sort_keys=False)


def write_cbar_dicts(cbar_dicts, filepath, names=None, force=False, sort_keys=False, validate=True):
    """Write a multiple colorbar settings dictionary to a YAML file.

    By default, the colorbar YAML file are validated before writing to disk !
    """
    if isinstance(names, str):
        names = [names]

    # Check if file exist
    remove_file_if_exists(filepath, force=force)

    # Select colorbars
    if names is not None:
        cbar_dicts = {name: cbar_dicts[name] for name in names}

    # Validate colorbars
    if validate:
        cbar_dicts = {
            name: validate_cbar_dict(cbar_dict=cbar_dict, name=name) for name, cbar_dict in cbar_dicts.items()
        }

    # Write file
    write_yaml(cbar_dicts, filepath, sort_keys=sort_keys)
