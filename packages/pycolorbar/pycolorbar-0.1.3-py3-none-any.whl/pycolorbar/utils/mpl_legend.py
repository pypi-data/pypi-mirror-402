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
"""Utility to add legends or insets to a Matplotlib figure."""
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.transforms import Bbox

# -----------------------------------------------------------------------------.
# NOTES
# How to rotate subplot by 45 degrees (not easy)
# - Create image, rotate, load image, attach to plot
# - https://stackoverflow.com/questions/62357483/how-to-rotate-a-subplot-by-45-degree-in-matplotlib


# Bbox([[xmin, ymin], [xmax, ymax]])
# Bbox.from_extents(xmin, ymin, xmax, ymax)
# Bbox.from_bounds(xmin, ymin, width, height)

# -----------------------------------------------------------------------------.


def get_locations_acronyms():
    """Get list of valid location acronyms."""
    locations = [
        "upper right",
        "upper left",
        "lower right",
        "lower left",
        "center left",
        "center right",
        "upper center",
        "lower center",
    ]
    return locations


def get_location_origin(loc, width, height, x_pad, y_pad):
    """Get the origin coordinates (x0, y0) for a given location on a plot.

    Parameters
    ----------
    loc : str
        The location string specifying the position. Accepted values are:
        'upper right', 'upper left', 'lower right', 'lower left',
        'center left', 'center right', 'upper center', 'lower center'.
    width : float
        The width of the element to be positioned.
    height : float
        The height of the element to be positioned.
    x_pad : float
        The horizontal padding from the specified location.
    y_pad : float
        The vertical padding from the specified location.

    Returns
    -------
    x0 : float
        The x-coordinate of the origin.
    y0 : float
        The y-coordinate of the origin.
    """
    # Define location mapping dictionary
    loc_mapping = {
        "upper right": (1 - width - x_pad, 1 - height - y_pad),
        "upper left": (0 + x_pad, 1 - height - y_pad),
        "lower right": (1 - width - x_pad, 0 + y_pad),
        "lower left": (0 + x_pad, 0 + y_pad),
        "center left": (0 + x_pad, 0.5 - height / 2 - y_pad),
        "center right": (1 - width - x_pad, 0.5 - height / 2 - y_pad),
        "upper center": (0.5 - width / 2 - x_pad, 1 - height / 2 - y_pad),
        "lower center": (0.5 - width / 2 - x_pad, 0 + y_pad),
    }
    valid_loc = list(loc_mapping)
    if loc not in loc_mapping:
        raise ValueError(f"Unsupported loc='{loc}'. Accepted 'loc' are {valid_loc}")

    # Define location x0, y0
    x0, y0 = loc_mapping[loc]
    return x0, y0


