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
"""Directory utility functions."""
import glob
import os
import pathlib


def remove_file_if_exists(filepath, force=False):
    """Remove a file if exists.

    Raise an error if the filepath is an existing directory.
    """
    if os.path.exists(filepath):
        if os.path.isdir(filepath):
            raise ValueError("The specified {filepath} file path is an existing directory !")
        if force:
            os.remove(filepath)
        else:
            raise ValueError(f"The {filepath} already exists !")


def _recursive_glob(dir_path, glob_pattern):
    # ** search for all files recursively
    # glob_pattern = os.path.join(base_dir, "**", "metadata", f"{station_name}.yml")
    # metadata_filepaths = glob.glob(glob_pattern, recursive=True)

    dir_path = pathlib.Path(dir_path)
    return [str(path) for path in dir_path.rglob(glob_pattern)]


def list_paths(dir_path, glob_pattern, recursive=False):
    """Return a list of filepaths and directory paths."""
    if not recursive:
        return glob.glob(os.path.join(dir_path, glob_pattern))
    return _recursive_glob(dir_path, glob_pattern)


def list_files(dir_path, glob_pattern, recursive=False):
    """Return a list of filepaths (exclude directory paths)."""
    paths = list_paths(dir_path, glob_pattern, recursive=recursive)
    return [f for f in paths if os.path.isfile(f)]
