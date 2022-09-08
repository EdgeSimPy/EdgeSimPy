"""Contains a method that defines random user access patterns."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager

# Python libraries
import random


class RandomDurationAndIntervalAccessPattern(ComponentManager):
    """Class responsible for simulating random access patterns functionality."""

    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        user: object = None,
        app: object = None,
        start: int = 1,
        duration_values: list = [],
        interval_values: list = [],
    ) -> object:
        """Creates a RandomDurationAndIntervalAccessPattern object.

        Args:
            obj_id (int, optional): Object identifier.
            user (object, optional): User to whom the access pattern belongs to. Defaults to None.
            app (object, optional): Application accessed by the user. Defaults to None.
            start (int, optional): Time step of the first user access. Defaults to 1.
            duration_values (list, optional): List of valid values for the access durations. Defaults to [].
            interval_values (list, optional): List of valid values for the access intervals. Defaults to [].

        Returns:
            object: Created RandomDurationAndIntervalAccessPattern object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Information about the user to whom the access pattern belongs to
        self.user = user if user else None
        self.app = app if app else None

        # List of valid access pattern values
        self.duration_values = duration_values
        self.interval_values = interval_values

        # History of user accesses
        self.history = []

        # Updating the user "making_request" for the steps prior to user's first access based on the "start" attribute
        if self.user:
            self.user.access_patterns[str(app.id)] = self
            self.user.making_requests[str(app.id)] = {}
            for step in range(1, start):
                self.user.making_requests[str(app.id)][str(step)] = False
            self.user.making_requests[str(app.id)][str(start)] = True

            # Generating the initial user request
            self.get_next_access(start=start)

        # Model-specific attributes
        self.model = ComponentManager._ComponentManager__model

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "attributes": {
                "id": self.id,
                "duration_values": self.duration_values,
                "interval_values": self.interval_values,
                "history": self.history,
            },
            "relationships": {
                "user": {"class": type(self.user).__name__, "id": self.user.id} if self.user else None,
                "app": {"class": type(self.app).__name__, "id": self.app.id} if self.app else None,
            },
        }
        return dictionary

    def get_next_access(self, start: int) -> dict:
        """Gets the next access.

        Args:
            start (int): Starting point for the new access.


        Returns:
            access (dict): Next access pattern.
        """
        duration = random.sample(self.duration_values, 1)[0]
        interval = random.sample(self.interval_values, 1)[0]

        access = {
            "start": start,
            "end": start + duration - 1,
            "duration": duration,
            "waiting_time": 0,
            "access_time": 0,
            "interval": interval,
            "next_access": start + duration + interval,
        }

        self.history.append(access)

        return access
