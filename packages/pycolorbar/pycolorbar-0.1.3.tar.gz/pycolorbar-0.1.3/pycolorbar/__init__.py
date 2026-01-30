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
import contextlib
import os
from importlib.metadata import PackageNotFoundError, version

from pycolorbar.bivariate.cmap import (  # noqa
    BivariateColormap,
    BivariateTransparencyColormap,
    available_bivariate_colormaps,
)
from pycolorbar.settings.colorbar_registry import (  # noqa
    ColorbarRegistry,
    available_colorbars,
    get_cbar_dict,
    get_plot_kwargs,
    register_colorbar,
    register_colorbars,
)
from pycolorbar.settings.colorbar_validator import validate_cbar_dict  # noqa
from pycolorbar.settings.colorbar_visualization import show_colorbar, show_colorbars  # noqa
from pycolorbar.settings.colormap_registry import (  # noqa
    ColormapRegistry,
    available_colormaps,
    check_colormap_archive,
    get_cmap,
    get_cmap_dict,
    register_colormap,
    register_colormaps,
)
from pycolorbar.settings.colormap_validator import validate_cmap_dict  # noqa
from pycolorbar.settings.colormap_visualization import show_colormap, show_colormaps  # noqa
from pycolorbar.univariate.colorbar import add_colorbar_legend, plot_colorbar, set_colorbar_fully_transparent  # noqa

# Create a module-level instance of ColormapRegistry
colormaps = ColormapRegistry.get_instance()

# Create a module-level instance of ColorbarRegistry
colorbars = ColorbarRegistry.get_instance()

# Register pycolorbar defaults colormaps and colorbars
# TODO: donfig config !
# pycolorbar.register_default_colormaps()
# pycolorbar.register_default_colorbars()
_root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
etc_directory = os.path.join(_root_path, "pycolorbar", "etc")


__all__ = []

# Get version
with contextlib.suppress(PackageNotFoundError):
    __version__ = version("pycolorbar")
