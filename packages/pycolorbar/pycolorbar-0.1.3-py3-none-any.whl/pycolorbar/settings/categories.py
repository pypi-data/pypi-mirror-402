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
"""Define utilities for pycolorbar colormap categories."""

import matplotlib.pyplot as plt
import numpy as np

CMAP_CATEGORIES = [
    "PERCEPTUAL",
    "SEQUENTIAL",
    "DIVERGING",
    "QUALITATIVE",
    "CATEGORICAL",
    "CYCLIC",
    "RAINBOW",
    "SPECTRAL",
]


def _get_mpl_cmap_by_category(cmap_category):
    """Return matplotlib colormap names by category.

    See: https://matplotlib.org/stable/users/explain/colors/colormaps.html#choosing-colormaps
    """
    type_dict = {
        "PERCEPTUAL": [
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "cividis",
        ],  # PERCEPTUALLY UNIFORM
        "SEQUENTIAL": [
            "viridis",
            "plasma",
            "inferno",
            "magma",
            "cividis",
            "Greys",
            "Purples",
            "Blues",
            "Greens",
            "Oranges",
            "Reds",
            "YlOrBr",
            "YlOrRd",
            "OrRd",
            "PuRd",
            "RdPu",
            "BuPu",
            "GnBu",
            "PuBu",
            "YlGnBu",
            "PuBuGn",
            "BuGn",
            "YlGn",
            "binary",
            "gist_yarg",
            "gist_gray",
            "gray",
            "bone",
            "pink",
            "spring",
            "summer",
            "autumn",
            "winter",
            "cool",
            "Wistia",
            "hot",
            "afmhot",
            "gist_heat",
            "copper",
        ],
        "DIVERGING": [
            "PiYG",
            "PRGn",
            "BrBG",
            "PuOr",
            "RdGy",
            "RdBu",
            "RdYlBu",
            "RdYlGn",
            "Spectral",
            "coolwarm",
            "bwr",
            "seismic",
        ],
        "QUALITATIVE": [
            "Pastel1",
            "Pastel2",
            "Paired",
            "Accent",
            "Dark2",
            "Set1",
            "Set2",
            "Set3",
            "tab10",
            "tab20",
            "tab20b",
            "tab20c",
        ],
        "CYCLIC": ["twilight", "twilight_shifted", "hsv"],
        "RAINBOW": ["brg", "hsv", "nipy_spectral", "rainbow", "gist_rainbow", "jet", "gist_ncar"],
        "SPECTRAL": ["Spectral"],
    }
    type_dict["CATEGORICAL"] = type_dict["QUALITATIVE"]
    return type_dict.get(cmap_category.upper(), [])


def get_matplotlib_cmaps(category=None, include_reversed=False):
    """Return matplotlib colormaps names."""
    # If category is None, return all matplotlib colormaps
    if category is None:
        names = plt.colormaps()
        if not include_reversed:
            names = [name for name in names if not name.endswith("_r")]
        return names

    # If category is specified but is not a colormap type category, return an empty list !
    if not is_cmap_category(category):
        return []

    # Retrieve colormaps of given type(s)
    # - i.e. Spectral is "diverging" but also "rainbow" type
    category = check_category_list(category)
    possible_names = [_get_mpl_cmap_by_category(cmap_category=cmap_category) for cmap_category in category]
    names = find_common_strings(possible_names)

    # Include names with _r suffix
    if include_reversed:
        names = [name + "_r" for name in names] + names
    return names


def find_common_strings(lists):
    """
    Find common strings across multiple lists.

    Parameters
    ----------
    lists : list of lists
        A list containing multiple lists of strings.

    Returns
    -------
    list
        A list of strings that are common across all lists.
    """
    # If there's only one list, return it as it is
    if len(lists) == 1:
        return lists[0]

    # Otherwise, use np.intersect1d iteratively to get common strings across lists
    common_strings = lists[0]
    for lst in lists[1:]:
        common_strings = np.intersect1d(common_strings, lst)
    return list(common_strings)


def check_category_list(category):
    """Ensure category is a list or None."""
    if category is None or len(category) == 0:
        return None
    if isinstance(category, str):
        category = [category]
    category = [cat.upper() for cat in category]
    return category


def is_cmap_category(category):
    """Test if the input category(s) is a colormap type category."""
    category = check_category_list(category)
    return np.all(np.isin(category, CMAP_CATEGORIES))


def get_aux_category(dictionary):
    """Retrieve list of categories keys from a cmap or colorbar dictionary.

    It ensure the output is a list with upper case strings.
    """
    if "auxiliary" in dictionary:
        category = dictionary["auxiliary"].get("category", [])
        category = check_category_list(category)
        return category
    return []
