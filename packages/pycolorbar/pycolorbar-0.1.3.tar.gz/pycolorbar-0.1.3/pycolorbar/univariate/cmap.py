import numpy as np
from matplotlib.colors import Colormap, LinearSegmentedColormap, ListedColormap


def _subset_colors(colors, interval, n):
    """
    Subset a list of colors based on the provided interval and number of colors (n).

    Parameters
    ----------
    colors : array-like
        List of RGB or RGBA colors.
    interval : tuple
        A tuple of two float values between 0 and 1, indicating the fraction of the colormap to retain.
    n : int, optional
        Number of colors to return. If None, all colors in the specified interval are returned.

    Returns
    -------
    np.ndarray
        Subset of colors based on the interval and n.
    """
    # Check interval
    interval = check_interval(interval)
    # Define start and stop integer indices (inclusive)
    start = int(np.floor(interval[0] * len(colors)))
    stop = int(np.ceil(interval[1] * len(colors))) - 1
    # Define actual indices to use to retrieve <n> colors
    # - Act as cmap.resampled(n)
    if n is None:
        index = np.arange(start, stop + 1, dtype=int)
    else:
        index = np.array(np.rint(np.linspace(start, stop, num=n)), dtype=int)
    # Retrieve color list
    colors = np.array(colors)[index]
    return colors


def _create_new_cmap(colors, old_cmap, name=None):
    """
    Create a new colormap with the specified colors.

    Parameters
    ----------
    colors : array-like
        List of RGB or RGBA colors to define the new colormap.
    old_cmap : Colormap
        The original colormap to be adapted.
    name : str, optional
        Name for the new colormap. If None, the name of the original colormap is used.

    Returns
    -------
    Colormap
        A new colormap created using the provided colors.
    """
    if name is None:
        name = old_cmap.name
    if isinstance(old_cmap, ListedColormap):
        cmap = ListedColormap(name=name, colors=colors)
    else:
        cmap = LinearSegmentedColormap.from_list(name=name, colors=colors, N=len(colors))
    return cmap


def check_interval(interval):
    """
    Validate that the interval is within the range [0, 1].

    Parameters
    ----------
    interval : tuple or None
        A tuple of two float values between 0 and 1 representing the range of the colormap.
        If None, the interval is set to (0, 1).

    Returns
    -------
    tuple
        Validated interval.

    Raises
    ------
    ValueError
        If the interval is not within the range [0, 1] or if the first value is greater than or equal to the second.
    """
    if interval is None:
        interval = (0, 1)
    if not ((0 <= interval[0] <= 1) and (0 <= interval[1] <= 1)):
        raise ValueError(
            "The colormap 'interval' must have values between 0 and 1.",
        )
    if interval[0] >= interval[1]:
        raise ValueError("The first value of the interval must be less than the second.")
    return interval


def get_cmap_colors(cmap, *, interval=None, n=None, alpha=None, bias=1):
    """
    Retrieve a list of RGB colors from a colormap, optionally subsetting by an interval and number of colors (n).

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        A colormap instance (e.g., LinearSegmentedColormap or ListedColormap).
    interval : tuple of float, optional
        A tuple (start, end) with values between 0 and 1, representing the fraction of the colormap to retain.
        Defaults to the full colormap (0, 1).
    n : int, optional
        Number of colors to return. If None, the number of colors depends on the colormap (default: None).
    alpha : float, optional
        A transparency value to apply to the colors, where 0 is fully transparent and 1 is fully opaque.
        If `alpha` is None (the default), the original transparency of the colors is preserved.
        If provided, all colors will be updated to have the specified alpha value.
    bias : float, optional
        A factor that skews the distribution of colors in the colormap.
        A `bias` of 1 (default) results in no bias.
        Values less than 1 space the colors more widely at the high end of the color map.
        Values greater than 1 space the colors more widely at the lower end of the colormap.

    Returns
    -------
    np.ndarray
        A NumPy array of RGB colors extracted from the colormap.

    Notes
    -----
    - If the colormap is a LinearSegmentedColormap and does not have an `N` attribute, 256 colors are returned.
    - If `interval` is provided, only the specified range of the colormap will be returned.
    """
    # Get colors
    if hasattr(cmap, "N"):
        rgb_colors = cmap(np.linspace(0, 1, cmap.N) ** bias, alpha=alpha)
    else:
        rgb_colors = cmap(np.linspace(0, 1, 256) ** bias, alpha=alpha)[:, :3]
    # Subset colors if asked
    rgb_colors = _subset_colors(colors=rgb_colors, interval=interval, n=n)
    return rgb_colors


