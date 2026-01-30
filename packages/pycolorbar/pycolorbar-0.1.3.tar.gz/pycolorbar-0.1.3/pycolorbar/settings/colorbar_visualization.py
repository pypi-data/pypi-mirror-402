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
"""Define functions to visualize univariate colorbars."""
import math

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np


def _draw_colorbar(plot_kwargs, cbar_kwargs, fig, ax=None, cax=None):
    # Retrieve ticklabels (not accepted yet by fig.colorbar)
    ticklabels = cbar_kwargs.pop("ticklabels", None)
    # Display colorbar
    cbar = fig.colorbar(
        mpl.cm.ScalarMappable(**plot_kwargs),
        ax=ax,
        cax=cax,
        orientation="horizontal",
        **cbar_kwargs,
    )
    if ticklabels is not None:
        cbar.set_ticklabels(ticklabels)
    return cbar


def plot_colorbar(plot_kwargs, cbar_kwargs, ax=None, subplot_size=(6, 1), dpi=100):
    """Plot a single colorbar."""
    # Initialize figure if necessary
    if ax is None:
        fig, ax = plt.subplots(figsize=subplot_size, layout="constrained", dpi=dpi)
    # Draw figure
    _ = _draw_colorbar(plot_kwargs=plot_kwargs, cbar_kwargs=cbar_kwargs, fig=fig, ax=None, cax=ax)
    plt.show()


def plot_colorbars(list_args, cols=None, subplot_size=None, dpi=200):
    """Plot multiple colorbars in a single figure."""
    # If a single colorbar setting, plot with plot_colorbar
    if len(list_args) == 1:
        name, plot_kwargs, cbar_kwargs = list_args[0]
        return plot_colorbar(plot_kwargs=plot_kwargs, cbar_kwargs=cbar_kwargs, dpi=dpi)

    # Define subplot_size
    if subplot_size is None:
        subplot_size = (5, 1.2)  # 3 --> 2

    # Define number of subplots
    n = len(list_args)

    # Define a layout most similar to a square
    if cols is None:
        cols = math.ceil(math.sqrt(n))
        cols = min(cols, 2)

    # Define number of rows required
    rows = int(np.ceil(n / cols))

    # Define figure width and height
    fig_width = cols * subplot_size[0]
    fig_height = rows * subplot_size[1]

    # Initialize figure
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height), dpi=dpi)

    # Flatten axes for easy iteration
    axes = axes.ravel()

    # Loop through colorbars and axes
    for (name, plot_kwargs, cbar_kwargs), ax in zip(list_args, axes, strict=False):
        _ = _draw_colorbar(plot_kwargs=plot_kwargs, cbar_kwargs=cbar_kwargs, fig=fig, ax=None, cax=ax)
        ax.set_title(name, fontsize=10, weight="bold")
    # Turn off any remaining axes
    for ax in axes[n:]:
        ax.axis("off")

    fig.tight_layout()
    plt.show()
    return fig


def show_colorbar(name=None, user_plot_kwargs=None, user_cbar_kwargs=None, fig_size=(6, 1)):
    """Show a single pycolorbar colorbar."""
    from pycolorbar import colorbars

    if user_cbar_kwargs is None:
        user_cbar_kwargs = {}
    if user_plot_kwargs is None:
        user_plot_kwargs = {}
    colorbars.show_colorbar(
        name=name,
        user_plot_kwargs=user_plot_kwargs,
        user_cbar_kwargs=user_cbar_kwargs,
        fig_size=fig_size,
    )


def show_colorbars(category=None, exclude_referenced=True, subplot_size=None):
    """Show pycolorbar colorbars."""
    from pycolorbar import colorbars

    colorbars.show_colorbars(category=category, exclude_referenced=exclude_referenced, subplot_size=subplot_size)
