from __future__ import annotations

from typing import TYPE_CHECKING

from edge_sim_py.helpers.enums import PrivacyLevel

if TYPE_CHECKING:
    from edge_sim_py.components.user import User
    from edge_sim_py.components.service import Service

from edge_sim_py.component_manager import ComponentManager
from mesa import Agent


class Application(ComponentManager, Agent):
    """Represents an application in the edge simulation framework.

    This class models an application composed of multiple services that interact with users
    and other components in the simulation. Each application is uniquely identified by an ID
    and label and includes methods for managing relationships with services and collecting metrics.

    Attributes:
        id (int): Unique identifier of the application.
        label (str): Label describing the application.
        services (list[Service]): List of services that compose the application.
        users (list[User]): List of users interacting with the application.
        model (optional): Reference to the simulation model (set during initialization).
        unique_id (optional): Unique identifier used within the simulation framework.
    """

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        label: str = "",
        required_privacy_level: PrivacyLevel = PrivacyLevel.NONE,
    ):
        """Creates an Application object.

        Args:
            obj_id (int, optional): Object identifier.
            label (str, optional): Application label.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id: int = obj_id

        self.label = label
        """Application label."""

        self.services: list[Service] = []
        """List of services that compose the application."""

        self.users: list[User] = []
        """List of users that access the application."""

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

        self.required_privacy_level: PrivacyLevel = required_privacy_level
        """The privacy level required by the service."""

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
                "services": [
                    {"class": type(service).__name__, "id": service.id}
                    for service in self.services
                ],
                "users": [
                    {"class": type(user).__name__, "id": user.id} for user in self.users
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

    def connect_to_service(self, service: Service) -> Application:
        """Creates a relationship between the application and a given Service object.

        Args:
            service (Service): Service object.

        Returns:
            Application: Updated Application object.
        """
        self.services.append(service)
        service.application = self

        return self
