import math

import matplotlib.pyplot as plt
import numpy as np

from pycolorbar.univariate.cmap import get_cmap_colors, get_cmap_lab, get_cmap_lightness
from pycolorbar.univariate.cmap_cyclic import plot_circular_colormap


def _plot_colormaps_subplots(cmaps, plot_func, cols=None, subplot_size=None, subplot_kw=None, dpi=200, **plot_kwargs):
    """Plot a list of colormaps."""
    # Accept only a single colormap
    if not isinstance(cmaps, list):
        cmaps = [cmaps]

    # If a single colormap, plot with plot_colormap
    if len(cmaps) == 1:
        ax = plot_func(cmaps[0], **plot_kwargs)
        return ax.figure

    # Define subplot_size
    if subplot_size is None:
        subplot_size = (2, 0.5)

    # Define number of subplots
    n = len(cmaps)

    # Initialize subplot_kw
    # --> Required polar project for circular colormaps
    if subplot_kw is None:
        subplot_kw = {}

    # Define a layout most similar to a square
    if cols is None:
        cols = math.ceil(math.sqrt(n))
        cols = min(cols, 6)

    # Define number of rows required
    rows = int(np.ceil(n / cols))

    # Define figure width and height
    fig_width = cols * subplot_size[0]
    fig_height = rows * subplot_size[1]

    # Initialize figure
    fig, axes = plt.subplots(rows, cols, figsize=(fig_width, fig_height), dpi=dpi, subplot_kw=subplot_kw)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1, hspace=0.1, wspace=0.1)

    # Flatten axes for easy iteration
    axes = axes.ravel()

    # Loop through colormaps and axes
    for cmap, ax in zip(cmaps, axes[:n], strict=False):
        _ = plot_func(cmap=cmap, ax=ax, **plot_kwargs)

    # Turn off any remaining axes
    for ax in axes[n:]:
        ax.axis("off")
    return fig


####-------------------------------------------------------------------------------------------------------------------.
#### Univariate rectangular colormap


def _plot_colormap(cmap, ax):
    # mpl.colorbar.ColorbarBase(ax, cmap=cmap, orientation="horizontal")
    # ax.set_title(cmap.name, fontsize=10, weight="bold")

    # Create dummy image for colormap
    im = np.outer(np.ones(10), np.arange(100))
    ax.imshow(im, cmap=cmap)
    ax.set_title(cmap.name, fontsize=10, weight="bold")
    ax.axis("off")  # Set axis off
    return ax


def plot_colormap(cmap, dpi=200, ax=None, **plot_kwargs):
    """Plot a single colormap."""
    if ax is None:
        fig, ax = plt.subplots(figsize=(4, 0.4), dpi=dpi)
    ax = _plot_colormap(cmap=cmap, ax=ax, **plot_kwargs)
    plt.show()
    return fig


def plot_colormaps(cmaps, cols=None, subplot_size=None, dpi=200, **plot_kwargs):
    """Plot a list of colormaps."""
    # Define subplot_size
    if subplot_size is None:
        subplot_size = (2, 0.5)
    # Plot colormaps
    _ = _plot_colormaps_subplots(
        cmaps=cmaps,
        plot_func=_plot_colormap,
        cols=cols,
        subplot_size=subplot_size,
        dpi=dpi,
        **plot_kwargs,
    )
    plt.show()


####-------------------------------------------------------------------------------------------------------------------.
#### Univariate circular colormap


def plot_circular_colormaps(
    cmaps,
    # Subplots options
    cols=None,
    subplot_size=None,
    dpi=200,
    # Options for sine ramp of Kovesi
    n_cycles=0,  # 50
    amplitude=np.pi / 5,
    power=4,
    **plot_kwargs,
):
    """Plot a list of colormaps."""
    # Define project
    subplot_kw = {"projection": "polar"}
    # Define subplot_size
    if subplot_size is None:
        subplot_size = (2, 2)
    # Plot colormaps
    fig = _plot_colormaps_subplots(
        cmaps=cmaps,
        plot_func=plot_circular_colormap,
        cols=cols,
        subplot_size=subplot_size,
        subplot_kw=subplot_kw,
        dpi=dpi,
        # Options for sine ramp of Kovesi
        n_cycles=n_cycles,
        amplitude=amplitude,
        power=power,
        **plot_kwargs,
    )
    fig.tight_layout()
    plt.show()


