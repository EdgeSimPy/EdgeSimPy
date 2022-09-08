""" Contains container-layer-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Mesa modules
from mesa import Agent


class ContainerLayer(ComponentManager, Agent):
    """Class that represents a container layer."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None, digest: str = "", size: int = 0, instruction: str = "") -> object:
        """Creates an User object.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
            digest (str, optional): Layer digest. Defaults to "".
            size (int, optional): Layer size (in megabytes). Defaults to 0.
            instruction (str, optional): Layer instruction. Defaults to "".

        Returns:
            object: Created User object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Layer's metadata
        self.digest = digest
        self.size = size
        self.instruction = instruction

        # Reference to the server that hosts the layer
        self.server = None

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
                "digest": self.digest,
                "size": self.size,
                "instruction": self.instruction,
            },
            "relationships": {
                "server": {"class": type(self.server).__name__, "id": self.server.id} if self.server else None,
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
