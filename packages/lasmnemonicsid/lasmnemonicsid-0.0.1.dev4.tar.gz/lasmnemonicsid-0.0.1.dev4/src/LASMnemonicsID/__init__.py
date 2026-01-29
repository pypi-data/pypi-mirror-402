
# src/LASMnemonicsID/__init__.py

"""LASMnemonicsID package for well log analysis."""

# Import submodules as objects
from . import LAS
#from . import DLIS
from . import utils

# Import all functions directly for convenience
from .LAS import *
from .DLIS import *
from .utils import *

__version__ = "0.0.1"