def get_cmap_segmentdata(cmap, n=None):
    """
    Retrieve the segment data of a colormap, or generate it if not present.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        A colormap instance (e.g., LinearSegmentedColormap or ListedColormap).
    n : int, optional
        The number of discrete points to sample from the colormap. If None, the colormap's `N` attribute is used.

    Returns
    -------
    dict
        A dictionary representing the colormap's segment data for red, green, and blue channels.
        Each entry in the dictionary corresponds to a list of (x, y0, y1) tuples, where:
        - `x` is the position (0 to 1) along the colormap.
        - `y0` is the color value to the left of `x`.
        - `y1` is the color value to the right of `x`.

    Notes
    -----
    - The segment data is used to create `LinearSegmentedColormap` objects.
    - If the colormap has a `_segmentdata` attribute, it is returned directly.
    - If the colormap is sampled using `n` points, this function constructs the segment data manually.

    """
    # Check if the colormap already has `_segmentdata` and return it
    if hasattr(cmap, "_segmentdata"):
        return cmap._segmentdata

    # If `n` is not provided, use the number of colors in the colormap
    if n is None:
        n = cmap.N

    # Sample `n` points from the colormap along the range [0, 1]
    x = np.linspace(0, 1, n)
    rgb = cmap(x)

    # Extract blue channel values at each sample point
    b3 = rgb[:, 2]  # Right-hand value of blue at sample point
    b2 = rgb[:, 2]  # Left-hand value of blue at sample point

    # Extract green channel values at each sample point
    g3 = rgb[:, 1]  # Right-hand value of green at sample point
    g2 = rgb[:, 1]  # Left-hand value of green at sample point

    # Extract red channel values at each sample point
    r3 = rgb[:, 0]  # Right-hand value of red at sample point
    r2 = rgb[:, 0]  # Left-hand value of red at sample point

    # Create lists of tuples for red, green, and blue segment data
    R = list(zip(x, r2, r3, strict=False))  # Red segment data
    G = list(zip(x, g2, g3, strict=False))  # Green segment data
    B = list(zip(x, b2, b3, strict=False))  # Blue segment data

    # Create a dictionary to store the segment data for each color channel
    k = ["red", "green", "blue"]
    segmentdata = dict(zip(k, [R, G, B], strict=False))

    return segmentdata


def get_cmap_lab(cmap):
    """
    Convert a colormap's RGB values into the CAM02-UCS color space.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    np.ndarray
        A NumPy array of LAB values corresponding to the colormap's colors in the CAM02-UCS color space.
        The LAB values represent Lightness (L) and color components (A, B) in a perceptually uniform space.

    Raises
    ------
    ImportError
        If the `colorspacious` package is not installed.

    Notes
    -----
    This function converts the RGB values of the input colormap into the CAM02-UCS color space, which is
    designed to provide perceptually uniform color information, meaning that equal distances in this color space
    correspond to equal perceptual differences. The conversion is done using the `colorspacious` package.

    The LAB values consist of:
    - L: Lightness
    - A and B: Unique color components

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib import cm
    >>> cmap = cm.viridis
    >>> lab = get_cmap_lab(cmap)
    >>> print(lab)
    """
    # Check if the colorspacious package is available
    try:
        from colorspacious import cspace_convert
    except ImportError:
        raise ImportError(
            "The 'colorspacious' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge colorspacious",
        ) from None
    # Get RGB colors
    rgb_colors = get_cmap_colors(cmap)[:, :3]
    # Convert RGB colors to CAM02 Uniform Color Space
    # LAB --> L(ightness) AB unique colors ..
    lab = cspace_convert(rgb_colors, "sRGB1", "CAM02-UCS")
    return lab


