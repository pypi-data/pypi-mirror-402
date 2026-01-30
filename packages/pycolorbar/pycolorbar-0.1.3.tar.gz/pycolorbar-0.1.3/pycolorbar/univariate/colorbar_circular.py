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
"""Module with functions to plot circular univariate colorbars."""
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle, Wedge
from mpl_toolkits.axes_grid1 import make_axes_locatable

from pycolorbar.utils.mpl_legend import add_colorbar_inset

# Alternative solution:
# - Draw pies and mask with inner disk: https://stackoverflow.com/questions/59877425/python-matplotlib-donut-chart-with-smaller-width-on-one-wedge
# - However does not allow for full transparency in the inner circle ...


def _create_wedges(r_min, r_max, n, center, theta_offset, direction):
    """
    Create a list of wedges (annular sectors) for a circular colorbar.

    Parameters
    ----------
    r_min : float
        Inner radius of the wedges.
    r_max : float
        Outer radius of the wedges.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5)
    n : int
        Number of discrete wedges to create.
    theta_offset : float
        Offset angle (in degrees) for the starting point of the wedges.
    direction : int
        Rotation direction (-1 for clockwise, 1 for counterclockwise).

    Returns
    -------
    list of Wedge
        List of matplotlib Wedge objects representing the colorbar sectors.
    """
    wedges = []
    width = r_max - r_min
    for i in range(n):
        # Define start angle
        theta1 = (direction * (360 * i / n) - theta_offset) % 360
        # Define end angle
        theta2 = (direction * (360 * (i + 1) / n) - theta_offset) % 360
        if direction == 1:
            wedge = Wedge(center, r_max, theta1, theta2, width=width)
        else:
            wedge = Wedge(center[0], r_max, theta2, theta1, width=width)
        wedges.append(wedge)
    return wedges


def _get_ticklabels_alignment(tick):
    """
    Determine horizontal and vertical alignment for tick labels based on their position.

    Parameters
    ----------
    tick : float
        The angle (in degrees) of the current tick.

    Returns
    -------
    tuple of (str, str)
        Horizontal and vertical alignment for the tick label. Possible values for horizontal alignment are
        'left', 'right', and 'center'. For vertical alignment, 'top', 'bottom', or 'center' are returned.
    """
    # Normalize the angle to [0, 360)
    tick = tick % 360

    # Quadrant-based alignment:
    #  - Quadrant I (0 to < 90):    label corner is bottom-left
    #  - Quadrant II (90 to < 180): label corner is bottom-right
    #  - Quadrant III (180 to < 270): label corner is top-right
    #  - Quadrant IV (270 to < 360): label corner is top-left
    # This ensures that the radial line "touches" the same corner of the text.
    if 0 <= tick < 90:
        ha = "left"
        va = "bottom"
    elif 90 <= tick < 180:
        ha = "right"
        va = "bottom"
    elif 180 <= tick < 270:
        ha = "right"
        va = "top"
    else:  # 270 <= tick < 360
        ha = "left"
        va = "top"

    return ha, va

    # Determine horizontal alignment (ha) based on quadrant
    # ha = "left" if 0 <= tick < 90 or 270 <= tick < 360 else "right"
    # # Special case for ticks near the top and bottom
    # if 85 <= tick <= 95:
    #     ha = "center"
    #     va = "bottom"  # Labels at the top
    # elif 265 <= tick <= 275:
    #     ha = "center"
    #     va = "top"  # Labels at the bottom
    # else:
    #     # General vertical alignment: depends on top/bottom half of the circle
    #     va = "center" if 0 <= tick < 180 else "center"
    # return ha, va


def _add_ticklabels(
    ax,
    center,
    ticks,
    ticklabels,
    r_max,
    direction,
    theta_offset,
    ticklabels_pad=0.05,
    ticklabels_size=10,
):
    """
    Add tick labels to the circular colorbar.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes on which to add the tick labels.
    ticks : array-like
        The angular positions of the ticks (in degrees).
    ticklabels : array-like
        List of labels to display at each tick.
    r_max : float
        Outer radius of the colorbar where the labels will be positioned.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5)
    direction : int
        Rotation direction (-1 for clockwise, 1 for counterclockwise).
    theta_offset : float
        Offset angle (in degrees) for the starting point of the ticks.
    ticklabels_pad : float, optional
        Radial offset for tick labels, by default 0.05.

    Returns
    -------
    None
    """
    ticks = (direction * ticks - theta_offset) % 360
    for tick, label in zip(ticks, ticklabels, strict=False):
        ha, va = _get_ticklabels_alignment(tick)
        ax.text(
            center[0] + np.cos(np.deg2rad(tick)) * (r_max + ticklabels_pad),
            center[1] + np.sin(np.deg2rad(tick)) * (r_max + ticklabels_pad),
            label,
            horizontalalignment=ha,
            verticalalignment=va,
            fontsize=ticklabels_size,
        )


