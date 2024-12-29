from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edge_sim_py.components.application import Application

import copy

import networkx as nx
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.base_station import BaseStation
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.topology import Topology
from mesa import Agent


class User(ComponentManager, Agent):
    # Class attributes that allow this class to use helper methods from the
    # ComponentManager
    _instances = []
    """List of all `User` instances created."""

    _object_count: int = 0
    """Counter to assign unique IDs to each `User` instance."""

    def __init__(self, obj_id: int | None = None):
        """Initializes a new instance of the `User` class.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id
        """Unique identifier for the user."""

        # User coordinates
        self.coordinates_trace = []
        self.coordinates = None

        self.applications: list[Application] = []
        """List of applications accessed by the user."""

        self.base_station = None
        """Reference to the base station the user is connected to."""

        # User access metadata
        self.making_requests = {}
        self.access_patterns = {}

        # User mobility model
        self.mobility_model = None
        self.mobility_model_parameters = {}

        # List of metadata from applications accessed by the user
        self.communication_paths = {}
        self.delays = {}
        self.delay_slas = {}

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        access_patterns = {}
        for app_id, access_pattern in self.access_patterns.items():
            access_patterns[app_id] = {
                "class": access_pattern.__class__.__name__,
                "id": access_pattern.id,
            }

        dictionary = {
            "attributes": {
                "id": self.id,
                "coordinates": self.coordinates,
                "coordinates_trace": self.coordinates_trace,
                "delays": copy.deepcopy(self.delays),
                "delay_slas": copy.deepcopy(self.delay_slas),
                "communication_paths": copy.deepcopy(self.communication_paths),
                "making_requests": copy.deepcopy(self.making_requests),
                "mobility_model_parameters": (
                    copy.deepcopy(self.mobility_model_parameters)
                    if self.mobility_model_parameters
                    else {}
                ),
            },
            "relationships": {
                "access_patterns": access_patterns,
                "mobility_model": self.mobility_model.__name__,
                "applications": [
                    {"class": type(app).__name__, "id": app.id}
                    for app in self.applications
                ],
                "base_station": {
                    "class": type(self.base_station).__name__,
                    "id": self.base_station.id,
                },
            },
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        access_history = {}
        for app in self.applications:
            access_history[str(app.id)] = self.access_patterns[str(app.id)].history

        metrics = {
            "Instance ID": self.id,
            "Coordinates": self.coordinates,
            "Base Station": (
                f"{self.base_station} ({self.base_station.coordinates})"
                if self.base_station
                else None
            ),
            "Delays": copy.deepcopy(self.delays),
            "Communication Paths": copy.deepcopy(self.communication_paths),
            "Making Requests": copy.deepcopy(self.making_requests),
            "Access History": copy.deepcopy(access_history),
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        # Updating user access
        current_step = self.model.schedule.steps + 1
        for app in self.applications:
            last_access = self.access_patterns[str(app.id)].history[-1]

            # Updating user access waiting and access times. Waiting time represents
            # the period in which the user is waiting for his application to be
            # provisioned. Access time represents the period in which the user is
            # successfully accessing his application, meaning his application is
            # available. We assume that an application is only available when all its
            # services are available.
            if self.making_requests[str(app.id)][str(current_step)] is True:
                if len([s for s in app.services if s._available]) == len(app.services):
                    last_access["access_time"] += 1
                else:
                    last_access["waiting_time"] += 1

            # Updating user's making requests attribute for the next time step
            if (
                current_step + 1 >= last_access["start"]
                and current_step + 1 <= last_access["end"]
            ):
                self.making_requests[str(app.id)][str(current_step + 1)] = True
            else:
                self.making_requests[str(app.id)][str(current_step + 1)] = False

            # Creating new access request if needed
            if current_step + 1 == last_access["next_access"]:
                self.making_requests[str(app.id)][str(current_step + 1)] = True
                self.access_patterns[str(app.id)].get_next_access(
                    start=current_step + 1
                )

        # Re-executing user's mobility model in case no future mobility track is known
        # by the simulator
        if len(self.coordinates_trace) <= self.model.schedule.steps:
            self.mobility_model(self)

        # Updating user's location
        if self.coordinates != self.coordinates_trace[self.model.schedule.steps]:
            self.coordinates = self.coordinates_trace[self.model.schedule.steps]

            # Connecting the user to the closest base station
            self.base_station = BaseStation.find_by(
                attribute_name="coordinates", attribute_value=self.coordinates
            )

            for application in self.applications:
                # Only updates the routing path of apps available (i.e., whose services
                # are available)
                services_available = len(
                    [s for s in application.services if s._available]
                )
                if services_available == len(application.services):
                    # Recomputing user communication paths
                    self.set_communication_path(app=application)
                else:
                    self.communication_paths[str(application.id)] = []
                    self._compute_delay(app=application)

    def _compute_delay(self, app: object, metric: str = "latency") -> int:
        """Computes the delay of an application accessed by the user.

        Args:
            metric (str, optional): Delay measure (valid options: 'latency' and 'response time'). Defaults to 'latency'.
            app (object): Application accessed by the user.

        Returns:
            delay (int): User-perceived delay when accessing application "app".
        """
        topology = Topology.first()

        services_available = len([s for s in app.services if s._available])
        if services_available < len(app.services):
            # Defining the delay as infinity if any of the application services is not
            # available
            delay = float("inf")
        else:
            # Initializes the application's delay with the time it takes to communicate
            # its client and his base station
            delay = self.base_station.wireless_delay

            # Adding the communication path delay to the application's delay
            for path in self.communication_paths[str(app.id)]:
                delay += topology.calculate_path_delay(
                    path=[NetworkSwitch.find_by_id(i) for i in path]
                )

            if metric.lower() == "response time":
                # We assume that Response Time = Latency * 2
                delay = delay * 2

        # Updating application delay inside user's 'applications' attribute
        self.delays[str(app.id)] = delay

        return delay

    def set_communication_path(
        self, app: object, communication_path: list = []
    ) -> list:
        """Updates the set of links used during the communication of user and its
        application.

        Args:
            app (object): User application.
            communication_path (list, optional): User-specified communication path.
                Defaults to [].

        Returns:
            list: Updated communication path.
        """
        topology = Topology.first()

        # Releasing links used in the past to connect the user with its application
        if app in self.communication_paths:
            path = [
                [NetworkSwitch.find_by_id(i) for i in p]
                for p in self.communication_paths[str(app.id)]
            ]
            topology._release_communication_path(communication_path=path, app=app)

        # Defining communication path
        if len(communication_path) > 0:
            self.communication_paths[str(app.id)] = communication_path
        else:
            self.communication_paths[str(app.id)] = []

            service_hosts_base_stations = [
                service.server.base_station
                for service in app.services
                if service.server
            ]
            communication_chain = [self.base_station] + service_hosts_base_stations

            # Defining a set of links to connect the items in the application's service
            # chain
            for i in range(len(communication_chain) - 1):

                # Defining origin and target nodes
                origin = communication_chain[i]
                target = communication_chain[i + 1]

                # Finding and storing the best communication path between the origin and
                # target nodes
                if origin == target:
                    path = []
                else:
                    path = nx.shortest_path(
                        G=topology,
                        source=origin.network_switch,
                        target=target.network_switch,
                        weight="delay",
                        method="dijkstra",
                    )

                # Adding the best path found to the communication path
                self.communication_paths[str(app.id)].append(
                    [network_switch.id for network_switch in path]
                )

                # Computing the new demand of chosen links
                path = [
                    [NetworkSwitch.find_by_id(i) for i in p]
                    for p in self.communication_paths[str(app.id)]
                ]
                topology._allocate_communication_path(communication_path=path, app=app)

        # Computing application's delay
        self._compute_delay(app=app, metric="latency")

        return self.communication_paths[str(app.id)]

    def _connect_to_application(self, app: object, delay_sla: float) -> object:
        """Connects the user to a given application, establishing all the relationship
        attributes in both objects.

        Args:
            app (object): Application that will be connected to the user.
            delay_sla (float): Delay threshold for the user regarding the specified
              application.

        Returns:
            self (object): Updated user object.
        """
        # Defining the relationship attributes between the user and its new application
        self.applications.append(app)
        app.users.append(self)

        # Assigning delay and delay SLA attributes.
        # Delay is initially None, and must be overwritten by the service placement
        self.delay_slas[str(app.id)] = delay_sla
        self.delays[str(app.id)] = None

    def _set_initial_position(
        self, coordinates: list, number_of_replicates: int = 0
    ) -> object:
        """Defines the initial coordinates for the user, automatically connecting to a
        base station in that position.

        Args:
            coordinates (list): Initial user coordinates.
            number_of_replicates (int, optional): Number of times the initial
              coordinates will replicated in the coordinates trace. Defaults to 0.

        Returns:
            self (object): Updated user object.
        """
        # Defining the "coordinates" and "coordinates_trace" attributes
        self.coordinates = coordinates
        self.coordinates_trace = [coordinates for _ in range(number_of_replicates - 1)]

        # Connecting the user to the base station that shares his initial position
        base_station = BaseStation.find_by(
            attribute_name="coordinates", attribute_value=self.coordinates
        )

        if base_station is None:
            raise Exception(
                f"No base station was found at coordinates {coordinates} to connect to"
                f" user {self}."
            )

        self.base_station = base_station
        base_station.users.append(self)