def get_cmap_lightness(cmap):
    """
    Extract the lightness component of a colormap using the CAM02-UCS color space.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    lightness : ndarray
        A 1D array of lightness values corresponding to the colors in the colormap.
        These values are derived from the CAM02-UCS color space's lightness (L) component.

    Raises
    ------
    ImportError
        If the `colorspacious` package is not installed, an error is raised.

    Notes
    -----
    The function converts the RGB values of the input colormap into the CAM02-UCS
    color space, which provides perceptually uniform color information. The lightness
    component (L) is then extracted and returned as a 1D array.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib import cm
    >>> cmap = cm.viridis
    >>> lightness = get_cmap_lightness(cmap)
    >>> print(lightness)
    """
    lab = get_cmap_lab(cmap)
    lightness = lab[:, 0]
    return lightness


def adapt_cmap(cmap, *, interval=None, n=None, alpha=None, bias=1):
    """
    Adapt a colormap by subsetting its colors and applying transparency, if specified.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The original colormap to adapt (e.g., LinearSegmentedColormap or ListedColormap).
    interval : tuple of float, optional
        A tuple (start, end) with values between 0 and 1, indicating the fraction of the colormap to use.
        Defaults to using the full colormap (0, 1).
    n : int, optional
        The number of colors to return. If None, the colormap is not resampled.
    alpha : float, optional
        A transparency value to apply to the colors, where 0 is fully transparent and 1 is fully opaque.
        If `alpha` is None (the default), the original transparency of the colors is preserved.
    bias : float, optional
        A factor that skews the distribution of colors in the colormap.
        A `bias` of 1 (default) results in no bias.
        Values less than 1 space the colors more widely at the high end of the color map.
        Values greater than 1 space the colors more widely at the lower end of the colormap.

    Returns
    -------
    matplotlib.colors.Colormap
        A new colormap that reflects the specified interval, n, alpha and bias values.

    Notes
    -----
    - The function creates a new colormap by extracting a subset of the colors from the original colormap.
    - The resulting colormap has the same name as the original, unless specified otherwise in the internal logic.
    """
    # Subset colormap (interval and n)
    colors = get_cmap_colors(cmap=cmap, interval=interval, n=n, alpha=alpha, bias=bias)
    # Create new colormap
    cmap = _create_new_cmap(colors=colors, old_cmap=cmap)
    return cmap


def infer_cmap_type(cmap):
    """
    Infer the type of a colormap based on its lightness values and color differences.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    str
        A string indicating the type of colormap:
        - 'misc' if the colormap does not fit other categories.
        - 'sequential' if lightness values always increase or decrease.
        - 'diverging' if the colormap has a central extreme with sequential sides.
        - 'cyclic' if the perceptual differences between colors indicate a repeating pattern.
        - 'isoluminant' if all lightness values are the same.

    Notes
    -----
    This function analyzes the lightness and color differences of the colormap
    to classify it into one of several categories: sequential, diverging, cyclic, or miscellaneous.
    It is adapted from the cmasher library's `get_cmap_type` function.
    """
    # Extract the LAB color values
    lab = get_cmap_lab(cmap)

    # Get lightness values of colormap
    lightness = lab[:, 0]  #  get_cmap_lightness(cmap)
    # Calculate the difference between consecutive lightness values
    lightness_diff = np.diff(lightness)

    # Determine the central indices for the lightness array
    n = len(lightness) - 1
    central_indices = [int(np.floor(n / 2)), int(np.ceil(n / 2))]

    # Calculate lightness differences for the left and right halves of the colormap
    lightness_diff_left = np.diff(lightness[: central_indices[0] + 1])
    lightness_diff_right = np.diff(lightness[central_indices[1] :])

    # Calculate the perceptual differences between the last two and first two colors
    # --> To test for cyclic colormap
    lab_endpoints = lab[[-2, -1, 0, 1]]
    deltas = np.sqrt(np.sum(np.diff(lab_endpoints, axis=0) ** 2, axis=-1))

    # ISOLUMINANT
    # - If all lightness values are the same, categorize as "iso"
    if np.allclose(lightness_diff, 0):
        return "isoluminant"

    # SEQUENTIAL
    # - If lightness values always increase or decrease
    if np.isclose(np.abs(np.sum(lightness_diff)), np.sum(np.abs(lightness_diff))):
        return "sequential"

    # DIVERGING
    # - If the lightness values have a central extreme and sequential sides, then it is diverging
    if np.isclose(np.abs(np.sum(lightness_diff_left)), np.sum(np.abs(lightness_diff_left))) and np.isclose(
        np.abs(np.sum(lightness_diff_right)),
        np.sum(np.abs(lightness_diff_right)),
    ):
        # If the perceptual difference between the last and first value is
        # comparable to the other perceptual differences, it is cyclic
        if np.all(np.abs(np.diff(deltas)) < deltas[::2]) and np.diff(deltas[::2]):
            return "cyclic"

        # Otherwise, it is a normal diverging colormap
        return "diverging"
    return "misc"


