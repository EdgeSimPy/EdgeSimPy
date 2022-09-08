"""Automatic Python configuration file."""
__version__ = "1.0.0"


# Main simulation component
from .simulator import Simulator

# Misc components
from .component_manager import ComponentManager

# EdgeSimPy components
from .components import *

# EdgeSimPy component builders
from .dataset_generator import *
