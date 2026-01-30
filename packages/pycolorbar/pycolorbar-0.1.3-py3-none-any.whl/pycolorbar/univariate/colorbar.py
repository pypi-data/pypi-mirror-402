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
"""Module with functions to plot univariate colorbars."""
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable

from pycolorbar.utils.mpl_legend import add_colorbar_inset


def _get_orientation_location(cbar_kwargs):

    location = cbar_kwargs.get("location", None)
    orientation = cbar_kwargs.get("orientation", None)

    # Set defaults
    if location is None and orientation is None:
        return "vertical", "right"

    # Check orientation is horizontal or vertical
    if orientation is not None and orientation not in ("horizontal", "vertical"):
        raise ValueError("Invalid orientation. Choose 'horizontal' or 'vertical'.")
    # Check location is top, left, right or bottom
    if location is not None and location not in ("top", "left", "right", "bottom"):
        raise ValueError("Invalid location. Choose 'top', 'left', 'right', or 'bottom'.")

    # Check compatible arguments
    if orientation is not None and location is not None:
        if orientation == "vertical":
            # Raise error if not right or left
            if location not in ("right", "left"):
                raise ValueError("Invalid location for vertical orientation. Choose 'right' or 'left'.")
        elif location not in ("bottom", "top"):
            raise ValueError("Invalid location for horizontal orientation. Choose 'bottom' or 'top'.")
        return orientation, location

    # Return with default location if missing
    if orientation is not None:
        if orientation == "vertical":
            return "vertical", "right"
        return "horizontal", "bottom"

    # Return with correct orientation if missing
    # if location is not None:
    if location in ("right", "left"):
        return "vertical", location
    return "horizontal", location


def plot_colorbar(p, *, ax=None, cax=None, **cbar_kwargs):
    """Add a univariate colorbar to a matplotlib/cartopy plot.

    You can either provide:

    - An existing Axes (`ax`) in which to place the colorbar (the colorbar will
      be appended to one of its sides).
    - A dedicated Axes object (`cax`) for direct drawing of the colorbar
      on the specified `cax`.
    - Or no Axes at all, in which case a new figure and Axes are created.

    If both `ax` and `cax` are given, `ax` is ignored !.

    Parameters
    ----------
    mappable
        The matplotlib.cm.ScalarMappable (i.e., AxesImage, ContourSet, etc.)
        described by the colorbar.
    ax : matplotlib.axes.Axes or cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        The Axes to which the colorbar should be appended. Ignored if
        `cax` is provided. If both `ax` and `cax` are None, a new figure
        and Axes are created.
    cax : matplotlib.axes.Axes, optional
        The Axes in which to directly draw the colorbar. If provided,
        `ax` is ignored.
    **cbar_kwargs : dict
        Additional keyword arguments passed to the ``matplotlib.figure.colorbar``.
        See the ``matplotlib.figure.colorbar`` documentation.
        Arguments 'size' and 'pad' controls the size of the colorbar.
        and the padding between the plot and the colorbar only if cax is not specified !.

    """
    cbar_kwargs = cbar_kwargs.copy()  # otherwise pop ticklabels outside the function
    ticklabels = cbar_kwargs.pop("ticklabels", None)
    label_position = cbar_kwargs.pop("label_position", None)

    # Define orientation
    orientation, location = _get_orientation_location(cbar_kwargs)

    # Define colorbar axis
    if cax is None and ax is not None:
        # Define colorbar axis
        divider = make_axes_locatable(ax)
        if orientation == "vertical":
            size = cbar_kwargs.pop("size", "5%")
            pad = cbar_kwargs.get("pad", 0.1)
            cax = divider.append_axes(location, size=size, pad=pad, axes_class=plt.Axes)
        else:  # orientation == "horizontal":
            size = cbar_kwargs.pop("size", "5%")
            pad = cbar_kwargs.get("pad", 0.25)
            cax = divider.append_axes(location, size=size, pad=pad, axes_class=plt.Axes)
        p.figure.add_axes(cax)

    # Add colorbar
    cbar = plt.colorbar(mappable=p, cax=cax, ax=ax, **cbar_kwargs)
    if ticklabels is not None:
        # Retrieve ticks
        ticks = cbar_kwargs.get("ticks", None)
        if ticks is None:
            ticks = cbar.get_ticks()
        # Remove existing ticklabels
        cbar.set_ticklabels([])
        cbar.set_ticklabels([], minor=True)
        # Add custom ticklabels
        p.colorbar.set_ticks(ticks, labels=ticklabels)
        # _ = cbar.ax.set_yticklabels(ticklabels) if orientation == "vertical" else cbar.ax.set_xticklabels(ticklabels)
    if label_position is not None:
        if orientation == "vertical":
            cbar.ax.yaxis.set_label_position(label_position)
        else:
            cbar.ax.xaxis.set_label_position(label_position)
    return cbar