def is_sequential_cmap(cmap):
    """
    Check if the colormap is of type 'sequential'.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    bool
        True if the colormap is sequential, False otherwise.
    """
    return infer_cmap_type(cmap) == "sequential"


def is_diverging_cmap(cmap):
    """
    Check if the colormap is of type 'diverging'.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    bool
        True if the colormap is diverging, False otherwise.
    """
    return infer_cmap_type(cmap) == "diverging"


def is_isoluminant_cmap(cmap):
    """
    Check if the colormap is of type 'isoluminant'.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    bool
        True if the colormap is isoluminant, False otherwise.
    """
    return infer_cmap_type(cmap) == "isoluminant"


def is_cyclic_cmap(cmap):
    """
    Check if the colormap is of type 'cyclic'.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    bool
        True if the colormap is cyclic, False otherwise.
    """
    return infer_cmap_type(cmap) == "cyclic"


def get_cvd_cmap(cmap, *, cvd_type, severity=50):
    """
    Return a Matplotlib colormap emulating a specified color-vision deficiency (CVD).

    This function simulates how the colormap would appear to someone with a particular type of color-vision
    deficiency using the `colorspacious` package.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap to be converted.
        It can be an instance of either `ListedColormap` or `LinearSegmentedColormap`.
    cvd_type : str
        The type of color-vision deficiency to simulate. Valid options are:
        'deuteranomaly', 'protanomaly', and 'tritanomaly'.
    severity : int, optional
        The severity of the color-vision deficiency on a scale from 0 (no deficiency) to 100 (complete deficiency),
        by default 50. For people suffering of tritanomaly, only severity = 100 actually exists in reality.

    Returns
    -------
    matplotlib.colors.Colormap
        A new colormap that simulates the appearance of the input colormap for individuals with the specified
        color-vision deficiency.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib.colors import get_cmap
    >>> cmap = get_cmap("viridis")
    >>> cvd_cmap = get_cvd_cmap(cmap, cvd_type="deuteranomaly", severity=50)
    >>> plt.imshow([list(range(256))], cmap=cvd_cmap)
    >>> plt.show()

    Notes
    -----
    This function relies on the `colorspacious` package to perform color conversions.
    Make sure to install it using `conda install -c conda-forge colorspacious` if not already available.
    """
    # Check if the colorspacious package is available
    try:
        from colorspacious import cspace_convert
    except ImportError:
        raise ImportError(
            "The 'colorspacious' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge colorspacious",
        ) from None
    # Check valid CVD type
    valid_cvd_types = ["deuteranomaly", "protanomaly", "tritanomaly"]
    if cvd_type not in valid_cvd_types:
        raise ValueError(f"Invalid 'cvd_type' {cvd_type}. Valid values are: {valid_cvd_types}.")
    # Define CVD space
    cvd_space = {"name": "sRGB1+CVD", "cvd_type": cvd_type, "severity": severity}
    # Get RGB colors
    rgba_colors = get_cmap_colors(cmap)
    rgb_colors = rgba_colors[:, :3]  # discard alpha
    # Convert to CVD
    cvd_colors = cspace_convert(rgb_colors, cvd_space, "sRGB1")
    cvd_colors = np.clip(cvd_colors, 0, 1)
    # Add back the alpha (transparency) channel
    if rgba_colors.shape[1] == 4:
        cvd_colors = np.column_stack((cvd_colors, rgba_colors[:, 3]))
    # Create colormap
    cvd_cmap = _create_new_cmap(colors=cvd_colors, old_cmap=cmap)
    return cvd_cmap


