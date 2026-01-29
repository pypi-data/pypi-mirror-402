"""
pyGEKO: Fast Generalized Covariance Kriging for Python.
"""

from .__about__ import __version__
from .kdata import Kdata
from .kgrid import Kgrid
from .gplot import Gplot
from . import utils

Kdata.__module__ = "pygeko"
Gplot.__module__ = "pygeko"
Kgrid.__module__ = "pygeko"


__all__ = ["Kdata", "Gplot", "Kgrid", "utils", "__version__"]

