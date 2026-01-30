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
"""Define categorical norms."""
import numpy as np
from matplotlib.colors import BoundaryNorm


def is_monotonically_increasing(x):
    """Check if a list of values is monotonically increasing."""
    x = np.asanyarray(x)
    return np.all(x[1:] > x[:-1])


def check_boundaries(boundaries, arg_name="boundaries"):
    """Check boundaries/levels validity."""
    if not isinstance(boundaries, (list, np.ndarray)):
        raise TypeError(f"'{arg_name}' should be a list or a numpy array.")
    boundaries = np.array(boundaries).tolist()
    if not all(isinstance(b, (int, float)) for b in boundaries):
        raise ValueError(f"'{arg_name}' must be a list of numbers.")
    if len(boundaries) < 3:
        raise ValueError(f"Expecting '{arg_name}' of at least size 3.")
    if not is_monotonically_increasing(boundaries):
        raise ValueError(f"'{arg_name}' must be monotonically increasing !")
    return boundaries


def check_categories(categories):
    """Check categories dictionary validity."""
    if not all(isinstance(key, int) for key in categories):
        raise ValueError("All 'categories' dictionary keys must be integers.")
    if not all(isinstance(key, str) for key in categories.values()):
        raise ValueError("All 'categories' dictionary values be strings.")
    if len(categories) < 2:
        raise ValueError("Expecting a 'categories' dictionary with at least 2 keys.")
    # Reorder dictionary by integer order
    categories = dict(sorted(categories.items()))
    return categories


def is_categorical_norm(norm):
    """Check if a norm is categorical."""
    return isinstance(norm, (BoundaryNorm, CategoryNorm, CategorizeNorm))


class CategoryNorm(BoundaryNorm):  # BoundaryNorm instance required my matplotlib !
    """Generate a colormap index based on a category dictionary.

    Similarly to `BoundaryNorm`, `CategoryNorm` maps values to integers
    instead of to the interval 0-1.
    """

    def __init__(self, categories):
        """Create a CategoryNorm instance.

        Parameters
        ----------
        categories : dict
            Dictionary specifying categories id (keys) and class labels (values).
            The keys must be integers.

        Notes
        -----
        Appropriate colorbar ticks and ticklabels can be retrieved from
        the `ticks` and `ticklabels` attributes.
        """
        # Check keys are integers, and values are strings
        categories = check_categories(categories)
        n_categories = len(categories)
        boundaries = list(categories.keys())
        boundaries = np.append(boundaries, boundaries[-1] + 1)
        super().__init__(boundaries=boundaries, ncolors=n_categories, clip=False)
        self.ticks = boundaries[:-1] + np.diff(boundaries) / 2
        self.ticklabels = np.array(list(categories.values()))


class CategorizeNorm(BoundaryNorm):  # BoundaryNorm instance required my matplotlib !
    """Generates a colormap index based on a set of intervals into which discretize a continuous variable.

    Similarly to `BoundaryNorm`, `CategorizeNorm` maps values to integers
    instead of to the interval 0-1.
    """

    def __init__(self, boundaries, labels):
        """Create a CategorizeNorm instance.

        Parameters
        ----------
        boundaries : list
            Set of intervals into which categorize the continuous variable.
        labels : list
            Name of the discretized intervals.

        Notes
        -----
        Appropriate colorbar ticks and ticklabels can be retrieved from
        the `ticks` and `ticklabels` attributes.
        """
        boundaries = check_boundaries(boundaries, arg_name="boundaries")
        n_categories = len(labels)
        expected_n = len(boundaries) - 1
        if n_categories != expected_n:
            raise ValueError(f"'labels' size must be {expected_n} given the size of 'boundaries'.")
        boundaries = np.array(boundaries)
        boundaries[-1] = boundaries[-1] + 1e-9  # add infinitesimal threshold to include last boundary value
        super().__init__(boundaries=boundaries, ncolors=n_categories, clip=False)
        self.ticks = boundaries[:-1] + np.diff(boundaries) / 2
        self.ticklabels = np.array(labels)
