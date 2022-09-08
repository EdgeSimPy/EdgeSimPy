"""Contains a function that creates Raspberry Pi 4 edge server objects with the capacity/power specifications provided in [1].

Please notice that disk capacity is not informed in [1]. Accordingly, we arbitrarily set a disk capacity of 32GB for the servers.

[1] Süzen, Ahmet Ali, Burhan Duman, and Betül Şen. "Benchmark Analysis of Jetson TX2, Jetson nano and
    raspberry Pi using Deep-CNN." In 2020 International Congress on Human-Computer Interaction,
    Optimization and Robotic Applications (HORA), pp. 1-5. IEEE, 2020.
"""
# EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer


def raspberry_pi4() -> object:
    """Creates an edge server object with the specifications of Raspberry Pi 4 single-board computers provided in [1].

    Returns:
        edge_server (object): Created edge server object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "Raspberry Pi 4"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 4
    edge_server.memory = 8192
    edge_server.disk = 32768

    # Power-related attributes
    edge_server.power_model_parameters = {
        "max_power_consumption": 7.3,
        "static_power_percentage": 2.56,
    }

    return edge_server