####-------------------------------------------------------------------------------------------------------------------.
#### Diagnostics


def plot_lightness(cmap, ax=None, difference=False, labelsize=6, ticksize=6, s=2, **plot_kwargs):
    """
    Plot the lightness values of a colormap.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The colormap instance (e.g., LinearSegmentedColormap or ListedColormap) whose lightness will be plotted.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot the lightness. If None, a new figure and axes will be created.
    **plot_kwargs : keyword arguments
        Additional keyword arguments passed to `ax.scatter` (e.g., marker size, edge colors).

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes with the lightness plot.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 0.8), dpi=200)  # noqa: RUF059
    colors = get_cmap_colors(cmap)
    lightness = get_cmap_lightness(cmap)
    title = "Lightness"
    if difference:
        colors = colors[:-1]
        lightness = np.diff(lightness)
        title = "ΔL"
    x = np.linspace(0.0, 1.0, len(colors))
    ax.scatter(x, lightness, c=colors, s=s, **plot_kwargs)
    ax.set_ylabel(title, fontsize=labelsize)
    ax.set_xlim(0, 1)
    if not difference:
        ax.set_ylim(0, 100)
    ax.xaxis.set_visible(False)
    ax.tick_params(axis="y", labelsize=ticksize)
    ax.figure.tight_layout()
    return ax


def plot_rgb_components(cmap, ax=None, labelsize=6, ticksize=6, s=2, **plot_kwargs):
    """
    Plot the RGB components of a colormap.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The colormap instance (e.g., LinearSegmentedColormap or ListedColormap) whose RGB components will be plotted.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot the RGB components. If None, a new figure and axes will be created.
    labelsize : int, optional
        Font size for the labels. Default is 6.
    ticksize : int, optional
        Font size for the tick labels. Default is 6.
    s : int, optional
        Marker size for the scatter plot. Default is 2.
    **plot_kwargs : keyword arguments
        Additional keyword arguments passed to `ax.scatter` (e.g., marker size, edge colors).

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes with the RGB component plots.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 0.8), dpi=200)  # noqa: RUF059

    # Get RGB colors from colormap
    colors = get_cmap_colors(cmap)

    # Extract R, G, B components
    red = colors[:, 0]
    green = colors[:, 1]
    blue = colors[:, 2]

    # Generate x values for the plot
    x = np.linspace(0.0, 1.0, len(colors))

    # Plot each component with the corresponding color
    ax.plot(x, red, color="red", label="Red", s=s, **plot_kwargs)
    ax.plot(x, green, color="green", label="Green", s=s, **plot_kwargs)
    ax.plot(x, blue, color="blue", label="Blue", s=s, **plot_kwargs)

    # Set y-axis label and legend
    ax.set_ylabel("RGB", fontsize=labelsize)
    # ax.legend(fontsize=labelsize, loc='upper right')

    # Set y-axis limits (RGB values range from 0 to 1)
    ax.set_ylim(0, 1)
    ax.set_xlim(0, 1)

    # Turn off x-axis
    ax.xaxis.set_visible(False)

    # Set y-axis ticks with the specified size
    ax.tick_params(axis="y", labelsize=ticksize)

    # Adjust layout
    ax.figure.tight_layout()

    return ax