def get_gray_cmap(cmap):
    """Convert a given colormap to its grayscale equivalent.

    Grayscale conversion is based on the lightness component of CAM02-UCS color space.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The input colormap, which can be a `ListedColormap` or a `LinearSegmentedColormap`.

    Returns
    -------
    cmap_gray : matplotlib.colors.Colormap
        The grayscale version of the input colormap, where the RGB values are
        set based on the lightness of the corresponding color in the CAM02-UCS
        color space. If the original colormap includes transparency (alpha),
        it is preserved.

    Raises
    ------
    ImportError
        If the `colorspacious` package is not installed, an error is raised.

    Notes
    -----
    This function uses the CAM02-UCS color space to convert the colors of the
    input colormap to grayscale based on their perceived lightness. The grayscale
    colors are created by setting the R, G, and B channels to the normalized
    lightness values. If the original colormap contains an alpha channel, it
    is maintained in the resulting grayscale colormap.

    Examples
    --------
    >>> import matplotlib.pyplot as plt
    >>> from matplotlib import cm
    >>> cmap = cm.viridis
    >>> cmap_gray = get_gray_cmap(cmap)
    >>> plt.imshow([[0, 1]], cmap=cmap_gray)
    >>> plt.show()
    """
    # Check if the colorspacious package is available
    try:
        from colorspacious import cspace_convert
    except ImportError:
        raise ImportError(
            "The 'colorspacious' package is required but not found. "
            "Please install it using the following command: "
            "conda install -c conda-forge colorspacious",
        ) from None
    # Get RGB colors
    rgba_colors = get_cmap_colors(cmap)
    rgb_colors = get_cmap_colors(cmap)[:, :3]
    # Convert RGB colors to CAM02 Uniform Color Space
    # LAB --> L(ightness) AB unique colors ..
    lab = cspace_convert(rgb_colors, "sRGB1", "CAM02-UCS")
    lightness = lab[:, 0]
    # Normalize lightness values
    lightness = lightness / 99.99871678
    # Create an RGB grayscale array (R=G=B=lightness)
    rgb_grayscale = np.stack([lightness] * 3, axis=-1)
    rgb_grayscale = np.clip(rgb_grayscale, 0, 1)
    # Add back the alpha (transparency) channel
    if rgba_colors.shape[1] == 4:
        rgb_grayscale = np.column_stack((rgb_grayscale, rgba_colors[:, 3]))
    # Create colormap
    cmap_gray = _create_new_cmap(colors=rgb_grayscale, old_cmap=cmap)
    return cmap_gray


def get_shifted_cmap(cmap):
    """
    Shift the colors of a cyclic colormap, centering the midpoint of the color range.

    This function is useful for cyclic colormaps, such as those representing
    angles or phases, where the start and end colors should seamlessly wrap around.
    The function shifts the colormap so that the midpoint of the color range becomes the new start.

    Parameters
    ----------
    cmap : matplotlib.colors.Colormap
        The original cyclic colormap to shift.

    Returns
    -------
    matplotlib.colors.Colormap
        A new colormap with its colors shifted so that the midpoint of the
        original colormap becomes the new starting point.

    Notes
    -----
    - This function is particularly useful for cyclic colormaps where symmetry or phase is important.
    - It works by dividing the colormap at its midpoint and swapping the two halves.
    """
    # Subset colormap
    colors = get_cmap_colors(cmap=cmap)
    # Determine the central value index of the colormap
    idx = len(colors) // 2
    # Shift the entire colormap by this index
    colors_shifted = np.r_[colors[idx:], colors[:idx]]
    # Create new colormap
    cmap = _create_new_cmap(colors=colors_shifted, old_cmap=cmap)
    return cmap


def _check_cmaps(cmaps, n):
    """Check and retrieve the specified colormaps, ensuring proper formatting.

    Parameters
    ----------
    cmaps : list of Colormap or str
        List of colormap instances or their names to be combined.
    ns : list of int or None
        List of integers specifying the number of colors for each colormap.
        If None, defaults to using the number of colors of the colormaps,
        or 256 colors for LinearSegmentedColormap defined by segmentdata.

    Raises
    ------
    ValueError
        If fewer than two colormaps are provided.

    Returns
    -------
    list of Colormap
        A list of Colormap instances, resampled if necessary.
    """
    import pycolorbar

    # Check colormap datatype and convert to list[Colormap]
    if len(cmaps) <= 1:
        raise ValueError("Expected at least two colormaps to combine.")
    # Check ns
    if n is None:
        n = [None] * len(cmaps)
    # Retrieve and resample cmap if necessary
    cmaps = [pycolorbar.get_cmap(cm, n=cm_n) for cm, cm_n in zip(cmaps, n, strict=False)]
    return cmaps


