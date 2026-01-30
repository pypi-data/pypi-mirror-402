# Welcome to pycolorbar

|                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Deployment        | [![PyPI](https://badge.fury.io/py/pycolorbar.svg?style=flat)](https://pypi.org/project/pycolorbar/) [![Conda](https://img.shields.io/conda/vn/conda-forge/pycolorbar.svg?logo=conda-forge&logoColor=white&style=flat)](https://anaconda.org/conda-forge/pycolorbar)                                                                                                                                                                                                                                                                                                                                                                            |
| Activity          | [![PyPI Downloads](https://img.shields.io/pypi/dm/pycolorbar.svg?label=PyPI%20downloads&style=flat)](https://pypi.org/project/pycolorbar/) [![Conda Downloads](https://img.shields.io/conda/dn/conda-forge/pycolorbar.svg?label=Conda%20downloads&style=flat)](https://anaconda.org/conda-forge/pycolorbar)                                                                                                                                                                                                                                                                                                                                    |
| Python Versions   | [![Python Versions](https://img.shields.io/badge/Python-3.11%20%203.12%20%203.13%20%203.14-blue?style=flat)](https://www.python.org/downloads/)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Supported Systems | [![Linux](https://img.shields.io/github/actions/workflow/status/ghiggi/pycolorbar/.github/workflows/tests.yml?label=Linux&style=flat)](https://github.com/ghiggi/pycolorbar/actions/workflows/tests.yml) [![macOS](https://img.shields.io/github/actions/workflow/status/ghiggi/pycolorbar/.github/workflows/tests.yml?label=macOS&style=flat)](https://github.com/ghiggi/pycolorbar/actions/workflows/tests.yml) [![Windows](https://img.shields.io/github/actions/workflow/status/ghiggi/pycolorbar/.github/workflows/tests_windows.yml?label=Windows&style=flat)](https://github.com/ghiggi/pycolorbar/actions/workflows/tests_windows.yml) |
| Project Status    | [![Project Status](https://www.repostatus.org/badges/latest/active.svg?style=flat)](https://www.repostatus.org/#active)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| Build Status      | [![Tests](https://github.com/ghiggi/pycolorbar/actions/workflows/tests.yml/badge.svg?style=flat)](https://github.com/ghiggi/pycolorbar/actions/workflows/tests.yml) [![Lint](https://github.com/ghiggi/pycolorbar/actions/workflows/lint.yml/badge.svg?style=flat)](https://github.com/ghiggi/pycolorbar/actions/workflows/lint.yml) [![Docs](https://readthedocs.org/projects/pycolorbar/badge/?version=latest&style=flat)](https://pycolorbar.readthedocs.io/en/latest/)                                                                                                                                                                     |
| Linting           | [![Black](https://img.shields.io/badge/code%20style-black-000000.svg?style=flat)](https://github.com/psf/black) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat)](https://github.com/astral-sh/ruff) [![Codespell](https://img.shields.io/badge/Codespell-enabled-brightgreen?style=flat)](https://github.com/codespell-project/codespell)                                                                                                                                                                                                                  |
| Code Coverage     | [![Coveralls](https://coveralls.io/repos/github/ghiggi/pycolorbar/badge.svg?branch=main&style=flat)](https://coveralls.io/github/ghiggi/pycolorbar?branch=main) [![Codecov](https://codecov.io/gh/ghiggi/pycolorbar/branch/main/graph/badge.svg?style=flat)](https://codecov.io/gh/ghiggi/pycolorbar)                                                                                                                                                                                                                                                                                                                                          |
| Code Quality      | [![Codefactor](https://www.codefactor.io/repository/github/ghiggi/pycolorbar/badge?style=flat)](https://www.codefactor.io/repository/github/ghiggi/pycolorbar) [![Codacy](https://app.codacy.com/project/badge/Grade/bee842cb10004ad8bb9288256f2fc8af?style=flat)](https://app.codacy.com/gh/ghiggi/pycolorbar/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade) [![Codescene](https://codescene.io/projects/41870/status-badges/code-health?style=flat)](https://codescene.io/projects/41870)                                                                                                                |
| License           | [![License](https://img.shields.io/github/license/ghiggi/pycolorbar?style=flat)](https://github.com/ghiggi/pycolorbar/blob/main/LICENSE)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| Community         | [![Slack](https://img.shields.io/badge/Slack-pycolorbar-green.svg?logo=slack&style=flat)](https://join.slack.com/t/pycolorbar/shared_invite/zt-2bxdsywo3-368GbufPyb8vNJ1GC9aT3g) [![GitHub Discussions](https://img.shields.io/badge/GitHub-Discussions-green?logo=github&style=flat)](https://github.com/ghiggi/pycolorbar/discussions)                                                                                                                                                                                                                                                                                                       |
| Citation          | [![DOI](https://zenodo.org/badge/664671614.svg?style=flat)](https://doi.org/10.5281/zenodo.10613635)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |

[**Slack**](https://join.slack.com/t/pycolorbar/shared_invite/zt-2bxdsywo3-368GbufPyb8vNJ1GC9aT3g) | [**Docs**](https://pycolorbar.readthedocs.io/en/latest/)

pycolorbar offers a simple and intuitive interface to define, save, and load colormaps and colorbar configurations.
It is designed to be used in combination with matplotlib, but it can also be used with other libraries such as cartopy, xarray and geopandas.

Please read the software documentation available at [https://pycolorbar.readthedocs.io/en/latest/](https://pycolorbar.readthedocs.io/en/latest/) and try
out the [Jupyter Notebook Tutorials](https://github.com/ghiggi/pycolorbar/tree/main/tutorials)

## 🛠️ Installation

### pip

pycolorbar can be installed via [pip][pip_link] on Linux, Mac, and Windows.
On Windows you can install [WinPython][winpy_link] to get Python and pip
running.
Then, install the pycolorbar package by typing the following command in the command terminal:

```
pip install pycolorbar
```

To install the latest development version, see the
[documentation][dev_installation].

### conda

pycolorbar can be installed via [conda][conda_link] on Linux, Mac, and Windows.
Install the package by typing the following command in a command terminal:

```
conda install pycolorbar
```

In case conda forge is not set up for your system yet, see the easy to follow
instructions on [conda forge][conda_forge_link].

## 💭 Feedback and Contributing Guidelines

If you aim to contribute your data or discuss the future development of pycolorbar,
we highly suggest to join the [**Slack Workspace**](https://join.slack.com/t/pycolorbar/shared_invite/zt-2bxdsywo3-368GbufPyb8vNJ1GC9aT3g)

Feel free to also open a [GitHub Issue](https://github.com/ghiggi/pycolorbar/issues) or a [GitHub Discussion](https://github.com/ghiggi/pycolorbar/discussions) specific to your questions or ideas.

## Citation

If you are using pycolorbar in your publication please cite our Zenodo repository:

> Ghiggi Gionata. ghiggi/pycolorbar. Zenodo. [![<https://doi.org/10.5281/zenodo.10613635>](https://zenodo.org/badge/664671614.svg?style=flat)](https://doi.org/10.5281/zenodo.10613635)

If you want to cite a specific version, have a look at the [Zenodo site](https://doi.org/10.5281/zenodo.10613635).

## License

The content of this repository is released under the terms of the [MIT](LICENSE) license.

[conda_forge_link]: https://github.com/conda-forge/pycolorbar-feedstock#installing-pycolorbar
[conda_link]: https://docs.conda.io/en/latest/miniconda.html
[dev_installation]: https://pycolorbar.readthedocs.io/en/latest/installation.html#installation-for-contributors
[pip_link]: https://pypi.org/project/pycolorbars
[winpy_link]: https://winpython.github.io/
