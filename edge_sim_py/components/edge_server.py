""" Contains edge-server-related functionality."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edge_sim_py.components.service import Service

import typing

import networkx as nx
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.network_flow import NetworkFlow
from mesa import Agent


class EdgeServer(ComponentManager, Agent):
    """Represents an edge server in the edge simulation framework.

    This class models an edge server that processes and manages computing resources
    within the simulation environment. Edge servers connect to base stations, host
    services, and support container-based operations. They include functionalities
    for resource allocation, power management, and network flow handling.

    Attributes:
        id (int): Unique identifier of the edge server.
        coordinates (tuple, optional): Geographical coordinates of the edge server.
        model_name (str): The model name of the edge server.
        cpu (int): CPU capacity of the edge server.
        memory (int): Memory capacity of the edge server.
        disk (int): Disk storage capacity of the edge server.
        cpu_demand (int): Current CPU demand on the edge server.
        memory_demand (int): Current memory demand on the edge server.
        disk_demand (int): Current disk storage demand on the edge server.
        available (bool): Indicates if the edge server is available for hosting services.
        ongoing_migrations (int): Number of active migrations involving the edge server.
        active (bool): Indicates whether the edge server is operational.
        power_model (callable, optional): A function or object modeling power consumption.
        container_registries (list[ContainerRegistry]): Container registries hosted by the server.
        services (list[Service]): Services hosted on the edge server.
        container_images (list[ContainerImage]): Container images stored on the server.
        container_layers (list[ContainerLayer]): Container layers stored on the server.
        waiting_queue (list): Queue of container layers waiting to be downloaded.
        download_queue (list): Queue of container layers currently being downloaded.
        max_concurrent_layer_downloads (int): Maximum simultaneous downloads of container layers.
    """

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        coordinates: tuple = None,
        model_name: str = "",
        cpu: int = 0,
        memory: int = 0,
        disk: int = 0,
        power_model: typing.Callable = None,
    ):
        """Creates an EdgeServer object.

        Args:
            obj_id (int, optional): Object identifier.
            coordinates (tuple, optional): 2-tuple that represents the edge server coordinates.
            model_name (str, optional): Edge server model name. Defaults to "".
            cpu (int, optional): Edge server's CPU capacity. Defaults to 0.
            memory (int, optional): Edge server's memory capacity. Defaults to 0.
            disk (int, optional): Edge server's disk capacity. Defaults to 0.
            power_model (typing.Callable, optional): Edge server power model. Defaults to None.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id
        """Unique identifier for the edge server."""

        self.model_name = model_name
        """Model name of the edge server."""

        self.base_station = None
        """Reference to the base station the edge server is connected to."""

        self.network_switch = None
        """Reference to the network switch associated with the edge server."""

        self.coordinates = coordinates
        """Edge server coordinates"""

        # Edge server capacity
        self.cpu = cpu
        """CPU capacity of the edge server."""
        self.memory = memory
        """Memory capacity of the edge server."""
        self.disk = disk
        """Disk storage capacity of the edge server."""

        # Edge server demand
        self.cpu_demand = 0
        """Current CPU demand on the edge server."""

        self.memory_demand = 0
        """Current memory demand on the edge server."""

        self.disk_demand = 0
        """Current disk storage demand on the edge server."""

        self.available = True
        """Indicates whether the edge server is available for hosting services."""

        self.ongoing_migrations = 0
        """Number of active migrations involving this edge server."""

        # Power Features
        self.active = True
        """Indicates whether the edge server is active."""

        self.power_model = power_model
        self.power_model_parameters = {}

        self.container_registries: list[ContainerRegistry] = []
        """List of container registries hosted by the edge server."""

        self.services: list[Service] = []
        """List of services hosted on the edge server."""

        self.container_images: list[ContainerImage] = []
        """List of container images hosted by the edge server."""

        self.container_layers: list[ContainerLayer] = []
        """List of container layers hosted by the edge server."""

        # Lists that control the layers being pulled to the edge server
        self.waiting_queue: list = []
        """Queue of container layers waiting to be downloaded."""

        self.download_queue: list = []
        """Queue of container layers currently being downloaded."""

        # Number of container layers the edge server can download simultaneously (default = 3)
        self.max_concurrent_layer_downloads = 3
        """Maximum number of container layers the edge server can download simultaneously."""

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
                "available": self.available,
                "model_name": self.model_name,
                "cpu": self.cpu,
                "memory": self.memory,
                "disk": self.disk,
                "cpu_demand": self.cpu_demand,
                "memory_demand": self.memory_demand,
                "disk_demand": self.disk_demand,
                "coordinates": self.coordinates,
                "max_concurrent_layer_downloads": self.max_concurrent_layer_downloads,
                "active": self.active,
                "power_model_parameters": self.power_model_parameters,
            },
            "relationships": {
                "power_model": self.power_model.__name__ if self.power_model else None,
                "base_station": (
                    {
                        "class": type(self.base_station).__name__,
                        "id": self.base_station.id,
                    }
                    if self.base_station
                    else None
                ),
                "network_switch": (
                    {
                        "class": type(self.network_switch).__name__,
                        "id": self.network_switch.id,
                    }
                    if self.network_switch
                    else None
                ),
                "services": [
                    {"class": type(service).__name__, "id": service.id}
                    for service in self.services
                ],
                "container_layers": [
                    {"class": type(layer).__name__, "id": layer.id}
                    for layer in self.container_layers
                ],
                "container_images": [
                    {"class": type(image).__name__, "id": image.id}
                    for image in self.container_images
                ],
                "container_registries": [
                    {"class": type(reg).__name__, "id": reg.id}
                    for reg in self.container_registries
                ],
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
            "Coordinates": self.coordinates,
            "Available": self.available,
            "CPU": self.cpu,
            "RAM": self.memory,
            "Disk": self.disk,
            "CPU Demand": self.cpu_demand,
            "RAM Demand": self.memory_demand,
            "Disk Demand": self.disk_demand,
            "Ongoing Migrations": self.ongoing_migrations,
            "Services": [service.id for service in self.services],
            "Registries": [registry.id for registry in self.container_registries],
            "Layers": [layer.instruction for layer in self.container_layers],
            "Images": [image.name for image in self.container_images],
            "Download Queue": [
                f.metadata["object"].instruction for f in self.download_queue
            ],
            "Waiting Queue": [layer.instruction for layer in self.waiting_queue],
            "Max. Concurrent Layer Downloads": self.max_concurrent_layer_downloads,
            "Power Consumption": self.get_power_consumption(),
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        while (
            len(self.waiting_queue) > 0
            and len(self.download_queue) < self.max_concurrent_layer_downloads
        ):
            layer = self.waiting_queue.pop(0)

            # Gathering the list of registries that have the layer
            registries_with_layer = []
            for registry in [reg for reg in ContainerRegistry.all() if reg.available]:
                # Checking if the registry is hosted on a valid host in the
                # infrastructure and if it has the layer we need to pull
                if registry.server and any(
                    layer.digest == layer.digest
                    for layer in registry.server.container_layers
                ):
                    # Selecting a network path to be used to pull the layer from the registry
                    path = nx.shortest_path(
                        G=self.model.topology,
                        source=registry.server.base_station.network_switch,
                        target=self.base_station.network_switch,
                    )

                    registries_with_layer.append({"object": registry, "path": path})

            # Selecting the registry from which the layer will be pulled to the (target) edge server
            registries_with_layer = sorted(
                registries_with_layer, key=lambda r: len(r["path"])
            )
            registry = registries_with_layer[0]["object"]
            path = registries_with_layer[0]["path"]

            # Creating the flow object
            flow = NetworkFlow(
                topology=self.model.topology,
                source=registry.server,
                target=self,
                start=self.model.schedule.steps + 1,
                path=path,
                data_to_transfer=layer.size,
                metadata={
                    "type": "layer",
                    "object": layer,
                    "container_registry": registry,
                },
            )
            self.model.initialize_agent(agent=flow)

            # Adding the created flow to the edge server's download queue
            self.download_queue.append(flow)

    def get_power_consumption(self) -> float:
        """Gets the edge server's power consumption.

        Returns:
            power_consumption (float): Edge server's power consumption.
        """
        power_consumption = (
            self.power_model.get_power_consumption(device=self)
            if self.power_model is not None
            else 0
        )
        return power_consumption

    def has_capacity_to_host(self, service: Service) -> bool:
        """Checks if the edge server has enough free resources to host a given service.

        Args:
            service (Service): Service object that we are trying to host on the edge server.

        Returns:
            can_host (bool): Information of whether the edge server has capacity to host the service or not.
        """
        # Calculating the additional disk demand that would be incurred to the edge server
        additional_disk_demand = self._get_disk_demand_delta(service=service)

        # Calculating the edge server's free resources
        free_cpu = self.cpu - self.cpu_demand
        free_memory = self.memory - self.memory_demand
        free_disk = self.disk - self.disk_demand

        # Checking if the host would have resources to host the registry and its (additional) layers
        can_host = (
            free_cpu >= service.cpu_demand
            and free_memory >= service.memory_demand
            and free_disk >= additional_disk_demand
        )
        return can_host

    def _add_container_image(self, template_container_image: ContainerImage) -> object:
        """Adds a new container image to the edge server based on the specifications of an existing image.
        Args:
            template_container_image (object): Template container image.

        Returns:
            image (ContainerImage): New ContainerImage object.
        """
        # Checking if the edge server has no existing instance representing the same container image
        digest = template_container_image.digest
        if digest in [image.digest for image in self.container_images]:
            raise Exception(
                f"Failed in adding an image to {self} as it already hosts a image with the same digest ({digest})."
            )

        # Checking if the edge server has all the container layers that compose the
        # container image
        for layer_digest in template_container_image.layers_digests:
            if not any(
                [layer_digest == layer.digest for layer in self.container_layers]
            ):
                raise Exception(
                    f"Failed in adding an image to {self} as it does not hosts all the"
                    f" layers necessary ({layer_digest})."
                )

        # Creating a ContainerImage object to represent the new image
        image = ContainerImage()
        image.name = template_container_image.name
        image.digest = template_container_image.digest
        image.tag = template_container_image.tag
        image.architecture = template_container_image.architecture
        image.layers_digests = template_container_image.layers_digests

        # Connecting the new image to the target host
        image.server = self
        self.container_images.append(image)

        # Adding the new ContainerImage object to the list of simulator agents
        self.model.initialize_agent(agent=image)

        return image

    def _get_uncached_layers(self, service: Service) -> list:
        """Gets the list of container layers from a given service that are not present
        in the edge server's layers cache list.

        Args:
            service (Service): Service whose disk demand delta will be calculated.

        Returns:
            uncached_layers (float): List of layers from service's image not present in
              the edge server's layers cache list.
        """
        # Gathering layers present in the target server (layers, download_queue, waiting_queue)
        layers_downloaded = [layer for layer in self.container_layers]
        layers_on_download_queue = [
            flow.metadata["object"]
            for flow in self.download_queue
            if flow.metadata["object"] == "layer"
        ]
        layers_on_waiting_queue = [layer for layer in self.waiting_queue]
        layers = layers_downloaded + layers_on_download_queue + layers_on_waiting_queue

        # Gathering the service's container image
        service_image = ContainerImage.find_by(
            attribute_name="digest", attribute_value=service.image_digest
        )

        # Gathering the list of uncached layers
        uncached_layers = []
        for layer_digest in service_image.layers_digests:
            if not any(layer_digest == layer.digest for layer in layers):
                layer = ContainerLayer.find_by(
                    attribute_name="digest", attribute_value=layer_digest
                )
                if layer not in uncached_layers:
                    uncached_layers.append(layer)

        return uncached_layers

    def _get_disk_demand_delta(self, service: Service) -> float:
        """Calculates the additional disk demand necessary to host a registry inside the edge server considering
        the list of cached layers inside the edge server and the layers that compose the service's image.

        Args:
            service (Service): Service whose disk demand delta will be calculated.

        Returns:
            disk_demand_delta (float): Disk demand delta.
        """
        # Gathering the list of layers that compose the service's image that are not present in the edge server
        uncached_layers = self._get_uncached_layers(service=service)

        # Calculating the amount of disk resources required by all service layers not present in the host's disk
        disk_demand_delta = sum([layer.size for layer in uncached_layers])

        return disk_demand_delta
