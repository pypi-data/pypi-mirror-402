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
"""Color encoding and decoding functions."""
import numpy as np


class ColorEncoderDecoder:
    """Base Color Encoding-Decoding Class."""

    def __init__(self, external_data_range, internal_data_range, name):
        """Initialize a color encoder-decoder to convert color values between external and internal representations.

        Parameters
        ----------
        external_data_range : dict
            Dictionary specifying the data range for each channel in the external representation.
        internal_data_range : dict
            Dictionary specifying the data range for each channel in the internal representation.
        name : str
            The name of the color space.

        Raises
        ------
        ValueError
            If the keys of external_data_range and internal_data_range do not match.
        """
        if external_data_range.keys() != internal_data_range.keys():
            raise ValueError("The keys of external and internal data ranges must match.")

        self.external_data_range = external_data_range
        self.internal_data_range = internal_data_range
        self.decoding_functions = dict.fromkeys(self.external_data_range, self._default_decode)
        self.encoding_functions = dict.fromkeys(self.internal_data_range, self._default_encode)
        self.ndim = len(external_data_range)
        self.name = name

    def decode(self, colors):
        """
        Decode color values from external to internal representation.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.

        Returns
        -------
        numpy.ndarray
            Decoded color values in internal representation.
        """
        return np.array(
            [
                self.decoding_functions[channel](
                    val,
                    *self.external_data_range[channel],
                    *self.internal_data_range[channel],
                )
                for channel, val in zip(self.external_data_range.keys(), colors.T, strict=False)
            ],
        ).T

    def encode(self, colors):
        """
        Encode color values from internal to external representation.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.

        Returns
        -------
        numpy.ndarray
            Encoded color values in external representation.
        """
        return np.array(
            [
                self.encoding_functions[channel](
                    val,
                    *self.internal_data_range[channel],
                    *self.external_data_range[channel],
                )
                for channel, val in zip(self.internal_data_range.keys(), colors.T, strict=False)
            ],
        ).T

    def _default_decode(self, value, from_min, from_max, to_min, to_max):
        """Default decoding function (linear scaling)."""
        return ((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min

    def _default_encode(self, value, from_min, from_max, to_min, to_max):
        """Default encoding function (linear scaling)."""
        return ((value - from_min) / (from_max - from_min)) * (to_max - to_min) + to_min

    def check_colors(self, colors):
        """
        Check colors array dimension, size and type validity.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.

        Returns
        -------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.

        """
        if not isinstance(colors, np.ndarray):
            raise ValueError("The colors array must be a numpy 2-dimensional array.")

        # Check 2D array
        if colors.ndim != 2:
            raise ValueError("The colors array must be a 2-dimensional array.")

        # Check number of columns
        if colors.shape[1] != self.ndim:
            raise ValueError(f"The colors array in the {self.name} color space must have {self.ndim} columns.")

        # Check data type
        if not (np.issubdtype(colors.dtype, np.integer) or np.issubdtype(colors.dtype, np.floating)):
            raise ValueError("The colors array must have integer or floating type.")
        return colors

    def check_valid_internal_data_range(self, colors):
        """Check if the color values are within the internal data range for each channel.

        Raises an informative ValueError if a channel does not comply with the data range.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.

        Raises
        ------
        ValueError
            If any channel values are not within the internal data range.
        """
        colors = self.check_colors(colors)
        for idx, channel in enumerate(self.internal_data_range.keys()):
            channel_colors = colors[:, idx]
            min_val, max_val = self.internal_data_range[channel]
            if not ((min_val <= channel_colors) & (channel_colors <= max_val)).all():
                raise ValueError(
                    f"Channel '{channel}' values are not within the internal data range. "
                    f"Expected range ({min_val}, {max_val}), but got values outside this range.",
                )

    def check_valid_external_data_range(self, colors, strict=False):
        """
        Check if the color values are within the external data range for each channel.

        Raises an informative ValueError if a channel does not comply with the data range.
        If 'strict' is True, it ensures that not all values are within the internal data range.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.
        strict : bool, optional
            If True, performs a strict check to ensure that the values are within the external data range
            and not within the internal data range. Default is False.

        Raises
        ------
        ValueError
            If any channel values are not within the external data range or, if 'strict' is True,
            that not all channel values are also within the internal data range.
        """
        colors = self.check_colors(colors)
        for idx, channel in enumerate(self.external_data_range.keys()):
            channel_colors = colors[:, idx]
            min_val, max_val = self.external_data_range[channel]
            if not ((min_val <= channel_colors) & (channel_colors <= max_val)).all():
                raise ValueError(
                    f"Channel '{channel}' values are not within the external data range. "
                    f"Expected range ({min_val}, {max_val}), but got values outside this range.",
                )

            if strict:
                internal_min_val, internal_max_val = self.internal_data_range[channel]
                if ((internal_min_val <= channel_colors) & (channel_colors <= internal_max_val)).all():
                    raise ValueError(
                        f"All '{channel}' values are within the internal data range "
                        "while expecting external representation.",
                    )

    def is_within_internal_data_range(self, colors):
        """
        Check if the color values are within the internal data range for each channel.

        Parameters
        ----------
        colors : numpy.ndarray
            2D-Array with the columns representing the color space dimensions.

        Returns
        -------
        bool
            True if all channel values are within the internal data range, False otherwise.
        """
        colors = self.check_colors(colors)
        conditions = [
            np.logical_and(
                colors[:, idx] >= self.internal_data_range[channel][0],
                colors[:, idx] <= self.internal_data_range[channel][1],
            )
            for idx, channel in enumerate(self.internal_data_range.keys())
        ]
        return np.all(np.vstack(conditions))

    def is_within_external_data_range(self, colors, strict: bool = False):
        """
        Check if the color values of each channels are within the external data range.

        Optionally, perform a strict check to ensure that not all values are also within the internal data range.

        Parameters
        ----------
        colors : numpy.ndarray
            2D array where each column represents a channel in the color space.
        strict : bool, optional
            If True, performs a check to ensure that not all values are also within the internal data range.
            Default is False.

        Returns
        -------
        bool
            If strict=False, True if all channel values are within the external data range, False otherwise.
            If strict=True,  True if all channels values are within the external data range and
            not also all inside the internal data range, False otherwise.
        """
        colors = self.check_colors(colors)
        conditions = [
            np.logical_and(
                colors[:, idx] >= self.external_data_range[channel][0],
                colors[:, idx] <= self.external_data_range[channel][1],
            )
            for idx, channel in enumerate(self.external_data_range.keys())
        ]
        is_within = np.all(np.vstack(conditions))
        if not strict:
            return is_within
        return is_within and not self.is_within_internal_data_range(colors)


class RGBEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding RGB color values.

    This class handles the conversion between external and internal RGB color values.

    External data range: R (0-255), G (0-255), B (0-255)
    Internal data ranges: R (0-1), G (0-1), B (0-1)
    """

    def __init__(self):
        external_data_range = {"R": (0, 255), "G": (0, 255), "B": (0, 255)}
        internal_data_range = {"R": (0, 1), "G": (0, 1), "B": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="RGB")


class RGBAEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding RGBA color values.

    This class handles the conversion between external and internal RGB color values.

    External data range: R (0-255), G (0-255), B (0-255), A (0-100)
    Internal data ranges: R (0-1), G (0-1), B (0-1), A (0-1)
    """

    def __init__(self):
        external_data_range = {"R": (0, 255), "G": (0, 255), "B": (0, 255), "A": (0, 100)}
        internal_data_range = {"R": (0, 1), "G": (0, 1), "B": (0, 1), "A": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="RGBA")


class HSVEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding HSV (also called HSB) color values.

    This class handles the conversion between external and internal HSV color values.

    External data range: Hue (0-360), Saturation (0-100),  Value (0-100)
    Internal data range: Hue (0-2π),  Saturation (0-1),  Value (0-1)

    The Hue channel requires special handling for the conversion between degrees and radians.
    """

    def __init__(self):
        external_data_range = {"H": (0, 360), "S": (0, 100), "V": (0, 100)}
        internal_data_range = {"H": (0, 2 * np.pi), "S": (0, 1), "V": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="HSV")

        # Override default functions for the 'H' channel
        self.decoding_functions["H"] = self._hue_decode
        self.encoding_functions["H"] = self._hue_encode

    def _hue_decode(self, hue, from_min, from_max, to_min, to_max):  # noqa: ARG002
        """Custom decode function for Hue channel (from degrees to radians)."""
        return hue * (2 * np.pi) / 360  # Convert degrees to radians

    def _hue_encode(self, hue, from_min, from_max, to_min, to_max):  # noqa: ARG002
        """Custom encode function for Hue channel (from radians to degrees)."""
        return hue * 360 / (2 * np.pi)  # Convert radians to degrees


class HCLEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding HCL color values.

    The color space is also known as PolarLUV or cylindrical transformations of the CIELUV (CIELChuv)

    HCL rearrange the two CIELUV U and V chroma values into chroma (C) and hue (h).
    The CIELUV coordinate L* (luminance) remains unchanged.

    This class handles the conversion between external and internal HCL color values.

    External data range: Hue (0-255), Chroma (0-255), Luminance (0-255)
    Internal data range: Hue (0-1), Chroma (0-1), Luminance (0-1)

    """

    # TODO: check data_range and name
    def __init__(self):
        external_data_range = {"H": (0, 255), "C": (0, 255), "L": (0, 255)}
        internal_data_range = {"H": (0, 1), "C": (0, 1), "L": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="HCL")


class LCHEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding LCH color values.

    The color space is also known as PolarLAB or cylindrical transformations of the CIELAB (CIELChab)

    LCH rearrange the two CIELAB A and B chroma values into chroma (C) and hue (h).
    The CIELAB coordinate L* (luminance) remains unchanged.

    This class handles the conversion between external and internal LCh color values.

    External data range: Luminance (0-100), Chroma (0-200),  Hue (0-360)
    Internal data range: Luminance (0-1), Chroma (0-2),  Hue (0-2π)

    The Hue channel requires special handling for the conversion between degrees and radians.
    """

    # TODO: check data_range and name
    def __init__(self):
        external_data_range = {"L": (0, 100), "C": (0, 200), "H": (0, 360)}
        internal_data_range = {"L": (0, 1), "C": (0, 1), "H": (0, 2 * np.pi)}
        super().__init__(external_data_range, internal_data_range, name="LCH")

        # Override default functions for the 'H' channel
        self.decoding_functions["H"] = self._hue_decode
        self.encoding_functions["H"] = self._hue_encode

    def _hue_decode(self, hue, from_min, from_max, to_min, to_max):  # noqa: ARG002
        """Custom decode function for Hue channel (from degrees to radians)."""
        return hue * (2 * np.pi) / 360  # Convert degrees to radians

    def _hue_encode(self, hue, from_min, from_max, to_min, to_max):  # noqa: ARG002
        """Custom encode function for Hue channel (from radians to degrees)."""
        return hue * 360 / (2 * np.pi)  # Convert radians to degrees


class CIELUVEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding CIE LUV color values.

    This class handles the conversion between external and internal LUV color values.

    External data range: Luminance (0-100), U (-100,100),  V (-100, 100)
    Internal data range: Luminance (0-1),  U (-1,1),  V (-1,1)

    U* and V* can theoretically range from -100 to +100 but practical ranges are smaller.
    The u and v coordinates measure positions on green/red and blue/yellow axes.

    """

    def __init__(self):
        external_data_range = {"L": (0, 100), "U": (-100, 100), "V": (-100, 100)}
        internal_data_range = {"L": (0, 1), "U": (-1, 1), "V": (-1, 1)}
        super().__init__(external_data_range, internal_data_range, name="CIELUV")


class CIELABEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding CIE LAB color values.

    This class handles the conversion between external and internal CIELAB color values.

    External data range: Luminance (0-100), A (-128,127),  B (-128, 127)
    Internal data range: Luminance (0-1),  A (-1,1),  B (-1,1)

    Note: A and B can theoretically range from -128 to +127 but practical ranges are smaller.
    """

    def __init__(self):
        external_data_range = {"L": (0, 100), "A": (-128, 127), "B": (-128, 127)}
        internal_data_range = {"L": (0, 1), "A": (-1, 1), "B": (-1, 1)}  # TBD
        super().__init__(external_data_range, internal_data_range, name="CIELAB")


class CIEXYZEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding CIE XYZ color values.

    This class handles the conversion between external and internal CIE XYZ color values.

    External data range: X (0-100), Y (0-100),  Z (0-100)
    Internal data range: X (0-1), Y (0-1),  Z (0-1)

    """

    def __init__(self):
        external_data_range = {"X": (0, 100), "Y": (0, 100), "Z": (0, 100)}
        internal_data_range = {"X": (0, 1), "Y": (0, 1), "Z": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="CIEXYZ")


class CMYKEncoderDecoder(ColorEncoderDecoder):
    """
    A class for encoding and decoding CMYK color values.

    This class handles the conversion between external and internal CMYK color values.

    External data range: Cyan (0-100), Magenta (0-100), Yellow (0-100) Key/Black (0-100)
    Internal data range: Cyan (0-1), Magenta (0-1), Yellow (0-1) Key/Black (0-1)

    """

    def __init__(self):
        external_data_range = {"C": (0, 100), "M": (0, 100), "Y": (0, 100), "K": (0, 100)}
        internal_data_range = {"C": (0, 1), "M": (0, 1), "Y": (0, 1), "K": (0, 1)}
        super().__init__(external_data_range, internal_data_range, name="CMYK")


def _get_color_space_dict():
    return {
        "RGB": RGBEncoderDecoder,
        "RGBA": RGBAEncoderDecoder,
        "HSV": HSVEncoderDecoder,
        "LCH": LCHEncoderDecoder,
        "HCL": HCLEncoderDecoder,
        "CIELUV": CIELUVEncoderDecoder,
        "CIELAB": CIELABEncoderDecoder,
        "CIEXYZ": CIEXYZEncoderDecoder,
        "CMYK": CMYKEncoderDecoder,
    }


def get_color_space_class(color_space):
    """
    Retrieve the class associated with the specified color space.

    Parameters
    ----------
    color_space : str
        The name of the color space.
        Valid color spaces are `'RGB'`, `'RGBA'`, `'HSV'`, `'LCH'`, `'HCL'`,
        `'CIELUV'`, `'CIELAB'`, `'CIEXYZ'`, `'CMYK'`.

    Returns
    -------
    class
        The class corresponding to the specified color space.
    """
    class_dict = _get_color_space_dict()
    if color_space not in class_dict:
        raise ValueError(f"Color space '{color_space}' is not recognized.")
    return class_dict[color_space]


COLOR_SPACES = list(_get_color_space_dict())


def decode_colors(colors, color_space):
    """
    Decode colors from external to internal representation for the specified color space.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.

    Returns
    -------
    numpy.ndarray
        Decoded color values in internal representation.
    """
    colors = np.asanyarray(colors)
    color_space = color_space.upper()
    if color_space in COLOR_SPACES:
        color_class = get_color_space_class(color_space)
        return color_class().decode(colors)
    return colors


def encode_colors(colors, color_space):
    """
    Encode colors from internal to external representation for the specified color space.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.

    Returns
    -------
    numpy.ndarray
        Encoded color values in external representation.
    """
    colors = np.asanyarray(colors)
    color_space = color_space.upper()
    if color_space in COLOR_SPACES:
        color_class = get_color_space_class(color_space)
        return color_class().encode(colors)
    return colors


def is_within_internal_data_range(colors, color_space):
    """
    Check if the color values are within the internal data range for the specified color space.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.

    Returns
    -------
    bool
        True if all channel values are within the internal data range, False otherwise.
    """
    color_instance = get_color_space_class(color_space)()
    return color_instance.is_within_internal_data_range(colors)


def is_within_external_data_range(colors, color_space, strict=False):
    """
    Check if the color values are within the external data range for the specified color space.

    Optionally, perform a strict check to ensure that not all values are also within the internal data range.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.
    strict : bool, optional
        If True, performs a check to ensure that not all values are also within the internal data range.
        Default is False.

    Returns
    -------
    bool
        True if all channel values are within the external data range (and, if strict
        is True, not within the internal data range), False otherwise.
    """
    color_instance = get_color_space_class(color_space)()
    return color_instance.is_within_external_data_range(colors, strict=strict)


def check_valid_internal_data_range(colors, color_space):
    """
    Check if the color values are within the internal data range for the specified color space.

    Raises an informative ValueError if a channel does not comply with the data range.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.

    Raises
    ------
    ValueError
        If any channel values are not within the internal data range.
    """
    color_instance = get_color_space_class(color_space)()
    color_instance.check_valid_internal_data_range(colors)


def check_valid_external_data_range(colors, color_space, strict=False):
    """
    Check if the color values are within the external data range for each channel.

    Raises an informative ValueError if a channel does not comply with the data range.
    If 'strict' is True, it ensures that not all values are within the internal data range.

    Parameters
    ----------
    colors : numpy.ndarray
        2D array where each column represents a channel in the color space.
    color_space : str
        The name of the color space.
    strict : bool, optional
        If True, performs a strict check to ensure that the values are within the external data range
        and not within the internal data range. Default is False.

    Raises
    ------
    ValueError
        If any channel values are not within the external data range or, if 'strict' is True,
        that not all channel values are also within the internal data range.
    """
    color_instance = get_color_space_class(color_space)()
    color_instance.check_valid_external_data_range(colors, strict=strict)
