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
"""Define the register of univiariate colorbars."""

import os

import numpy as np

from pycolorbar.settings.categories import check_category_list, get_aux_category
from pycolorbar.settings.colorbar_io import read_cbar_dicts, write_cbar_dicts
from pycolorbar.settings.colorbar_validator import validate_cbar_dict
from pycolorbar.utils.yaml import list_yaml_files


class ColorbarRegistry:
    """
    A singleton class to manage colorbar registrations.

    This class provides methods to register colorbars settings, add new one on-the-fly,
    and to remove them.

    Attributes
    ----------
    _instance : ColorbarRegistry
        The singleton instance of the `ColorbarRegistry`.
    registry : dict
        The dictionary holding the registered colorbar settings.
    """

    _instance = None

    def __new__(cls):
        """Create a new instance of the ColorbarRegistry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            #  cls._instance = super(ColorbarRegistry, cls).__new__(cls)
            cls._instance.registry = {}
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Return the singleton instance of the ColorbarRegistry."""
        if cls._instance is None:
            cls()  # this will call __new__
        return cls._instance

    def reset(self):
        """Clears the entire Colorbar registry."""
        self.registry.clear()

    @property
    def names(self):
        """List the names of all registered colorbars settings."""
        return sorted(self.registry)

    def __contains__(self, item):
        """Test registration of a colorbar in the registry."""
        return item in self.names

    def _check_if_cbar_in_use(self, name, force, verbose):
        """Check if a colorbar is already registered and if it can be overwritten."""
        if name in self.registry:
            if force and verbose:
                print(f"Warning: Overwriting existing colorbar '{name}'")
            if not force:
                raise ValueError(
                    f"A colorbar setting named '{name}' already exists. To allow overwriting, set 'force=True'.",
                )

    def register(self, filepath: str, verbose: bool = True, force: bool = True, validate=False):
        """
        Register colorbar(s) configuration(s) defined in a YAML file.

        Parameters
        ----------
        filepath : str
            The YAML file path where the colorbar(s) settings are specified.
            A single YAML file can contain the configuration of multiple colorbars !
            The name of the YAML files it's not used !
        force : bool, optional
            If `True`, it allow to overwrites existing colorbar settings. The default is `True`.
            If `False`, it raise an error if attempting to overwrite an existing colorbar.
        verbose : bool, optional
            If `True`, the method will print a warning when overwriting existing colorbars. The default is `True`.
        validate: bool, optional
            Whether to validate the colorbar configuration file before registering.
            The default is `False`.

        Notes
        -----
        If a a colorbar configuration with the same name already exists, it will be overwritten.
        The validity of the colorbar(s) configuration(s) is not validated at registration !
        Use `pycolorbar.colorbars.validate()` to validate the registered colorbars.
        """
        # Check file exists
        if not os.path.isfile(filepath):
            raise ValueError(f"The colorbars configuration YAML file {filepath} does not exist.")
        # Read colorbars settings
        cbar_dicts = read_cbar_dicts(filepath=filepath)
        # Register colorbars settings
        for name, cbar_dict in cbar_dicts.items():
            if validate:
                cbar_dict = validate_cbar_dict(cbar_dict=cbar_dict, name=name)  # noqa
            self._check_if_cbar_in_use(name=name, force=force, verbose=verbose)
            self.registry[name] = cbar_dict

    def add_cbar_dict(self, cbar_dict: dict, name: str, verbose: bool = True, force: bool = True):
        """
        Add a colorbar configuration to the registry by providing a colorbar dictionary.

        Parameters
        ----------
        cbar_dict : dict
            The colorbar dictionary containing the colorbar's configuration.
        name : str
            The name of the colorbar.
        verbose : bool, optional
            If `True`, the method will print a warning when overwriting an existing colorbar. The default is `True`.
        force : bool, optional
            If `True`, it allow to overwrites existing colorbar settings. The default is `True`.
            If `False`, it raise an error if attempting to overwrite an existing colorbar.

        Notes
        -----
        If a colorbar with the same name already exists, it will be overwritten.
        The configuration is validated when adding a colorbar configuration with this method !
        """
        # Check if the name is already used
        self._check_if_cbar_in_use(name=name, force=force, verbose=verbose)
        # Validate cbar_dict
        cbar_dict = validate_cbar_dict(cbar_dict, name=name)
        # Update registry
        self.registry[name] = cbar_dict

    def unregister(self, name: str):
        """
        Remove a specific colorbar configuration from the registry.

        Parameters
        ----------
        name : str
            The name of the colorbar's configuration to remove.

        Raises
        ------
        ValueError
            If the colorbar with the specified name is not registered.
        """
        if name in self.registry:
            _ = self.registry.pop(name)
        else:
            raise ValueError(f"The colorbar configuration for {name} is not registered in pycolorbar.")

    def get_cbar_dict(self, name: str, resolve_reference=True, validate=True):
        """
        Retrieve the colorbar dictionary of a registered colorbar.

        Parameters
        ----------
        name : str
            The name of the colorbar.
        resolve_reference: bool
            Determines the behavior when the colorbar dictionary contains the `'reference'` keyword.
            If `True`, the function resolves the reference by returning the actual colorbar dictionary
            that the reference points to.
            If `False`, the function returns the original colorbar dictionary, including the `'reference'` keyword.
            The default is `True`.
        validate: bool
            Whether to validate the colorbar dictionary.
            The default is `True`.

        Returns
        -------
        dict
            The validated colorbar dictionary.

        Raises
        ------
        ValueError
            If the colorbar configuration is not registered.
        """
        if name not in self.registry:
            raise ValueError(f"The colorbar configuration for {name} is not registered in pycolorbar.")
        cbar_dict = self.registry[name].copy()
        if validate:
            cbar_dict = validate_cbar_dict(cbar_dict, name=name, resolve_reference=resolve_reference)
        return cbar_dict

    def get_cmap(self, name):
        """
        Retrieve the colormap of a registered colorbar.

        Parameters
        ----------
        name : str
            The name of the colorbar.

        Returns
        -------
        matplotlib.colors.Colormap
            The matplotlib `Colormap`.

        Notes
        -----
        This function also sets the over/under and bad colors specified in the colorbar configuration.

        """
        from pycolorbar.settings.matplotlib_kwargs import get_cmap

        cbar_dict = self.get_cbar_dict(name=name, resolve_reference=True)
        return get_cmap(cbar_dict)

    def to_yaml(self, filepath, names=None, force=False, sort_keys=False):
        """Write the registered colorbars settings to a YAML file."""
        write_cbar_dicts(
            cbar_dicts=self.registry,
            filepath=filepath,
            names=names,
            force=force,
            sort_keys=sort_keys,
        )

    def validate(self, name: str | None = None):
        """
        Validate the registered colorbars. If a specific name is provided, only that colorbar is validated.

        Parameters
        ----------
        name : str, optional
            The name of a specific colorbar to validate. If `None`, all registered colorbars are validated.

        Raises
        ------
        ValueError
            If any of the validated colorbars have invalid configurations.

        Notes
        -----
        Invalid colorbar configurations are reported.
        """
        # TODO: allow for list of names ?
        names = [name] if isinstance(name, str) else self.names

        # Validate colorbars
        wrong_names = []
        for name in names:
            try:
                cbar_dict = self.get_cbar_dict(name, resolve_reference=False)
                _ = validate_cbar_dict(cbar_dict=cbar_dict, name=name)
            except Exception as e:
                wrong_names.append(name)
                print(f"{name} has an invalid configuration: {e}")
                print("")
        if wrong_names:
            raise ValueError(f"The {wrong_names} colorbars have invalid configurations.")

    def get_standalone_settings(self):
        """Return the colorbar settings names which are not a reference to another colorbar."""
        names = []
        for name in self.names:
            cbar_dict = self.get_cbar_dict(name, resolve_reference=False)
            if "reference" not in cbar_dict:
                names.append(name)
        return names

    def get_referenced_settings(self):
        """Return the colorbar settings names which a reference to another colorbar."""
        names = []
        for name in self.names:
            cbar_dict = self.get_cbar_dict(name, resolve_reference=False)
            if "reference" in cbar_dict:
                names.append(name)
        return names

    def _get_category_subset(self, category, candidates_names):
        """List subset of colorbars matching the specified category."""
        category = check_category_list(category)  # ensure upper case
        names = []
        for name in candidates_names:
            cbar_dict = self.get_cbar_dict(name, resolve_reference=True)
            aux_category = get_aux_category(cbar_dict)  # list of upper case strings
            if np.all(np.isin(category, aux_category)):  # intersection !
                names.append(name)
        return names

    def available(self, category=None, exclude_referenced=False):
        """List the name of available colorbars for a specific category."""
        names = self.get_standalone_settings() if exclude_referenced else self.names
        names = names if category is None else self._get_category_subset(category=category, candidates_names=names)
        return names

    def show_colorbar(self, name, user_plot_kwargs=None, user_cbar_kwargs=None, fig_size=(6, 1)):
        """Display a colorbar (updated with optional user arguments)."""
        from pycolorbar.settings.colorbar_visualization import plot_colorbar

        if user_cbar_kwargs is None:
            user_cbar_kwargs = {}
        if user_plot_kwargs is None:
            user_plot_kwargs = {}
        plot_kwargs, cbar_kwargs = self.get_plot_kwargs(
            name=name,
            user_plot_kwargs=user_plot_kwargs,
            user_cbar_kwargs=user_cbar_kwargs,
        )
        plot_colorbar(plot_kwargs=plot_kwargs, cbar_kwargs=cbar_kwargs, ax=None, subplot_size=fig_size)

    def show_colorbars(self, category=None, exclude_referenced=True, subplot_size=None):
        """Display available colorbars (optionally of a specific category)."""
        from pycolorbar.settings.colorbar_visualization import plot_colorbars

        # TODO: allow for names subset ?

        # Retrieve available (of a given category) colorbars settings
        names = self.available(category=category, exclude_referenced=exclude_referenced)
        if len(names) == 0:
            raise ValueError("No colorbars are yet registered in the pycolorbar ColorbarRegistry.")

        # If only 1 colormap registered, plot it with the other method
        if len(names) == 1:
            self.show_colorbar(name=names[0])
            return None

        # Display colorbars
        list_args = [[name, *list(self.get_plot_kwargs(name=name))] for name in names]
        fig = plot_colorbars(list_args, subplot_size=subplot_size)
        return fig

    def get_plot_kwargs(self, name=None, user_plot_kwargs=None, user_cbar_kwargs=None):
        """Get pycolorbar plot kwargs (updated with optional user arguments)."""
        from pycolorbar.settings.matplotlib_kwargs import (
            get_plot_cbar_kwargs,
            update_plot_cbar_kwargs,
        )

        if not isinstance(name, (str, type(None))):
            raise TypeError("Expecting the colorbar setting name.")

        try:
            cbar_dict = self.get_cbar_dict(name)
        except Exception:
            cbar_dict = {}

        # Retrieve defaults pycolorbar kwargs
        plot_kwargs, cbar_kwargs = get_plot_cbar_kwargs(cbar_dict)
        plot_kwargs, cbar_kwargs = update_plot_cbar_kwargs(
            default_plot_kwargs=plot_kwargs,
            default_cbar_kwargs=cbar_kwargs,
            user_plot_kwargs=user_plot_kwargs,
            user_cbar_kwargs=user_cbar_kwargs,
        )
        return plot_kwargs, cbar_kwargs


