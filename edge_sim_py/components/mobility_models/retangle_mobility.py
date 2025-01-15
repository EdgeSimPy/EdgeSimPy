from edge_sim_py.components.base_station import BaseStation

import random
import networkx as nx

def retangle_mobility(user: object):
    if hasattr(user, "mobility_model_parameters"):
        parameters = user.mobility_model_parameters
    else:
        parameters = {}

    n_paths = parameters["n_paths"] if "n_paths" in parameters else 5

    current_node = BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)

    mobility_path = []

    for i in range(n_paths):
        #allRetangularBaseStation = [
        #    BaseStation.find_by(attribute_name="coordinates", attribute_value=[0,0]),
        #    BaseStation.find_by(attribute_name="coordinates", attribute_value=[6,0]),
        #    BaseStation.find_by(attribute_name="coordinates", attribute_value=[7,3]),
        #    BaseStation.find_by(attribute_name="coordinates", attribute_value=[1,3])
        #]
        #target_node = random.choice([bs for bs in allRetangularBaseStation])
        
        
        #target_node = allRetangularBaseStation[len(allRetangularBaseStation)%4]
        #print('rodando como teste...')
        #print(user)
        #print(user.coordinates)

        #mapa da movimentação em quadrados
        coordinate_map = {
            (0, 0): (6, 0),
            (6, 0): (7, 3),
            (7, 3): (1, 3),
            (1, 3): (0, 0),
        }

        #pegar próxima movimentação
        next_coordinates = coordinate_map.get(tuple(user.coordinates), (0, 0))

        target_node = BaseStation.find_by(attribute_name="coordinates", attribute_value=list(next_coordinates))

        path = nx.shortest_path(G=user.model.topology, source=current_node.network_switch, target=target_node.network_switch)
        mobility_path.extend([network_switch.base_station for network_switch in path])

        if i < n_paths - 1:
            current_node = mobility_path.pop(-1)

        # Removing repeated entries
        #user_base_station = BaseStation.find_by(attribute_name="coordinates", attribute_value=user.coordinates)
        #if user_base_station == mobility_path[0]:
        #    mobility_path.pop(0)

    if "seconds_to_move" in parameters and type(parameters["seconds_to_move"]) == int and parameters["seconds_to_move"] < 1:
        raise Exception("The 'seconds_to_move' key passed inside the mobility model's 'parameters' attribute must be > 1.")

    seconds_to_move = parameters["seconds_to_move"] if "seconds_to_move" in parameters else 1
    seconds_to_move = max([1, int(seconds_to_move / user.model.tick_duration)])

    mobility_path = [item for item in mobility_path for i in range(seconds_to_move)]

    user.coordinates_trace.extend([bs.coordinates for bs in mobility_path])