def _add_ticks(ax, ticks, r_max, direction, theta_offset, center, ticklength=0.03, tickcolor="black", tickwidth=2):
    """
    Add tick marks to the circular colorbar.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes on which to add the tick marks.
    ticks : array-like
        The angular positions of the ticks (in degrees).
    r_max : float
        Outer radius of the colorbar where the tick marks will be positioned.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5)
    direction : int
        Rotation direction (-1 for clockwise, 1 for counterclockwise).
    theta_offset : float
        Offset angle (in degrees) for the starting point of the ticks.
    ticklength : float, optional
        Length of the tick marks, by default 0.03.
    tickcolor : str, optional
        Color of the tick marks, by default 'black'.
    tickwidth : float, optional
        Line width of the tick marks, by default 2.

    Returns
    -------
    None
    """
    ticks = (direction * ticks - theta_offset) % 360
    for tick in ticks:
        # Add small tick lines
        tick_line_x = [
            center[0] + np.cos(np.deg2rad(tick)) * r_max,
            center[0] + np.cos(np.deg2rad(tick)) * (r_max + ticklength),
        ]  # Small extension for tick
        tick_line_y = [
            center[1] + np.sin(np.deg2rad(tick)) * r_max,
            center[1] + np.sin(np.deg2rad(tick)) * (r_max + ticklength),
        ]  # Small extension for tick
        ax.plot(tick_line_x, tick_line_y, color=tickcolor, lw=tickwidth)


def _set_adaptive_limits(ax, r_max, center, margin_factor=0.1):
    """
    Set adaptive x and y limits based on the given radii, with a margin.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes on which to set the limits.
    r_max : float
        Outer radius of the colorbar.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5)
    margin_factor : float, optional
        Fraction of `r_max` to use as margin around the colorbar, by default 0.1.

    Returns
    -------
    None
    """
    # Calculate margin based on the maximum radius
    margin = margin_factor * r_max
    # Calculate the limits for the axes
    xlim = center[0] - (r_max + margin), center[0] + (r_max + margin)
    ylim = center[1] - (r_max + margin), center[1] + (r_max + margin)
    # Set the limits
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)


