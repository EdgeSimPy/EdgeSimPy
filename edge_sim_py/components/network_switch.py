import copy

from edge_sim_py.component_manager import ComponentManager
from mesa import Agent


class NetworkSwitch(ComponentManager, Agent):
    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None):
        """Creates a NetworkSwitch object.

        Args:
            obj_id (int, optional): Object identifier.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Network switch coordinates
        self.coordinates = None

        # Base station connected to the switch
        self.base_station = None

        # List of edge servers connected to the switch
        self.edge_servers = []

        # List of links connected to the switch ports
        self.links = []

        # Power Features
        self.active = True
        self.power_model = None
        self.power_model_parameters = {}

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
                "active": self.active,
                "power_model_parameters": copy.deepcopy(self.power_model_parameters),
            },
            "relationships": {
                "power_model": self.power_model.__name__ if self.power_model else None,
                "edge_servers": [
                    {"class": type(edge_server).__name__, "id": edge_server.id}
                    for edge_server in self.edge_servers
                ],
                "links": [
                    {"class": type(link).__name__, "id": link.id} for link in self.links
                ],
                "base_station": (
                    {
                        "class": type(self.base_station).__name__,
                        "id": self.base_station.id,
                    }
                    if self.base_station
                    else None
                ),
            },
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        metrics = {
            "Instance ID": self.id,
            "Power Consumption": self.get_power_consumption(),
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        ...

    def get_power_consumption(self) -> float:
        """Gets the network switch's power consumption.

        Returns:
            power_consumption (float): Network switch's power consumption.
        """
        power_consumption = (
            self.power_model.get_power_consumption(device=self)
            if self.power_model is not None
            else 0
        )
        return power_consumption
