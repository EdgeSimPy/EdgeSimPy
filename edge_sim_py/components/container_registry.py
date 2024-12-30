from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from edge_sim_py.components.edge_server import EdgeServer

from random import choice

from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.network_flow import NetworkFlow
from edge_sim_py.components.service import Service
from mesa import Agent


class ContainerRegistry(ComponentManager, Agent):
    """Class that represents a container registry."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(self, obj_id: int = None, cpu_demand: int = 0, memory_demand: int = 0):
        """Creates a ContainerRegistry object.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
            cpu_demand (int, optional): Registry's CPU demand. Defaults to 0.
            memory_demand (int, optional): Registry's Memory demand. Defaults to 0.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Registry's CPU and memory demand
        self.cpu_demand = cpu_demand
        self.memory_demand = memory_demand

        # Registry's available status (set to false when the registry is being provisioned)
        self.available = True

        # Server that hosts the registry
        self.server: EdgeServer | None = None

        # List that stores metadata about each migration experienced by the registry throughout the simulation
        self._migrations: list = []

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
                "cpu_demand": self.cpu_demand,
                "memory_demand": self.memory_demand,
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
        metrics = {
            "Available": self.available,
            "CPU Demand": self.cpu_demand,
            "RAM Demand": self.memory_demand,
            "Server": self.server.id if self.server else None,
            "Images": (
                [image.id for image in self.server.container_images]
                if self.server
                else []
            ),
            "Layers": (
                [layer.id for layer in self.server.container_layers]
                if self.server
                else []
            ),
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        if not self.available:
            # Gathering a template registry container image
            registry_image = ContainerImage.find_by(
                attribute_name="name", attribute_value="registry"
            )

            # Checking if the host has the container layers that compose the container registry image
            layers_hosted_by_server = 0
            for layer_digest in registry_image.layers_digests:
                if any(
                    [
                        layer_digest == layer.digest
                        for layer in self.server.container_layers
                    ]
                ):
                    layers_hosted_by_server += 1

            # Checking if the host has the container registry image
            server_images_digests = [
                image.digest for image in self.server.container_images
            ]
            if (
                layers_hosted_by_server == len(registry_image.layers_digests)
                and registry_image.digest not in server_images_digests
            ):
                self.server._add_container_image(
                    template_container_image=registry_image
                )

            # Updating registry's availability status if its provisioning process has ended
            if not self.available and registry_image.digest in [
                image.digest for image in self.server.container_images
            ]:
                self.available = True

    @classmethod
    def provision(
        cls,
        target_server: object,
        registry_cpu_demand: int = None,
        registry_memory_demand: int = None,
    ) -> object:
        """Provisions a new container registry on a given server.

        Args:
            target_server (object): Server that will host the new container registry.
            registry_cpu_demand (int, optional): CPU demand that will be assigned to
                the new registry. Defaults to None.
            registry_memory_demand (int, optional): Memory demand that will be assigned
                to the new registry. Defaults to None.

        Returns:
            registry (object): New container registry.
        """
        # If no information on CPU or memory demand are specified within the parameters,
        # those values are taken from random container registry within the infrastructure
        template_container_registry = choice(ContainerRegistry.all())
        cpu_demand = (
            registry_cpu_demand
            if registry_cpu_demand is not None
            else template_container_registry.cpu_demand
        )
        memory_demand = (
            registry_memory_demand
            if registry_memory_demand is not None
            else template_container_registry.memory_demand
        )

        # Creating the container registry object
        registry = ContainerRegistry(cpu_demand=cpu_demand, memory_demand=memory_demand)
        target_server.model.initialize_agent(agent=registry)

        # The new container is set as unavailable until it is completely provisioned in
        # the target server
        registry.available = False

        # Creating relationship between the edge server and the new registry
        registry.server = target_server
        target_server.container_registries.append(registry)

        # Updating the host's resource usage
        target_server.cpu_demand += registry.cpu_demand
        target_server.memory_demand += registry.memory_demand

        # Gathering a template registry image
        registry_image = ContainerImage.find_by(
            attribute_name="name", attribute_value="registry"
        )

        # Checking if the target server already has a registry container image on it
        if registry_image.digest not in [
            image.digest for image in target_server.container_images
        ]:
            # Gathering layers present in the target server (layers, download_queue,
            # waiting_queue)
            layers_downloaded = [layer for layer in target_server.container_layers]
            layers_on_download_queue = [
                flow.metadata["object"] for flow in target_server.download_queue
            ]
            layers_on_waiting_queue = [layer for layer in target_server.waiting_queue]

            layers_on_target_server = (
                layers_downloaded + layers_on_download_queue + layers_on_waiting_queue
            )

            # Adding the registry's container image layers into the target server's
            # waiting queue if they are not cached in there
            for layer_digest in registry_image.layers_digests:
                if not any(
                    layer.digest == layer_digest for layer in layers_on_target_server
                ):
                    # Creating a new layer object that will be pulled to the target server
                    layer_template = ContainerLayer.find_by(
                        attribute_name="digest", attribute_value=layer_digest
                    )
                    layer = ContainerLayer(
                        digest=layer_template.digest,
                        size=layer_template.size,
                        instruction=layer_template.instruction,
                    )
                    target_server.model.initialize_agent(agent=layer)

                    # Reserving the layer disk demand inside the target server
                    target_server.disk_demand += layer.size

                    # Adding the layer to the target server's waiting queue (layers it
                    # must download at some point)
                    target_server.waiting_queue.append(layer)

        return registry

    def deprovision(self, purge_images: bool = False):
        """Deprovisions a container registry, releasing the allocated resources on its
        host server.

        Args:
            purge_images (bool, optional): Removes all container images and associated
              layers from the server. Defaults to False.
        """
        # Checking if the registry has a host server and if is not currently being used
        # to pull any container layer
        flows_using_the_registry = [
            flow
            for flow in NetworkFlow.all()
            if flow.status == "active" and flow.metadata["container_registry"] == self
        ]
        if self.server and len(flows_using_the_registry) == 0:
            # Removing unused container images and associated layers from the server if
            # the "purge_images" flag is True
            if purge_images:
                # Gathering the list of unused container images and layers
                unused_images = list(self.server.container_images)
                unused_layers = list(self.server.container_layers)
                for service in Service.all():
                    service_target = (
                        service._migrations[-1]["target"]
                        if len(service._migrations) > 0
                        else None
                    )
                    if service.server == self.server or service_target == self.server:
                        image = next(
                            (
                                img
                                for img in unused_images
                                if img.digest == service.image_digest
                            ),
                            None,
                        )
                        # Removing the used image from the "unused_images" list
                        unused_images.remove(image)

                        # Removing used layers from the "unused_layers" list
                        for layer in unused_layers:
                            if layer.digest in image.layers_digests:
                                unused_layers.remove(layer)

                # Removing unused images
                for image in unused_images:
                    # Removing the unused image from its host
                    image.server.container_images.remove(image)
                    image.server = None

                    # Removing the unused image from the simulator's agent list and
                    # from its class instance list
                    image.model.schedule.remove(image)
                    image.__class__._instances.remove(image)

                # Removing unused layers
                for layer in unused_layers:
                    # Removing the unused layer from its host
                    layer.server.disk_demand -= layer.size
                    layer.server.container_layers.remove(layer)
                    layer.server = None

                    # Removing the unused layer from the simulator's agent list and
                    # from its class instance list
                    layer.model.schedule.remove(layer)
                    layer.__class__._instances.remove(layer)

            # Removing relationship between the registry and its server
            self.server.container_registries.remove(self)
            self.server.memory_demand -= self.memory_demand
            self.server.cpu_demand -= self.cpu_demand
            self.server = None

            # Removing the registry
            self.model.schedule.remove(self)
            self.__class__._instances.remove(self)
