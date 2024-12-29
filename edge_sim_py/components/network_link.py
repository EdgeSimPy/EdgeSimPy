from edge_sim_py.component_manager import ComponentManager
from mesa import Agent


class NetworkLink(dict, ComponentManager, Agent):
    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None):
        """Creates a NetworkLink object.

        Args:
            obj_id (int, optional): Object identifier.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self["id"] = obj_id

        # Reference to the network topology
        self["topology"] = None

        # List of network nodes that are connected by the link
        self["nodes"] = []

        # Link delay
        self["delay"] = 0

        # Link bandwidth capacity and bandwidth demand
        self["bandwidth"] = 0
        self["bandwidth_demand"] = 0

        # List of applications using the link for routing data to their users
        self["applications"] = []

        # List of network flows passing through the link
        self["active_flows"] = []

        # Network link active status
        self["active"] = True

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self["model"] = None
        self["unique_id"] = None

    def __getattr__(self, attribute_name: str):
        """Retrieves an object attribute by its name.

        Args:
            attribute_name (str): Name of the attribute to be retrieved.

        Returns:
            (any): Attribute value.
        """
        if attribute_name in self:
            return self[attribute_name]
        else:
            raise AttributeError(
                f"Object {self} has no such attribute '{attribute_name}'."
            )

    def __setattr__(self, attribute_name: str, attribute_value: object):
        """Overrides the value of an object attribute.

        Args:
            attribute_name (str): Name of the attribute to be changed.
            attribute_value (object): Value for the attribute.
        """
        self[attribute_name] = attribute_value

    def __delattr__(self, attribute_name: str):
        """Deletes an object attribute by its name.

        Args:
            attribute_name (str): Name of the attribute to be deleted.
        """
        if attribute_name in self:
            del self[attribute_name]
        else:
            raise AttributeError(
                f"Object {self} has no such attribute '{attribute_name}'."
            )

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "delay": self.delay,
                "bandwidth": self.bandwidth,
                "bandwidth_demand": self.bandwidth_demand,
                "active": self.active,
            },
            "relationships": {
                "topology": {"class": "Topology", "id": self.topology.id},
                "active_flows": [
                    {"class": type(flow).__name__, "id": flow.id}
                    for flow in self.active_flows
                ],
                "applications": [
                    {"class": type(app).__name__, "id": app.id}
                    for app in self.applications
                ],
                "nodes": [
                    {"class": type(node).__name__, "id": node.id} for node in self.nodes
                ],
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
