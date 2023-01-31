"""Contains a method that creates user mobility randomly."""
# EdgeSimPy components
from edge_sim_py.components.base_station import BaseStation

# Python libraries
import random


def random_mobility(user: object):
    """Creates a random mobility path for an user.

    Args:
        user (object): User whose mobility will be defined.
    """
    # Defining the mobility model parameters based on the user's 'mobility_model_parameters' attribute
    if hasattr(user, "mobility_model_parameters"):
        parameters = user.mobility_model_parameters
    else:
        parameters = {}

    # Gathering the network topology object
    topology = user.model.topology

    # Number of "mobility routines" added each time the method is called. Defaults to 5.
    n_moves = parameters["n_moves"] if "n_moves" in parameters else 5

    # Gathering the BaseStation located in the current client's location
    current_node = BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)

    # Random mobility path
    mobility_path = []

    last_base_station = current_node
    for _ in range(n_moves):
        neighbors = list(topology.neighbors(last_base_station.network_switch))

        random_base_station = random.choice([switch.base_station for switch in neighbors])
        mobility_path.append(random_base_station)

        last_base_station = random_base_station

    # We assume that users do not necessarily move from one step to another, as one step may represent a very small time interval
    # (e.g., 1 millisecond). Therefore, each position on the mobility path is repeated N times, so that user takes a predefined
    # amount of time steps to move from one position to another. By default, users take at least 1 minute to move across positions
    # in the map. This parameter can be changed by passing a "seconds_to_move" key to the "parameters" parameter.
    if "seconds_to_move" in parameters and type(parameters["seconds_to_move"]) == int and parameters["seconds_to_move"] < 1:
        raise Exception("The 'seconds_to_move' key passed inside the mobility model's 'parameters' attribute must be > 1.")
    seconds_to_move = parameters["seconds_to_move"] if "seconds_to_move" in parameters else 60
    mobility_path = [item for item in mobility_path for i in range(int(seconds_to_move / user.model.tick_duration))]

    # Adding the path that connects the current to the target location to the client's mobility trace
    user.coordinates_trace.extend([bs.coordinates for bs in mobility_path])
