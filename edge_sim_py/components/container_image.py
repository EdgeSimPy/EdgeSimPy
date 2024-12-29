""" Contains container-image-related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edge_sim_py.components.container_layer import ContainerLayer

from edge_sim_py.component_manager import ComponentManager


class ContainerImage(ComponentManager):
    """Class that represents a container image."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        name: str = "",
        digest: str = "",
        tag: str = "0.0.0",
        architecture: str = "",
        layers: list[ContainerLayer] = [],
    ):
        """Creates a ContainerImage object.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
            name (str, optional): Image name. Defaults to "".
            digest (str, optional): Image digest. Defaults to "".
            tag (str, optional): Image tag (i.e., version code). Defaults to "0.0.0".
            architecture (str, optional): Image architecture (e.g., "amd64"). Defaults to "".
            layers (list, optional): Digests of layers that compose the image. Defaults to [].
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Image metadata
        self.name = name
        self.digest = digest
        self.tag = tag
        self.architecture = architecture

        # List with the digests of the container layers that compose the image
        self.layers_digests: list[ContainerLayer] = layers

        # Reference to the server that accommodates the image
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
                "name": self.name,
                "tag": self.tag,
                "digest": self.digest,
                "layers_digests": self.layers_digests,
                "architecture": self.architecture,
            },
            "relationships": {
                "server": (
                    {"class": type(self.server).__name__, "id": self.server.id}
                    if self.server
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
        metrics = {}
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        ...
