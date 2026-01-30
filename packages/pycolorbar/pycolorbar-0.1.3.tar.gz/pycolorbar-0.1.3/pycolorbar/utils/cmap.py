import colorsys
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, ListedColormap

# Documentation
# - https://github.com/shaharkadmiel/cmaptools/blob/master/cmaptools/__init__.py
# - https://www.pygmt.org/dev/api/generated/pygmt.makecpt.html
# - https://docs.generic-mapping-tools.org/6.2/cookbook/cpts.html


def load_cpt(filepath):
    """
    Load a color palette table (CPT) from a file and convert it to a color dictionary.

    CPT files are used by the Generic Mapping Tools software and Matlab.

    Parameters
    ----------
    filepath : str
        The file path to the CPT file.

    Returns
    -------
    colorDict : dict
        A dictionary with normalized 'red', 'green', and 'blue' values.
        Each key holds a list of [x_norm, color_value, color_value] for interpolation.

    Notes
    -----
    The function supports both RGB and HSV color models. If HSV is used,
    it converts HSV to RGB. RGB values are normalized between 0 and 1.
    """
    try:
        with open(filepath) as f:
            lines = [line.strip() for line in f if not line.startswith("#")]  # Ignore comment lines
    except FileNotFoundError:
        print(f"File {filepath} not found")
        return None

    color_model = "RGB"
    x, r, g, b = [], [], [], []

    for line in lines:
        if line.startswith(("B", "F", "N")):  # Skip control point lines
            # B # COLOR_BACKGROUND
            # F # COLOR_FOREGROUND
            # N # COLOR_NAN
            continue

        values = list(map(float, line.split()))
        # First color stop
        x.append(values[0])
        r.append(values[1])
        g.append(values[2])
        b.append(values[3])
        # Second color stop
        x.append(values[4])
        r.append(values[5])
        g.append(values[6])
        b.append(values[7])

    # Convert HSV to RGB [0-1]
    if color_model == "HSV":
        r, g, b = zip(
            *[colorsys.hsv_to_rgb(rv / 360.0, gv, bv) for rv, gv, bv in zip(r, g, b, strict=False)],
            strict=False,
        )

    # Convert RGB [0-255] to RGB [0-1]
    if color_model == "RGB":
        r, g, b = np.array(r) / 255.0, np.array(g) / 255.0, np.array(b) / 255.0

    # Normalize x values to [0, 1]
    x = np.array(x)
    x_norm = (x - x[0]) / (x[-1] - x[0])

    # Build the color dictionary
    color_dict = {
        "red": [[x_norm[i], r[i], r[i]] for i in range(len(x))],
        "green": [[x_norm[i], g[i], g[i]] for i in range(len(x))],
        "blue": [[x_norm[i], b[i], b[i]] for i in range(len(x))],
    }
    return color_dict


def get_cmap_from_cpt(filepath):
    """
    Create a matplotlib.colors.Colormap from a color palette table (CPT) file.

    Parameters
    ----------
    filepath : str
        The file path to the CPT file.

    """
    name = os.path.basename(filepath).rsplit(".", maxsplit=1)[0]
    segmentdata = load_cpt(filepath)
    cmap = LinearSegmentedColormap(name=name, segmentdata=segmentdata)
    return cmap


def rgb_to_hex(rgb):
    """Convert RGB to hex."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def plot_colors(colors, name=""):
    """Plot a set of colors."""
    from pycolorbar.univariate import plot_colormap

    cmap = ListedColormap(colors=colors, name=name)
    plot_colormap(cmap)
    plt.show()


def get_colors_from_colorbar(
    image_path,
    N=10,
    skip_first=0,
    skip_last=None,
    orientation="vertical",
    plot_checker=False,
    plot_cmap=True,
):
    """Utility function to infer N equally spaced colors from the middle of a colorbar image.

    This routine is useful to attempt reproducing colormaps appearing in scientific visualizations.
    """
    from PIL import Image

    # Open the image
    img = Image.open(image_path)
    img = img.convert("RGB")  # Ensure the image is in RGB format

    # Convert the image to a NumPy array
    img_array = np.array(img)

    # Remove first/last pixels if asked
    if orientation == "vertical":
        img_array = img_array[slice(skip_first, skip_last), :, :]
    else:
        img_array = img_array[:, slice(skip_first, skip_last), :]

    # Get image dimensions
    height, width, _ = img_array.shape

    # Extract color line (based on orientation) and indices to sample
    if orientation == "vertical":
        middle_column = width // 2
        coords = np.linspace(0, height - 1, N).astype(int)
        img_line = img_array[:, middle_column]
    elif orientation == "horizontal":
        middle_row = height // 2
        coords = np.linspace(0, width - 1, N).astype(int)
        img_line = img_array[middle_row, :]
    else:
        raise ValueError("Invalid orientation. Choose 'vertical' or 'horizontal'.")

    if plot_checker:
        plot_colors(img_line[0:5] / 255, name="First five")
        plot_colors(img_line[-5:] / 255, name="Last five")
        plot_colors(img_line / 255, name="Full colors")

    # Convert RGB colors to HEX
    hex_colors_img = np.array([rgb_to_hex(color) for color in img_line])

    # Extract sample colors
    indices = np.unique(coords.astype(int))
    hex_colors_sampled = hex_colors_img[indices]

    if plot_cmap:
        plot_colors(hex_colors_sampled, name=f"{N}")

    # Get position from where sampled
    # coords_01 = np.linspace(0, 1, len(hex_colors_img))
    # is_sampled = np.isin(hex_colors_img, hex_colors_sampled)
    # idx_position = coords_01[np.isin(hex_colors_img, hex_colors_sampled)]
    return hex_colors_sampled.tolist()