def plot_circular_colorbar_wedges(
    cmap,
    *,
    # Location
    ax=None,
    cax=None,
    location="right",
    size="30%",
    pad=0.3,
    box_aspect=1,
    # Appearance
    r_min=0.2,
    r_max=0.5,
    center=(0.5, 0.5),
    adapt_limits=True,
    zero_location="N",
    clockwise=True,
    antialiased=False,
    # Contour
    add_contour=True,
    contour_color="black",
    contour_linewidth=None,
    wedges_edgecolor="none",
    wedges_linewidths=None,
    # Ticks
    add_ticks=True,
    ticks=None,
    ticklength=0.02,
    tickcolor="black",
    tickwidth=1,
    # Ticklabels
    ticklabels=None,
    ticklabels_pad=0.05,
    ticklabels_size=10,
):
    """
    Plot a circular colorbar using wedges.

    This function plots a circular colorbar representing the specified
    cyclic colormap. You can either provide:

    - An existing Axes (`ax`) in which to place the colorbar (the colorbar will
      be appended to one of its sides).
    - A dedicated Axes object (`cax`) for direct drawing of the colorbar
      on the specified `cax`.
    - Or no Axes at all, in which case a new figure and Axes are created.

    If both `ax` and `cax` are given, `ax` is ignored !.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        Colormap to use for the wedges.
    ax : matplotlib.axes.Axes or cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        The Axes to which the colorbar should be appended.
        Ignored if `cax` is provided.
        If both `ax` and `cax` are None, a new figure and Axes are created.
        If ax is specified and cax is None, arguments 'pad', 'size' and 'box_aspect'
        controls the appearance of the new axis.
    cax : matplotlib.axes.Axes, optional
        The Axes in which to directly draw the colorbar.
        If provided, `ax` is ignored.
    location : str, optional
        The side of the plot ('right', 'left', 'top', 'bottom') where the
        colorbar should be placed.  The default location is "right".
    size : str, optional
         The size of the colorbar relative to the parent Axes when using
        `append_axes`. For instance, `'30%'` means 30% of the parent Axes
        width (or height, depending on `location`).  The default value is `'30%'`.
    pad : float, optional
        Padding between the main axis and colorbar. The default value is 0.3.
    box_aspect : float, optional
        Aspect ratio of the colorbar box. The default value is 1.
    r_min : float, optional
        Inner radius of the colorbar. The default value is 0.2.
    r_max : float, optional
        Outer radius of the colorbar. The default value is 0.5.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5)
    zero_location : str, optional
        Starting location of the colorbar ('N', 'E', 'S', 'W').
        The default zero location is "N".
    clockwise : bool, optional
        Direction of rotation. If True, clockwise; if False, counterclockwise.
        The default value is True.
    adapt_limits: bool, optional
        If True, automatically adjusts the the limits of the plot to include the circle colorbar if
        center and r_min or r_max are changed.
        The default is True.
    antialiased : bool, optional
        Whether to antialias the wedges. The default is False.
    add_contour : bool, optional
        Whether to add contour circles. The default is True.
    contour_color : str, optional
        Color of the contour circles. The default color "black".
    contour_linewidth : float, optional
        Line width of the contour circles.
    wedges_edgecolor : str, optional
        Edge color of the wedges. The default is "none".
    wedges_linewidths : float, optional
        Line widths of the wedges.
    add_ticks : bool, optional
        Whether to add tick marks. The default is True.
    ticklength : float, optional
        Length of the tick mark. The default value is 0.02.
    tickcolor : str, optional
        Color of the tick mark. The default color is "black".
    tickwidth : float, optional
        Line width of the tick marks. The default value is 1.
    ticks : array-like, optional
        Positions of the ticks in radians.
    ticklabels : array-like, optional
        Labels for the ticks.
    ticklabels_pad : float, optional
        Radial offset for the tick labels. The default value is 0.05.
    ticklabels_size : int, optional
        Font size for the tick labels. The default value is 10.

    Returns
    -------
    matplotlib.collection.PatchCollection
    """
    # Initialize arguments
    # - theta_offset in degrees !
    zero_location_dict = {"N": -90, "E": 0, "S": 90, "W": -180}
    theta_offset = zero_location_dict[zero_location] if isinstance(zero_location, str) else zero_location - 90
    direction = -1 if clockwise else 1

    # Define n
    n = cmap.N

    # Determine colorbar axis
    if cax is not None:
        pass
    elif ax is not None:  # and cax is None
        divider = make_axes_locatable(ax)
        cax = divider.append_axes(location, size=size, pad=pad, axes_class=plt.Axes)
        cax.set_box_aspect(box_aspect)
    else:
        _, cax = plt.subplots()

    # Set equal axis ratio
    cax.set_aspect("equal")

    # Create list of wedges (annular patches)
    wedges = _create_wedges(
        r_min=r_min,
        r_max=r_max,
        n=n,
        center=center,
        theta_offset=theta_offset,
        direction=direction,
    )
    # Define values
    values = np.linspace(0, 1, n)

    # Create a patch collection with the color mapped to the values
    collection = PatchCollection(
        wedges,
        cmap=cmap,
        match_original=False,
        antialiased=antialiased,
        edgecolor=wedges_edgecolor,  # "none"
        linewidths=wedges_linewidths,
    )
    collection.set_array(values)

    # Add the collection to the axis
    cax.add_collection(collection)

    # Add custom ticks and labels
    if ticks is not None and ticklabels is not None:
        # Conversion of ticks from radians to degrees
        ticks = ticks / np.pi * 180

        # Add ticks labels
        _add_ticklabels(
            ax=cax,
            ticks=ticks,
            ticklabels=ticklabels,
            ticklabels_pad=ticklabels_pad,
            ticklabels_size=ticklabels_size,
            r_max=r_max,
            center=center,
            direction=direction,
            theta_offset=theta_offset,
        )
        # Add ticks line
        if add_ticks:
            _add_ticks(
                ax=cax,
                ticks=ticks,
                r_max=r_max,
                center=center,
                direction=direction,
                theta_offset=theta_offset,
                ticklength=ticklength,
                tickcolor=tickcolor,
                tickwidth=tickwidth,
            )
    # Add circle
    if add_contour:
        cax.add_patch(Circle(center, r_max, color=contour_color, lw=contour_linewidth, fill=False))
        cax.add_patch(Circle(center, r_min, color=contour_color, lw=contour_linewidth, fill=False))
    # Turn off axis
    cax.set_axis_off()
    # Adapt limits
    if adapt_limits:
        _set_adaptive_limits(ax=cax, r_max=r_max, center=center, margin_factor=0.1)
    # Return ax
    return collection