def _check_nodes(nodes, cmaps):
    """Validate and prepare node positions for colormap blending.

    Parameters
    ----------
    nodes : list or numpy.ndarray, optional
        List or array of float values indicating blending points.
        Nodes values should be one less than the number of colormaps.
    cmaps : list of Colormap
        List of colormaps being combined.

    Raises
    ------
    TypeError
        If the nodes are not of a supported type (list or ndarray).
    ValueError
        If the number of nodes does not match the expected count or if node values
        are out of bounds or not in increasing order.

    Returns
    -------
    numpy.ndarray
        An array of nodes including the starting (0.0) and ending (1.0) points.
    """
    # Generate default nodes for equal separation
    if nodes is None:
        nodes_arr = np.linspace(0, 1, len(cmaps) + 1)
    elif isinstance(nodes, list | np.ndarray):
        if len(nodes) != len(cmaps) - 1:
            raise ValueError("Number of nodes should be one less than the number of colormaps.")
        nodes_arr = np.concatenate([[0.0], nodes, [1.0]])
    else:
        raise TypeError(f"Unsupported nodes type: {type(nodes)}, expect list of float.")

    # Check node values
    if any((nodes_arr < 0) | (nodes_arr > 1)) or any(np.diff(nodes_arr) <= 0):
        raise ValueError(
            "Nodes should only contain increasing values between 0.0 and 1.0.",
        )
    return nodes_arr


def combine_cmaps(
    cmaps: list[Colormap | str],
    *,
    nodes: list[float] | np.ndarray | None = None,
    n=None,
    output_n: int = 256,
    name: str = "combined_cmap",
) -> LinearSegmentedColormap:
    """Create a composite matplotlib colormap by combining multiple colormaps.

    Parameters
    ----------
    cmaps : list
        List of matplotlib.Colormap or registered colormap names to be combined.
    nodes : list of float or np.ndarray, optional
        Blending points between colormaps, in the range [0, 1].
        Nodes values should be one less than the number of colormaps.
        Defaults to equal divisions if None.
    n : list of int or None, optional
        Number of colors for each colormap. Defaults to None, which uses the
        original number of colors for each colormap.
    output_n : int, optional
        Number of colors in the output colormap. Default is 256.
    name : str, optional
        Name for the combined colormap. Default is "combined_cmap".

    Returns
    -------
    LinearSegmentedColormap
        The composite colormap created from the specified colormaps.

    Raises
    ------
    TypeError
        If the list contains mixed datatypes or invalid colormap names.
    ValueError
        If the cmaps contain only one single colormap, or if the number of nodes
        is not one less than the number of colormaps, or if the nodes do not
        contain incrementing values between 0.0 and 1.0.

    Notes
    -----
    The colormaps are combined from low value to high value end.
    Code adapted from CMasher (https://github.com/1313e/CMasher).

    Examples
    --------
    Using predefined colormap names:

        custom_cmap_1 = combine_cmaps(
            ["ocean", "prism", "coolwarm"], nodes=[0.2, 0.75]
        )

    Using Colormap objects:

        cmap_0 = plt.get_cmap("Blues")
        cmap_1 = plt.get_cmap("Oranges")
        cmap_2 = plt.get_cmap("Greens")
        custom_cmap_2 = combine_cmaps([cmap_0, cmap_1, cmap_2])
    """
    # Check valid cmaps and resample cmap if ns is not None
    cmaps = _check_cmaps(cmaps, n=n)
    nodes_arr = _check_nodes(nodes, cmaps=cmaps)

    # Retrieve colors for each colormap
    cmap_segments = []
    for i, cmap in enumerate(cmaps):
        # Define positions
        start_position = nodes_arr[i]
        end_position = nodes_arr[i + 1]
        # Calculate the length of the segment
        segment_length = int(output_n * (end_position - start_position))
        # Append the segment to the combined colormap segments
        cmap_segments.append(cmap(np.linspace(0, 1, segment_length)))

    # Define new color palette
    colors = np.vstack(cmap_segments)

    # Define the new colormap by combining the segments
    cmap = LinearSegmentedColormap.from_list(
        name=name,
        colors=colors,
        N=output_n,
    )
    return cmap