def get_inset_bounds(
    ax,
    loc="upper right",
    inset_height=0.2,
    inside_figure=True,
    aspect_ratio=1,
    border_pad=0,
):
    """Calculate the bounds for an inset axes in a matplotlib figure.

    This function computes the normalized figure coordinates for placing an inset axes within a figure,
    based on the specified location, size, and whether the inset should be fully inside the figure bounds.
    It is designed to be used with matplotlib figures to facilitate the addition of insets (e.g., for maps
    or zoomed plots) at predefined positions.

    Parameters
    ----------
    loc : str or tuple
        The location of the inset within the figure. Valid options are ``'lower left'``, ``'lower right'``,
        ``'upper left'``, and ``'upper right'``. The default is ``'upper right'``.
        Alternatively you can specify a tuple with the (x0, y0) figure coordinates.
    inset_height : float
        The size of the inset height, specified as a fraction of the figure's height.
        For example, a value of 0.2 indicates that the inset's height will be 20% of the figure's height.
        The aspect ratio will govern the ``inset_width``.
    aspect_ratio : float, optional
        The desired width-to-height ratio of the inset figure.
        A value greater than 1 indicates an inset figure wider than it is tall,
        and a value less than 1 indicates an inset figure taller than it is wide.
        The default value is 1.0, indicating a square inset figure.
    inside_figure : bool, optional
        Determines whether the inset is constrained to be fully inside the figure bounds. If  ``True`` (default),
        the inset is placed fully within the figure. If ``False``, the inset can extend beyond the figure's edges,
        allowing for a half-outside placement.
        This argument is used only if 'loc' is specified as a string.
    border_pad: int, float or tuple
        The padding to apply on the x and y direction.
        If a single value is supplied, applies the same padding in both directions.
        This arguments is used only if 'loc' is specified as a string.

    Returns
    -------
    inset_bounds : list of float
        The calculated bounds of the inset, in the format ``[x0, y0, width, height]``, where ``x0`` and ``y0``
        are the normalized figure coordinates of the lower left corner of the inset, and ``width`` and
        ``height`` are the normalized width and height of the inset, respectively.

    """
    # Define border_pad as tuple (x,y)
    if isinstance(border_pad, (int, float)):
        border_pad = (border_pad, border_pad)

    # ----------------------------------------------------------------.
    # Get the bounding box of the parent axes in figure coordinates
    bbox = ax.get_position()
    parent_width = bbox.width
    parent_height = bbox.height

    # Compute the relative inset width and height
    # - Take into account possible different aspect ratios
    inset_height_abs = inset_height * parent_height
    inset_width_abs = inset_height_abs * aspect_ratio
    inset_width = inset_width_abs / parent_width

    # ----------------------------------------------------------------.
    # Get axis position Bbox
    # ax_bbox = ax.get_position() # get the original position

    # # Get figure width and height
    # fig_width, fig_height = ax.figure.get_size_inches()

    # # Define width and height in inches
    # ax_height_in_inches = fig_height * ax_bbox.height
    # # ax_width_in_inches = fig_width * ax_bbox.width

    # # Now compute the inset width and height in inches
    # new_ax_height_in_inches = ax_height_in_inches*inset_height
    # new_ax_width_in_inches = new_ax_height_in_inches * aspect_ratio

    # # Now convert to relative position
    # new_ax_width = new_ax_width_in_inches/fig_width
    # new_ax_height = new_ax_height_in_inches/fig_height

    # inset_width = new_ax_width
    # inset_height = new_ax_height

    # #----------------------------------------------------------------.
    # print("Width:", inset_width)
    # print("Height:", inset_height)

    # ----------------------------------------------------------------.
    # If loc specify (x0,y0) return the inset bounds
    if isinstance(loc, (list, tuple)) and len(loc) == 2:
        return [loc[0], loc[1], inset_width, inset_height]

    # Compute the inset x0, y0 coordinates based on loc string
    inset_x, inset_y = get_location_origin(
        loc=loc,
        width=inset_width,
        height=inset_height,
        x_pad=border_pad[0],
        y_pad=border_pad[1],
    )

    # Adjust for insets that are allowed to be half outside of the figure
    if not inside_figure:
        inset_x += inset_width / 2 * (-1 if loc.endswith("left") else 1)
        inset_y += inset_height / 2 * (-1 if loc.startswith("lower") else 1)

    return [inset_x, inset_y, inset_width, inset_height]


def get_tightbbox_position(ax):
    """Return the axis Bbox position in figure coordinates.

    This Bbox includes also the area with axis ticklabels, labels and the title.
    """
    fig = ax.figure

    # Force a draw so Matplotlib computes the correct positions.
    fig.canvas.draw_idle()  # or draw() if you're sure you won't change anything else

    # Get the tight bounding box in DISPLAY (pixel) coordinates
    # - get_tightbbox() includes the area with labels, tick labels, etc
    renderer = fig.canvas.get_renderer()
    bbox = ax.get_tightbbox(renderer=renderer)

    # Convert that Bbox to FIGURE coordinates (0..1 range).
    bbox_fig = bbox.transformed(fig.transFigure.inverted())
    return bbox_fig