def plot_circular_colorbar_polar(
    cmap,
    *,
    # Location
    ax=None,
    cax=None,
    location="right",
    size="30%",
    pad=0.3,
    # Appearance
    r_min=0.8,
    r_max=1,
    antialiased=False,
    # Orientation
    clockwise=True,
    zero_location="N",
    # Contours
    add_contour=True,
    contour_color="black",
    contour_linewidth=None,
    # Ticklabels options
    ticks=None,
    ticklabels=None,
    ticklabels_pad=4,
    ticklabels_size=10,
):
    """
    Plot a circular colorbar on a polar projection.

    This function plots a circular colorbar representing the specified
    cyclic colormap using pcolormesh in a polar projection Axes.
    With this approach, it is not possible to add tick lines with this function !

    You can either provide:

    - An existing Axes (`ax`) in which to place the colorbar (the colorbar will
      be appended to one of its sides).
    - A dedicated Axes object (`cax`) for direct drawing of the colorbar
      on the specified `cax`.
    - Or no Axes at all, in which case a new figure and Axes are created.

    If both `ax` and `cax` are given, `ax` is ignored !.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        Colormap to use for the wedges.
    ax : matplotlib.axes.Axes or cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        The Axes to which the colorbar should be appended.
        Ignored if `cax` is provided.
        If both `ax` and `cax` are None, a new figure and Axes are created.
        If ax is specified and cax is None, arguments 'pad', 'size' and 'box_aspect'
        controls the appearance of the new axis.
    cax : matplotlib.axes.Axes, optional
        The Axes in which to directly draw the colorbar.
        If provided, `ax` is ignored.
    location : str, optional
        The side of the plot ('right', 'left', 'top', 'bottom') where the
        colorbar should be placed.  The default location is "right".
    size : str, optional
         The size of the colorbar relative to the parent Axes when using
        `append_axes`. For instance, `'30%'` means 30% of the parent Axes
        width (or height, depending on `location`).  The default value is `'30%'`.
    pad : float, optional
        Padding between the main axis and colorbar. The default value is 0.3.
    r_min : float, optional
        Inner radius of the colorbar. The default value is 0.8.
    r_max : float, optional
        Outer radius of the colorbar. The default value is 1.
    zero_location : str, optional
        Starting location of the colorbar ('N', 'E', 'S', 'W').
        The default zero location is "N".
    clockwise : bool, optional
        Direction of rotation. If True, clockwise; if False, counterclockwise.
        The default value is True.
    antialiased : bool, optional
        Whether to antialias the mesh. The default is False.
    add_contour : bool, optional
        Whether to add contour circles. The default is True.
    contour_color : str, optional
        Color of the contour circles. The default color "black".
    contour_linewidth : float, optional
        Line width of the contour circles.
    ticks : array-like, optional
        Positions of the ticks in radians.
    ticklabels : array-like, optional
        Labels for the ticks.
    ticklabels_pad : float, optional
        Radial offset for the tick labels. The default value is 0.05.
    ticklabels_size : int, optional
        Font size for the tick labels. The default value is 10.

    Returns
    -------
    matplotlib.collections.QuadMesh

    """
    from pycolorbar.univariate import plot_circular_colormap

    # Determine colorbar axis
    if cax is not None:
        pass
    elif ax is not None:  # and cax is None
        divider = make_axes_locatable(ax)
        cax = divider.append_axes(location, size=size, pad=pad, axes_class=mpl.projections.polar.PolarAxes)
    else:
        cax = None  # New plot created in plot_circular_colormap

    # Draw circular colormap
    p = plot_circular_colormap(
        cmap=cmap,
        ax=cax,
        r_min=r_min,
        r_max=r_max,
        antialiased=antialiased,
        add_title=False,
        # Orientation
        clockwise=clockwise,
        zero_location=zero_location,
        # Contours
        add_contour=add_contour,
        contour_color=contour_color,
        contour_linewidth=contour_linewidth,
    )

    # Improve ticklabels of the colorbar
    p.axes.tick_params(pad=ticklabels_pad, labelsize=ticklabels_size)

    # Add ticks if necessary
    if ticks is not None and ticklabels is not None:
        p.axes.set_xticks(ticks, labels=ticklabels, fontsize=ticklabels_size)

    return p


