"""Contains a function that creates NVIDIA Jetson Nano edge server objects with the capacity/power specifications provided in [1].

[1] Süzen, Ahmet Ali, Burhan Duman, and Betül Şen. "Benchmark Analysis of Jetson TX2, Jetson nano and
    raspberry Pi using Deep-CNN." In 2020 International Congress on Human-Computer Interaction,
    Optimization and Robotic Applications (HORA), pp. 1-5. IEEE, 2020.
"""
# EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer


def jetson_nano() -> object:
    """Creates an edge server object with the specifications of NVIDIA Jetson Nano single-board computers provided in [1].

    Returns:
        edge_server (object): Created edge server object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "NVIDIA Jetson Nano"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 4
    edge_server.memory = 4096
    edge_server.disk = 16384

    # Power-related attributes
    edge_server.power_model_parameters = {
        "max_power_consumption": 10,
        "static_power_percentage": 5,
    }

    return edge_server
