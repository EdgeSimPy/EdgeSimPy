""" Contains application-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent


class Application(ComponentManager, Agent):
    """Class that represents an application."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None, label: str = "") -> object:
        """Creates an Application object.

        Args:
            obj_id (int, optional): Object identifier.
            label (str, optional): Application label.

        Returns:
            object: Created Application object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Application label
        self.label = label

        # List of services that compose the application
        self.services = []

        # List of users that access the application
        self.users = []

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
                "label": self.label,
            },
            "relationships": {
                "services": [{"class": type(service).__name__, "id": service.id} for service in self.services],
                "users": [{"class": type(user).__name__, "id": user.id} for user in self.users],
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

    def connect_to_service(self, service: object) -> object:
        """Creates a relationship between the application and a given Service object.

        Args:
            service (Service): Service object.

        Returns:
            object: Updated Application object.
        """
        self.services.append(service)
        service.application = self

        return self