def register_colorbars(directory: str, verbose: bool = True, force: bool = True):
    """
    Register all colorbar YAML files present in the specified directory (if name=None).

    This function assumes that all YAML files present in the directory are
    valid pycolorbar colorbars configuration files.

    Parameters
    ----------
    directory : str
        The directory where colorbar YAML files are located.
    force : bool, optional
        If `True`, it allow to overwrites existing colorbar settings. The default is `True`.
        If `False`, it raise an error if attempting to overwrite an existing colorbar.
    verbose : bool, optional
        If `True`, the method will print a warning when overwriting existing colorbars. The default is `True`.

    Notes
    -----
    If a a colorbar configuration with the same name already exists and `force=True`, it will be overwritten.
    The validity of the colorbar(s) configuration(s) is not validated at registration !
    Use `pycolorbar.colorbars.validate()` to validate the registered colorbars.
    """
    # List the colorbar YAML files to register
    filepaths = list_yaml_files(directory)

    # Add colorbars to the ColorbarRegistry
    colorbars = ColorbarRegistry.get_instance()
    for filepath in filepaths:
        colorbars.register(filepath, force=force, verbose=verbose)


def register_colorbar(filepath: str, verbose: bool = True, force: bool = True):
    """
    Register a single colorbar YAML file.

    Parameters
    ----------
    filepath : str
        The file path where the colorbar's YAML file is located.
    force : bool, optional
        If `True`, it allow to overwrites existing colorbar settings. The default is `True`.
        If `False`, it raise an error if attempting to overwrite an existing colorbar.
    verbose : bool, optional
        If `True`, the method will print a warning when overwriting existing colorbars. The default is `True`.

    Raises
    ------
    ValueError
        If the specified colorbar YAML file is not available in the directory.

    Notes
    -----
    If a a colorbar configuration with the same name already exists and `force=True`, it will be overwritten.
    The validity of the colorbar(s) configuration(s) is not validated at registration !
    Use `pycolorbar.colorbars.validate()` to validate the registered colorbars.
    """
    colorbars = ColorbarRegistry.get_instance()
    colorbars.register(filepath, verbose=verbose, force=force)


