"""pyligent package."""

from importlib.metadata import version as _dist_version

__all__ = ["__version__"]

# Use the distribution name from pyproject: [project].name = "pyligent"
__version__ = _dist_version("pyligent")