def add_colorbar_legend(
    *,
    mappable,
    ax,
    # Inset options
    box_aspect=1,
    height=0.2,
    pad=0.005,
    loc="upper right",
    inside_figure=True,
    optimize_layout=True,
    # Fancybox options
    fancybox=False,
    fancybox_pad=0,
    fancybox_fc="white",
    fancybox_ec="none",
    fancybox_lw=0.5,
    fancybox_alpha=0.4,
    fancybox_shape="square",
    # Colorbar options
    **cbar_kwargs,
):
    """
    Add a univariate colorbar legend to a plot.

    Parameters
    ----------
    mappable
        The matplotlib.cm.ScalarMappable (i.e., AxesImage, ContourSet, etc.)
        described by the colorbar.
    ax : matplotlib.axes.Axes
        The axes to which the bivariate legend will be added.
    box_aspect : float, optional
        Aspect ratio of the inset Axes. Default is 1.
    height : float, optional
        Height of the inset as a fraction [0-1] of the main Axes. Default is 0.2.
    pad : float, optional
        Padding between the inset and main Axes in figure coordinates. Default is 0.005.
    loc : str or tuple, optional
        Location of the inset. Default is 'upper right'.
    inside_figure : bool, optional
        Whether inset is inside the figure region. Default is True.
    optimize_layout : bool, optional
        Whether to auto-adjust the inset position for ticklabels. Default is True.
        NOTE: If True, do not call `fig.tight_layout()` afterwards.
    fancybox : bool, optional
        Whether to draw a fancy box behind the inset. Default is False.
    fancybox_pad : float, optional
        Padding of the fancy box in figure coordinates. Default is 0.
    fancybox_fc : str, optional
        Face color of the fancy box. Default is 'white'.
    fancybox_ec : str, optional
        Edge color of the fancy box. Default is 'none'.
    fancybox_lw : float, optional
        Line width of the fancy box. Default is 0.5.
    fancybox_alpha : float, optional
        Alpha of the fancy box. Default is 0.4.
    fancybox_shape : {'circle', 'square'}, optional
        Shape of the fancy box. Default is 'square'.
    **kwargs : dict
        Additional keyword arguments passed to the ``matplotlib.figure.colorbar``.
        See the ``matplotlib.figure.colorbar`` documentation.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object representing the colorbar.

    """
    # The actual colorbar plotting function
    colorbar_func = plot_colorbar
    colorbar_func_kwargs = dict(
        p=mappable,
        **cbar_kwargs,
    )
    p_cbar = add_colorbar_inset(
        ax=ax,
        colorbar_func=colorbar_func,
        colorbar_func_kwargs=colorbar_func_kwargs,
        # Inset options
        projection=None,
        box_aspect=box_aspect,
        height=height,
        pad=pad,
        loc=loc,
        inside_figure=inside_figure,
        optimize_layout=optimize_layout,
        fancybox=fancybox,
        fancybox_pad=fancybox_pad,
        fancybox_fc=fancybox_fc,
        fancybox_ec=fancybox_ec,
        fancybox_lw=fancybox_lw,
        fancybox_alpha=fancybox_alpha,
        fancybox_shape=fancybox_shape,
    )
    return p_cbar


def set_colorbar_fully_transparent(p):
    """Set the colorbar of a plot fully transparent.

    This is useful for animation where the colorbar should
    not always in all frames but the plot area must be fixed.
    """
    # Get the position of the colorbar
    cbar_pos = p.colorbar.ax.get_position()

    cbar_x, cbar_y = cbar_pos.x0, cbar_pos.y0
    cbar_width, cbar_height = cbar_pos.width, cbar_pos.height

    # Remove the colorbar
    p.colorbar.ax.set_visible(False)

    # Now plot an empty rectangle
    fig = plt.gcf()
    rect = plt.Rectangle(
        (cbar_x, cbar_y),
        cbar_width,
        cbar_height,
        transform=fig.transFigure,
        facecolor="none",
        edgecolor="none",
    )

    fig.patches.append(rect)
