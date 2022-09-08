"""Contains a function that creates E5645 edge server objects with the capacity/power specifications provided in [1].

Please notice that disk capacity is not informed in [1]. Accordingly, we arbitrarily set a disk capacity of 128GB for the servers.

[1] Zakarya, Muhammad, Lee Gillam, Hashim Ali, Izaz Rahman, Khaled Salah, Rahim Khan, Omer Rana, and Rajkumar Buyya.
    "Epcaware: a game-based, energy, performance and cost efficient resource management technique for multi-access
    edge computing." IEEE Transactions on Services Computing (2020).
"""
# EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer


def e5645() -> object:
    """Creates an edge server object with the specifications of E5645 servers provided in [1].

    Returns:
        edge_server (object): Created edge server object.
    """
    edge_server = EdgeServer()
    edge_server.model_name = "E5645"

    # Computational capacity (CPU in cores, RAM memory in megabytes, and disk in megabytes)
    edge_server.cpu = 12
    edge_server.memory = 16384
    edge_server.disk = 131072

    # Power-related attributes
    edge_server.power_model_parameters = {
        "max_power_consumption": 200,
        "static_power_percentage": 63.1,
    }

    return edge_server
