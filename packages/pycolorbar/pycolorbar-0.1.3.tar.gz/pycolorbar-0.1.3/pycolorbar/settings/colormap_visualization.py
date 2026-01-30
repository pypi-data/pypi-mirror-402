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
"""Define functions to visualize univariate colormaps."""

from pycolorbar.settings.categories import check_category_list
from pycolorbar.univariate import plot_colormap, plot_colormaps


def show_colormap(cmap):
    """Show a registered colormap."""
    from pycolorbar import get_cmap

    cmap = get_cmap(cmap)
    plot_colormap(cmap)


def show_colormaps(category=None, include_reversed=False, cols=None, subplot_size=None):
    """Show all registered colormaps."""
    import pycolorbar

    # Retrieve list of colormaps names
    category = check_category_list(category)  # return upper case names
    if category is not None and "PYCOLORBAR" in category:
        category = [category for category in category if category != "PYCOLORBAR"]
        names = pycolorbar.colormaps.available(category=category, include_reversed=include_reversed)
    else:  # include also matplotlib colormaps
        names = pycolorbar.available_colormaps(category=category, include_reversed=include_reversed)

    # Retrieve colormaps to display
    cmaps = [pycolorbar.get_cmap(name) for name in sorted(names)]

    # Display colormaps
    if len(cmaps) > 0:
        plot_colormaps(cmaps, cols=cols, subplot_size=subplot_size)
    else:
        print(f"No colormaps are available for categories '{category}'.")
