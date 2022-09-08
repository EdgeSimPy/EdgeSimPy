""" Contains base-station-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent


class BaseStation(ComponentManager, Agent):
    """Class that represents a base station."""

    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None) -> object:
        """Creates a BaseStation object.

        Args:
            obj_id (int, optional): Object identifier.

        Returns:
            object: Created BaseStation object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Base station coordinates
        self.coordinates = None

        # Base station wireless delay
        self.wireless_delay = None

        # Lists of users, network switch, and edge servers connected to the base station
        self.users = []
        self.network_switch = None
        self.edge_servers = []

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "coordinates": self.coordinates,
                "wireless_delay": self.wireless_delay,
            },
            "relationships": {
                "users": [{"class": type(user).__name__, "id": user.id} for user in self.users],
                "edge_servers": [
                    {"class": type(edge_server).__name__, "id": edge_server.id} for edge_server in self.edge_servers
                ],
                "network_switch": {"class": type(self.network_switch).__name__, "id": self.network_switch.id}
                if self.network_switch
                else None,
            },
        }
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
        ...

    def _connect_to_network_switch(self, network_switch: object) -> object:
        """Creates a relationship between the base station and a given networkSwitch object.

        Args:
            network_switch (NetworkSwitch): networkSwitch object.

        Returns:
            object: Updated BaseStation object.
        """
        self.network_switch = network_switch
        network_switch.base_station = self

        network_switch.coordinates = self.coordinates

        return self

    def _connect_to_edge_server(self, edge_server: object) -> object:
        """Creates a relationship between the base station and a given EdgeServer object.

        Args:
            edge_server (EdgeServer): EdgeServer object.

        Returns:
            object: Updated BaseStation object.
        """
        self.edge_servers.append(edge_server)
        edge_server.base_station = self

        edge_server.coordinates = self.coordinates
        edge_server.network_switch = self.network_switch
        self.network_switch.edge_servers.append(edge_server)

        return self
