"""Automatic Python configuration file."""
__version__ = "1.1.0"

# EdgeSimPy Components
from .topology import Topology
from .network_switch import NetworkSwitch
from .network_link import NetworkLink
from .base_station import BaseStation
from .user import User
from .container_layer import ContainerLayer
from .container_image import ContainerImage
from .container_registry import ContainerRegistry
from .network_flow import NetworkFlow
from .application import Application
from .service import Service
from .edge_server import EdgeServer

# Network flow scheduling algorithms
from .flow_scheduling import *

# User mobility models
from .mobility_models import *

# User access patterns
from .user_access_patterns import *

# Power models
from .power_models import *
