# hurdat2py/__init__.py
from importlib.metadata import version, PackageNotFoundError

# Expose the main entry point
from .core import Hurdat2

# Expose the data objects
from .objects import TropicalCyclone, Season, Hurdat2Entry

# Expose errors
from .errors import (
    Hurdat2Error, 
    StormNotFoundError, 
    DataDownloadError, 
    DataParseError
)

# Fetch version dynamically from pyproject.toml metadata
try:
    __version__ = version("hurdat2py")
except PackageNotFoundError:
    # If the package is not installed (e.g. just running local script), avoid crashing
    __version__ = "unknown"

__author__ = "Andy McKeen"