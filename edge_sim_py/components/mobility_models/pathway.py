"""Contains a method that creates user mobility traces according to the Pathway mobility model [1].

[1] Bai, Fan, and Ahmed Helmy. "A Survey of Mobility Models in Wireless Adhoc Networks", pp. 1-29. 2004.
"""
# EdgeSimPy components
from edge_sim_py.components.base_station import BaseStation

# Python libraries
import random
import networkx as nx


def pathway(user: object, parameters: dict = {}):
    """Creates a mobility path for an user based on the Pathway mobility model.

    Args:
        user (object): User whose mobility will be defined.
        parameters (dict, optional): Parameters for the pathway mobility model. Defaults to {}.
    """
    # Number of "mobility routines" added each time the method is called. Defaults to 5.
    n_paths = parameters["n_paths"] if "n_paths" in parameters else 5

    # Probability of moving the user to a different location. Gets values between 0 and 1 (i.e., 0 means 0%, 1 means 100%, etc.)
    mobility_probability = parameters["mobility_probability"] if "mobility_probability" in parameters else 1

    # Gathering the BaseStation located in the current client's location
    current_node = BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)

    # Defining the user's mobility path
    mobility_path = []

    # Defining randomly if the user will move or stay in his current position
    if random.random() < mobility_probability:
        for i in range(n_paths):
            # Defining a target location and gathering the BaseStation located in that location
            target_node = random.choice([bs for bs in BaseStation.all() if bs != current_node])

            # Calculating the shortest mobility path according to the Pathway mobility model
            path = nx.shortest_path(G=user.model.topology, source=current_node.network_switch, target=target_node.network_switch)
            mobility_path.extend([network_switch.base_station for network_switch in path])

            # Removing repeated entries
            if i < n_paths - 1:
                current_node = mobility_path.pop(-1)

        # Removing repeated entries
        user_base_station = BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates_trace[-1])
        if user_base_station == mobility_path[0]:
            mobility_path.pop(0)

    else:
        mobility_path.extend([current_node for _ in range(n_paths)])

    # We assume that users do not necessarily move from one step to another, as one step may represent a very small time interval
    # (e.g., 1 millisecond). Therefore, each position on the mobility path is repeated N times, so that user takes a predefined
    # amount of time steps to move from one position to another. By default, users take at least 1 minute to move across positions
    # in the map. This parameter can be changed by passing a "seconds_to_move" key to the "parameters" parameter.
    if "seconds_to_move" in parameters and type(parameters["seconds_to_move"]) == int and parameters["seconds_to_move"] < 1:
        raise Exception("The 'seconds_to_move' key passed inside the mobility model's 'parameters' attribute must be > 1.")

    seconds_to_move = parameters["seconds_to_move"] if "seconds_to_move" in parameters else 60
    seconds_to_move = max([1, int(seconds_to_move / user.model.tick_duration)])

    mobility_path = [item for item in mobility_path for i in range(seconds_to_move)]

    # Adding the path that connects the current to the target location to the client's mobility trace
    user.coordinates_trace.extend([bs.coordinates for bs in mobility_path])
