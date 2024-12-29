import networkx as nx
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.network_flow import NetworkFlow
from mesa import Agent


class Topology(ComponentManager, nx.Graph, Agent):
    """Class that represents a network topology."""

    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None, existing_graph: nx.Graph = None) -> object:
        """Creates a Topology object backed by NetworkX functionality.

        Args:
            obj_id (int, optional): Object identifier.
            existing_graph (nx.Graph, optional): NetworkX graph representing the network
              topology.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Initializing the NetworkX topology
        if existing_graph is None:
            nx.Graph.__init__(self)
        else:
            nx.Graph.__init__(self, incoming_graph_data=existing_graph)

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {"attributes": {"id": self.id}}
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        metrics = {}
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        self.model.network_flow_scheduling_algorithm(
            topology=self, flows=NetworkFlow.all()
        )

    def _remove_path_duplicates(self, path: list) -> list:
        """Removes side-by-side duplicated nodes on network paths to avoid NetworkX
        crashes.

        Args:
            path (list): Original network path.

        Returns:
            modified_path (list): Modified network path without duplicates.
        """
        modified_path = []

        for i in range(len(path)):
            if (
                len(modified_path) == 0
                or len(modified_path) >= 1
                and modified_path[-1] != path[i]
            ):
                modified_path.append(path[i])

        return modified_path

    def calculate_path_delay(self, path: list) -> int:
        """Calculates the communication delay of a network path.

        Args:
            path (list): Network path whose delay will be calculated.

        Returns:
            path_delay (int): Network path delay.
        """
        path_delay = 0

        # Calculates the communication delay based on the delay property of each network
        # link in the path
        path_delay = nx.classes.function.path_weight(G=self, path=path, weight="delay")

        return path_delay

    def _allocate_communication_path(self, communication_path: list, app: object):
        """Adds the demand of a given application to a set of links that comprehend a
        communication path.

        Args:
            communication_path (list): Communication path.
            app (object): Application object.
        """
        for path in communication_path:
            if len(path) > 1:
                for i in range(len(path) - 1):
                    node1 = path[i]
                    node2 = path[i + 1]

                    link = self[node1][node2]

                    if app not in link["applications"]:
                        link["applications"].append(app)

    def _release_communication_path(self, communication_path: list, app: object):
        """Releases the demand of a given application from a set of links that
        comprehend a communication path.

        Args:
            communication_path (list): Communication path.
            app (object): Application object.
        """
        for path in communication_path:
            if len(path) > 1:
                for i in range(len(path) - 1):
                    node1 = path[i]
                    node2 = path[i + 1]
                    link = self[node1][node2]

                    if app in link["applications"]:
                        link["applications"].remove(app)