def plot_lab_components(cmap, ax=None, add_legend=True, labelsize=6, ticksize=6, s=2, **plot_kwargs):
    """Plot the LAB components of a colormap.

    Lightness (L*) is displayed on the left y-axis and A* and B* components on the right y-axis.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The colormap instance (e.g., LinearSegmentedColormap or ListedColormap) whose RGB components will be plotted.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot the LAB components. If None, a new figure and axes will be created.
    labelsize : int, optional
        Font size for the labels. Default is 6.
    ticksize : int, optional
        Font size for the tick labels. Default is 6.
    s : int, optional
        Marker size for the scatter plot. Default is 2.
    **plot_kwargs : keyword arguments
        Additional keyword arguments passed to `ax.scatter` (e.g., marker size, edge colors).

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes with the RGB component plots.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 0.8), dpi=200)  # noqa: RUF059

    # Get RGB colors from colormap
    lab = get_cmap_lab(cmap)

    # Extract L*, A*, and B* components
    L = lab[:, 0]  # Lightness
    A = lab[:, 1]  # A* (green-red axis)
    B = lab[:, 2]  # B* (blue-yellow axis)

    # Generate x values for the plot
    x = np.linspace(0.0, 1.0, len(L))

    # Plot the Lightness (L*) on the primary y-axis (left)
    ax.plot(x, L, color="black", label="Lightness (L*)", s=s, **plot_kwargs)
    ax.set_ylabel("L", fontsize=labelsize, color="black")
    ax.set_ylim(0, 100)  # Lightness typically ranges from 0 to 100

    # Set y-axis ticks and label size for Lightness
    ax.tick_params(axis="y", labelsize=ticksize, colors="black")

    # Create a secondary y-axis for A* and B* components
    ax_right = ax.twinx()
    ax_right.plot(x, A, color="green", label="A", s=s, **plot_kwargs)
    ax_right.plot(x, B, color="blue", label="B", s=s, **plot_kwargs)

    # Set y-axis limits for A* and B* (typical range for A* and B* is -128 to 128)
    ax_right.set_ylabel("A,B", fontsize=labelsize)
    ax_right.set_ylim(-128, 128)

    # Set y-axis ticks and label size for A* and B*
    ax_right.tick_params(axis="y", labelsize=ticksize)

    # Add a legend for the A* and B* components
    if add_legend:
        ax_right.legend(loc="lower right", fontsize=5, ncol=2)

    # Turn off x-axis labels and set axis limits
    ax.xaxis.set_visible(False)
    ax.set_xlim(0, 1)

    # Adjust layout
    ax.figure.tight_layout()

    return ax


def delta_e_cie2000(lab1, lab2):
    """
    Calculate the Delta E (CIEDE2000) color difference between two LAB colors.

    Parameters
    ----------
    lab1 : array-like, shape (3,)
        LAB color 1 in the format [L*, a*, b*].
    lab2 : array-like, shape (3,)
        LAB color 2 in the format [L*, a*, b*].

    Returns
    -------
    delta_e : float
        The Delta E (CIEDE2000) color difference between the two LAB colors.

    Notes
    -----
    This implementation follows the CIEDE2000 standard and is adapted from
    formulas described in Sharma et al. (2005).
    """
    # Constants
    kL = kC = kH = 1  # scaling factors

    L1, a1, b1 = lab1
    L2, a2, b2 = lab2

    # Mean values
    L_ = (L1 + L2) / 2.0
    C1 = np.sqrt(a1**2 + b1**2)
    C2 = np.sqrt(a2**2 + b2**2)
    C_ = (C1 + C2) / 2.0

    G = 0.5 * (1 - np.sqrt(C_**7 / (C_**7 + 25**7)))

    a1_ = (1 + G) * a1
    a2_ = (1 + G) * a2

    C1_ = np.sqrt(a1_**2 + b1**2)
    C2_ = np.sqrt(a2_**2 + b2**2)

    h1_ = np.degrees(np.arctan2(b1, a1_)) % 360
    h2_ = np.degrees(np.arctan2(b2, a2_)) % 360

    dL_ = L2 - L1
    dC_ = C2_ - C1_

    dh_ = h2_ - h1_
    if C1_ * C2_ == 0:
        dh_ = 0
    elif abs(dh_) > 180:
        dh_ -= np.sign(dh_) * 360

    dH_ = 2 * np.sqrt(C1_ * C2_) * np.sin(np.radians(dh_ / 2))

    L_50_sq = (L_ - 50) ** 2
    SL = 1 + (0.015 * L_50_sq) / np.sqrt(20 + L_50_sq)
    SC = 1 + 0.045 * C_
    T = (
        1
        - 0.17 * np.cos(np.radians(h1_ - 30))
        + 0.24 * np.cos(np.radians(2 * h1_))
        + 0.32 * np.cos(np.radians(3 * h1_ + 6))
        - 0.20 * np.cos(np.radians(4 * h1_ - 63))
    )
    SH = 1 + 0.015 * C_ * T

    dTheta = 30 * np.exp(-(((h1_ - 275) / 25) ** 2))
    RC = 2 * np.sqrt(C_**7 / (C_**7 + 25**7))
    RT = -RC * np.sin(np.radians(2 * dTheta))

    dE = np.sqrt(
        (dL_ / (kL * SL)) ** 2
        + (dC_ / (kC * SC)) ** 2
        + (dH_ / (kH * SH)) ** 2
        + RT * (dC_ / (kC * SC)) * (dH_ / (kH * SH)),
    )

    return dE


def plot_deltae(cmap, ax=None, accurate=True, labelsize=6, ticksize=6, s=2, **plot_kwargs):
    """Plot the Delta E (CIE76) values of a colormap.

    The Delta E represents the color difference between consecutive colors
    in the LAB color space.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The colormap instance (e.g., LinearSegmentedColormap or ListedColormap) whose color differences will be plotted.
    ax : matplotlib.axes.Axes, optional
        The axes on which to plot the Delta E values. If None, a new figure and axes will be created.
    accurate: bool
        If True, compute the Delta E (CIEDE2000). IF False, compute the Delta E (CIE76) which corresponds to the
        Euclidean distance in the CIELAB color space.
    labelsize : int, optional
        Font size for the labels. Default is 6.
    ticksize : int, optional
        Font size for the tick labels. Default is 6.
    s : int, optional
        Marker size for the scatter plot. Default is 2.
    **plot_kwargs : keyword arguments
        Additional keyword arguments passed to `ax.plot` (e.g., line style, marker).

    Returns
    -------
    ax : matplotlib.axes.Axes
        The axes with the Delta E plot.

    Notes
    -----
    - Delta E (ΔE) is a measure of color difference in LAB color space.
    - This function uses the CIE76 formula to compute ΔE between consecutive colors in the colormap.
    - Typical ΔE values:
        - 0-1: Imperceptible difference.
        - 1-2: Perceptible only to trained eyes.
        - 2-10: Perceptible to the human eye.
        - 10+: Large difference.

    Example
    -------
    >>> cmap = plt.get_cmap("viridis")
    >>> plot_deltae(cmap)
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(3, 0.8), dpi=200)  # noqa: RUF059

    # Get RGB colors from colormap
    lab = get_cmap_lab(cmap)

    # Compute deltaE
    if accurate:
        delta_e = np.array([delta_e_cie2000(lab[i], lab[i + 1]) for i in range(len(lab) - 1)])
    else:
        delta_e = np.linalg.norm(np.diff(lab, axis=0), axis=1)

    # Generate x values for the plot
    x = np.linspace(0.0, 1.0, len(delta_e))

    # Plot the Lightness (L*) on the primary y-axis (left)
    ax.plot(x, delta_e, color="black", label="Lightness (L*)", s=s, **plot_kwargs)
    ax.set_ylabel("ΔE", fontsize=labelsize, color="black")
    ax.set_ylim(0, None)

    # Set y-axis ticks and label size for Lightness
    ax.tick_params(axis="y", labelsize=ticksize, colors="black")

    # Turn off x-axis labels and set axis limits
    ax.xaxis.set_visible(False)
    ax.set_xlim(0, 1)

    # Adjust layout
    ax.figure.tight_layout()

    return ax


def plot_viscm_diagnostic(cmap):
    """Evaluate goodness of colormap using perceptual deltas."""
    try:
        from viscm import viscm
    except ImportError:
        raise ImportError(
            "The 'viscm' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge viscm",
        ) from None
    viscm(cmap)
    fig = plt.gcf()
    fig.set_size_inches(22, 10)
    plt.show()