def optimize_inset_position(ax, cax, pad=0):
    """Optimize the inset position to not touch the main plot region."""
    # Define border_pad as tuple (x,y)
    if isinstance(pad, (int, float)):
        pad = (pad, pad)

    # Retrieve axis positions
    ax_pos = ax.get_position(original=False)
    cax_pos = cax.get_position(original=False)
    cax_outer_pos = get_tightbbox_position(cax)

    # Compute margin required (if positive)
    left_margin = np.maximum(0, ax_pos.x0 - cax_outer_pos.x0 + pad[0])
    right_margin = np.maximum(0, cax_outer_pos.x1 - ax_pos.x1 + pad[0])
    upper_margin = np.maximum(0, cax_outer_pos.y1 - ax_pos.y1 + pad[1])
    bottom_margin = np.maximum(0, ax_pos.y0 - cax_outer_pos.y0 + pad[1])

    # If not possible to optimize, return current position
    if (left_margin > 0 and right_margin > 0) or (upper_margin > 0 and bottom_margin > 0):
        return cax_pos

    # Define new position
    new_pos = Bbox.from_extents(
        [
            cax_pos.x0 + left_margin - right_margin,
            cax_pos.y0 + bottom_margin - upper_margin,
            cax_pos.x1 + left_margin - right_margin,
            cax_pos.y1 + bottom_margin - upper_margin,
        ],
    )
    return new_pos


def add_fancybox(ax, bbox, fc="white", ec="none", lw=0.5, alpha=0.5, pad=0, shape="square", zorder=None):
    """Add fancy box.

    The bbox can be derived using get_tightbbox_position(ax_legend).
    """
    fancy_patch = mpatches.FancyBboxPatch(
        (bbox.x0, bbox.y0),
        width=bbox.width,
        height=bbox.height,
        boxstyle=f"{shape},pad={pad}",
        fc=fc,  # facecolor
        ec=ec,  # edgecolor
        lw=lw,  # linewidth
        alpha=alpha,
        transform=ax.figure.transFigure,  # so these coords are figure coords
        zorder=zorder,
        clip_on=False,
    )
    return ax.add_artist(fancy_patch)


def add_colorbar_inset(
    *,
    ax,
    colorbar_func,
    colorbar_func_kwargs,
    projection=None,
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
):
    """Helper function to add an inset Axes and plot a colorbar within it.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
        Parent Axes to which the inset will be added.
    colorbar_func : callable
        A function that takes `cax` and extra keyword arguments to plot
        the actual colorbar (e.g., `plot_bivariate_colorbar`).
    colorbar_func_kwargs : dict
        Extra kwargs passed directly to `colorbar_func`.
    projection : str or None, optional
        Projection type of the inset Axes, passed to `ax.inset_axes()`.
    box_aspect : float, optional
        Aspect ratio of the inset Axes. Default is 1.
    height : float, optional
        Height of the inset as a fraction of the main Axes. Default is 0.2.
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

    Returns
    -------
    matplotlib.image.AxesImage
        The image (or artist) returned by `colorbar_func`.
    """
    # Compute the bounds for the inset Axes
    cax_bounds = get_inset_bounds(
        ax=ax,
        loc=loc,
        inset_height=height,
        inside_figure=inside_figure,
        aspect_ratio=box_aspect,
        border_pad=pad,
    )

    # Create the inset Axes
    cax = ax.inset_axes(bounds=cax_bounds, projection=projection)  # [x0, y0, width, height]

    # Raise z-order so the colorbar is on top and fancybox behind
    fancybox_zorder = cax.get_zorder() + 1
    cax.set_zorder(cax.get_zorder() + 2)

    # Plot the colorbar in the inset
    p_cbar = colorbar_func(
        cax=cax,
        **colorbar_func_kwargs,
    )

    # Adjust Axes position to accommodate ticklabels
    if optimize_layout and inside_figure:
        # Set new position
        # - Since 'inset_axes' was used, cax has an AxesLocator
        # - We remove the AxesLocator so we can set manually
        new_cax_pos = optimize_inset_position(ax=ax, cax=cax, pad=pad)
        cax.set_axes_locator(None)
        cax.set_position(new_cax_pos)

    # Optionally add fancy box behind the inset
    if fancybox:
        fancy_bbox = get_tightbbox_position(cax)
        add_fancybox(
            ax=ax,
            bbox=fancy_bbox,
            fc=fancybox_fc,
            ec=fancybox_ec,
            lw=fancybox_lw,
            shape=fancybox_shape,
            alpha=fancybox_alpha,
            pad=fancybox_pad,
            zorder=fancybox_zorder,
        )

    return p_cbar