def get_cbar_dict(name, resolve_reference=True):
    """
    Retrieve the validated colorbar dictionary of a registered colorbar.

    Parameters
    ----------
    name : str
        The name of the colorbar.
    resolve_reference: bool
        Determines the behavior when the colorbar dictionary contains the `'reference'` keyword.
        If `True`, the function resolves the reference by returning the
        actual colorbar dictionary that the reference points to.
        If `False`, the function returns the original colorbar dictionary, including the `'reference'` keyword.
        The default is `True`.

    Returns
    -------
    dict
        The validated colorbar dictionary.

    """
    colorbars = ColorbarRegistry.get_instance()
    return colorbars.get_cbar_dict(name, resolve_reference=resolve_reference)


def get_plot_kwargs(name=None, user_plot_kwargs=None, user_cbar_kwargs=None):
    """
    Get matplotlib, xarray and geopandas compatible plot and colorbar kwargs.

    Parameters
    ----------
    name : str, optional
        Name of the registered colorbar settings.
        The default is None.
    user_plot_kwargs : dict, optional
        User-specific plot_kwargs. Example arguments includes 'vmin', 'vmax', 'norm', 'cmap', 'levels'.
    user_cbar_kwargs : dict, optional
       User-specific cbar_kwargs. See :class:`matplotlib.colorbar.Colorbar` for more details.

    Returns
    -------
    tuple
        A tuple with the `plot_kwargs` and `cbar_kwargs` to pass to the plotting functions.

    Examples
    --------
    **xarray Example:**

    .. code-block:: python

        plot_kwargs, cbar_kwargs = get_plot_kwargs("my_variable_name")
        da.plot.imshow(**plot_kwargs, cbar_kwargs=cbar_kwargs)

    **matplotlib Example:**

    .. code-block:: python

        plt.imshow(**plot_kwargs)
        plt.colorbar(**cbar_kwargs)

    **geopandas Example:**

    .. code-block:: python

        gdf.plot(**plot_kwargs, legend=False)
        plt.colorbar(**cbar_kwargs)
    """
    colorbars = ColorbarRegistry.get_instance()
    return colorbars.get_plot_kwargs(name=name, user_plot_kwargs=user_plot_kwargs, user_cbar_kwargs=user_cbar_kwargs)


def available_colorbars(category=None, exclude_referenced=False):
    """
    Return a list with the name of registered colorbars settings.

    Parameters
    ----------
    category : str or list,  optional
        The name(s) of an optional category to subset the list of registered colorbars.
        In the colormap YAML file, the `auxiliary/category` field lists the relevant
        categories of the colorbar.
        If `None` (the default), returns all available colorbars.
    exclude_referenced : bool, optional
        If `True`, exclude from the list the registered colorbars that refers to another colorbar for the
        actual configuration. The default is `False`.

    Returns
    -------
    names : str
        List of registered colorbars.
    """
    colorbars = ColorbarRegistry.get_instance()
    return colorbars.available(category=category, exclude_referenced=exclude_referenced)