####-----------------------------------------------------------------------------------


def plot_circular_colorbar(
    cmap,
    *,
    # Location
    ax=None,
    cax=None,
    location="right",
    size="30%",
    pad=0.3,
    box_aspect=1,
    # Approach
    use_wedges=True,
    r_min=0.2,
    r_max=0.5,
    antialiased=False,
    # Not available for method="polar"
    center=(0.5, 0.5),
    adapt_limits=True,
    wedges_edgecolor="none",
    wedges_linewidths=None,
    # Orientation
    zero_location="N",
    clockwise=True,
    # Contour
    add_contour=True,
    contour_color="black",
    contour_linewidth=None,
    # Ticks (not available for method="polar")
    add_ticks=True,
    ticklength=0.02,
    tickcolor="black",
    tickwidth=1,
    # Ticklabels
    ticks=None,
    ticklabels=None,
    ticklabels_pad=None,
    ticklabels_size=10,
):
    """
    Plot a circular colorbar either drawing wedges or a mesh in polar projection.

    You can either provide:

    - An existing Axes (`ax`) in which to place the colorbar (the colorbar will
      be appended to one of its sides).
    - A dedicated Axes object (`cax`) for direct drawing of the colorbar
      on the specified `cax`.
    - Or no Axes at all, in which case a new figure and Axes are created.

    If both `ax` and `cax` are given, `ax` is ignored !.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        Colormap to use for the wedges.
    ax : matplotlib.axes.Axes or cartopy.mpl.geoaxes.GeoAxesSubplot, optional
        The Axes to which the colorbar should be appended.
        Ignored if `cax` is provided.
        If both `ax` and `cax` are None, a new figure and Axes are created.
        If ax is specified and cax is None, arguments 'pad', 'size' and 'box_aspect'
        controls the appearance of the new axis.
    cax : matplotlib.axes.Axes, optional
        The Axes in which to directly draw the colorbar.
        If provided, `ax` is ignored.
    location : str, optional
        The side of the plot ('right', 'left', 'top', 'bottom') where the
        colorbar should be placed.  The default location is "right".
    size : str, optional
         The size of the colorbar relative to the parent Axes when using
        `append_axes`. For instance, `'30%'` means 30% of the parent Axes
        width (or height, depending on `location`).  The default value is `'30%'`.
    pad : float, optional
        Padding between the main axis and colorbar. The default value is 0.3.
    box_aspect : float, optional
        Aspect ratio of the colorbar box. The default value is 1.
    r_min, r_max : float, optional
        Inner and outer radius of the colorbar.
        If use_wedges=True, these define the annular wedge boundaries.
        If use_wedges=False,these define the radial range in the polar projection.
    center: tuple, optional
        The coordinate center (x,y) around which to draw the circular colorbar.
        The default is (0.5, 0.5). Only used if ``use_wedges=True``.
    zero_location : str, optional
        Starting location of the colorbar ('N', 'E', 'S', 'W').
        The default zero location is "N".
    clockwise : bool, optional
        Direction of rotation. If True, clockwise; if False, counterclockwise.
        The default value is True.
    adapt_limits: bool, optional
        If True, automatically adjusts the the limits of the plot to include the circle colorbar if
        center and r_min or r_max are changed.  Only used if ``use_wedges=True``.
        The default is True.
    antialiased : bool, optional
        Whether to antialias the wedges. The default is False.
    add_contour : bool, optional
        Whether to add contour circles. The default is True.
    contour_color : str, optional
        Color of the contour circles. The default color is "black".
    contour_linewidth : float, optional
        Line width of the contour circles.
    wedges_edgecolor : str, optional
        Edge color of the wedges. The default is "none".
        Only used if ``use_wedges=True``.
    wedges_linewidths : float, optional
        Line widths of the wedges.
        Only used if ``use_wedges=True``.
    add_ticks : bool, optional
        Whether to add tick marks. The default is True.
        Only used if ``use_wedges=True``.
    ticklength : float, optional
        Length of the tick marks. The default value is 0.02.
        Only used if ``use_wedges=True``.
    tickcolor : str, optional
        Color of the tick marks. The default color is "black".
        Only used if ``use_wedges=True``.
    tickwidth : float, optional
        Line width of the tick marks. The default value is 1.
        Only used if ``use_wedges=True``.
    ticks : array-like, optional
        Positions of the ticks in radians.
    ticklabels : array-like, optional
        Labels for the ticks.
    ticklabels_pad : float, optional
        Radial offset for the tick labels. The default value is 0.05.
    ticklabels_size : int, optional
        Font size for the tick labels. The default value is 10.

    Returns
    -------
    matplotlib.collection.PatchCollection or matplotlib.collection.Quadmesh
    """
    # ------------------------------------------------
    # Accept LinearSegmentedColormap
    if not hasattr(cmap, "N"):
        cmap = cmap.resampled(256)

    # ------------------------------------------------
    # Call colorbar method
    if use_wedges:
        ticklabels_pad = 0.05 if ticklabels_pad is None else ticklabels_pad
        r_min = 0.2 if r_min is None else r_min
        r_max = 0.5 if r_max is None else r_max
        p = plot_circular_colorbar_wedges(
            cmap=cmap,
            # Location
            ax=ax,
            cax=cax,
            location=location,
            size=size,
            pad=pad,
            box_aspect=box_aspect,
            # Appearance
            r_min=r_min,
            r_max=r_max,
            antialiased=antialiased,
            # Not available for method="polar"
            center=center,
            adapt_limits=adapt_limits,
            wedges_edgecolor=wedges_edgecolor,
            wedges_linewidths=wedges_linewidths,
            # Orientation
            clockwise=clockwise,
            zero_location=zero_location,
            # Contour
            add_contour=add_contour,
            contour_color=contour_color,
            contour_linewidth=contour_linewidth,
            # Ticks (not available for method="polar")
            add_ticks=add_ticks,
            ticklength=ticklength,
            tickcolor=tickcolor,
            tickwidth=tickwidth,
            # Ticklabels
            ticks=ticks,
            ticklabels=ticklabels,
            ticklabels_pad=ticklabels_pad,
            ticklabels_size=ticklabels_size,
        )
        return p

    # ------------------------------------------------
    # Polar approach
    ticklabels_pad = 4 if ticklabels_pad is None else ticklabels_pad
    r_min = 0.8 if r_min is None else r_min
    r_max = 0.1 if r_max is None else r_max
    p = plot_circular_colorbar_polar(
        cmap=cmap,
        # Location
        ax=ax,
        cax=cax,
        location=location,
        size=size,
        pad=pad,
        # box_aspect = box_aspect, # unused
        # Appearance
        r_min=r_min,
        r_max=r_max,
        antialiased=antialiased,
        # Orientation
        clockwise=clockwise,
        zero_location=zero_location,
        # Contours
        add_contour=add_contour,
        contour_color=contour_color,
        contour_linewidth=contour_linewidth,
        # Ticklabels options
        ticks=ticks,
        ticklabels=ticklabels,
        ticklabels_pad=ticklabels_pad,
        ticklabels_size=ticklabels_size,
    )
    return p


####---------------------------------------------------------------------------------.


def add_circular_colorbar_legend(
    *,
    cmap,
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
    use_wedges=True,
    **kwargs,
):
    """
    Add the circular colorbar legend to a plot.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        The axes to which the colorbar legend will be added.
    cmap: matplotlib.colors.Colormap
        A cyclic matplotlib colormap.
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
    discrete: float, optional
        Whether to plot a discrete or continuous circular colorbar.
        If True (the default) call the plot_circular_colorbar_discrete function.
        Otherwise call the plot_circular_colorbar function
    **kwargs : dict
        Additional keyword arguments passed to the circular colorbar.
        See the plot_circular_colorbar documentation.

    Returns
    -------
    matplotlib.image.AxesImage
        The image object representing the circular colorbar.

    """
    # Define axis projection
    projection = None if use_wedges else "polar"

    # Define plot_circular_colorbar kwargs
    colorbar_func_kwargs = dict(
        cmap=cmap,
        use_wedges=use_wedges,
        **kwargs,
    )

    # Add colorbar inset
    p_cbar = add_colorbar_inset(
        ax=ax,
        colorbar_func=plot_circular_colorbar,
        colorbar_func_kwargs=colorbar_func_kwargs,
        # Inset options
        projection=projection,
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