def resize_cax(cax, width_percent=None, height_percent=None, x_alignment="left", y_alignment="center"):
    """
    Resize a colorbar axis based on percentages with specified alignment.

    Parameters
    ----------
    cax : matplotlib.axes.Axes
        The colorbar axes to adjust
    width_percent : float or None
        If provided, new width as percentage of the original (e.g., 80 = 80% of original width)
    height_percent : float or None
        If provided, new height as percentage of the original (e.g., 90 = 90% of original height)
    x_alignment : str
        Horizontal alignment: 'left', 'center', or 'right'
    y_alignment : str
        Vertical alignment: 'bottom', 'center', or 'top'
    """
    # Get current position (relative to figure)
    pos = cax.get_position()

    # Store original dimensions
    orig_width = pos.width
    orig_height = pos.height
    orig_x0 = pos.x0
    orig_y0 = pos.y0

    # Calculate new dimensions
    new_width = orig_width * (width_percent / 100) if width_percent is not None else orig_width
    new_height = orig_height * (height_percent / 100) if height_percent is not None else orig_height

    # Calculate new x0 based on alignment
    if x_alignment == "left":
        new_x0 = orig_x0
    elif x_alignment == "center":
        new_x0 = orig_x0 + (orig_width - new_width) / 2
    elif x_alignment == "right":
        new_x0 = orig_x0 + (orig_width - new_width)
    else:
        raise ValueError("x_alignment must be 'left', 'center', or 'right'")

    # Calculate new y0 based on alignment
    if y_alignment == "bottom":
        new_y0 = orig_y0
    elif y_alignment == "center":
        new_y0 = orig_y0 + (orig_height - new_height) / 2
    elif y_alignment == "top":
        new_y0 = orig_y0 + (orig_height - new_height)
    else:
        raise ValueError("y_alignment must be 'bottom', 'center', or 'top'")

    # Apply new position
    new_pos = [new_x0, new_y0, new_width, new_height]
    cax.set_position(new_pos)

    return cax


def pad_cax(cax, pad_left=0, pad_right=0, pad_top=0, pad_bottom=0):
    """
    Add padding to a colorbar axis based on percentages of current dimensions.

    Parameters
    ----------
    cax : matplotlib.axes.Axes
        The colorbar axes to adjust
    pad_left, pad_right, pad_top, pad_bottom : float
        Padding values as percentage of the current dimension (e.g., 10 = 10% padding)
    """
    # Get current position
    pos = cax.get_position()

    # Calculate padding in figure coordinates
    left_pad = pos.width * (pad_left / 100)
    right_pad = pos.width * (pad_right / 100)
    top_pad = pos.height * (pad_top / 100)
    bottom_pad = pos.height * (pad_bottom / 100)

    # Calculate new dimensions
    new_width = pos.width - left_pad - right_pad
    new_height = pos.height - top_pad - bottom_pad

    # Calculate new position
    new_x0 = pos.x0 + left_pad
    new_y0 = pos.y0 + bottom_pad

    # Apply new position
    new_pos = [new_x0, new_y0, new_width, new_height]
    cax.set_position(new_pos)

    return cax
