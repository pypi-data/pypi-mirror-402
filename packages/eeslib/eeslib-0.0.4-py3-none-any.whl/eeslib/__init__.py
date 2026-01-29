"""
EESLib - Heat Transfer and Thermodynamics Library

This package provides functions for heat transfer and thermodynamics calculations, derived from Engineering Equation Solver (EES) for educational use.
"""

from . import fluid_properties
from . import internal_flow
from . import external_flow
from . import heat_exchangers
from . import boiling
from . import fin_efficiency
from . import radiation
from . import functions
from . import lookup_data
from . import talbot_inversion

__version__ = "0.0.4"
__author__ = "Mike Wagner"
__email__ = "mjwagner2@wisc.edu"