""" Contains service-related functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.network_flow import NetworkFlow

# Mesa modules
from mesa import Agent

# Python libraries
import networkx as nx


class Service(ComponentManager, Agent):
    """Class that represents a service."""

    # Class attributes that allow this class to use helper methods from the ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        image_digest: str = "",
        label: str = "",
        cpu_demand: int = 0,
        memory_demand: int = 0,
        state: int = 0,
    ) -> object:
        """Creates a Service object.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
            image_digest (str, optional): Service image's digest. Defaults to "".
            label (str, optional): Service label. Defaults to "".
            cpu_demand (int, optional): Service CPU demand. Defaults to 0.
            memory_demand (int, optional): Service Memory demand. Defaults to 0.
            state (int, optional): Service state (0 for stateless services). Defaults to 0.

        Returns:
            object: Created Service object.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Service label
        self.label = label

        # Service image's digest
        self.image_digest = image_digest

        # Service demand
        self.cpu_demand = cpu_demand
        self.memory_demand = memory_demand

        # Service state
        self.state = state

        # Server that hosts the service
        self.server = None

        # Application to whom the service belongs
        self.application = None

        # List of users that access the service
        self.users = []

        # Service availability and provisioning status
        self._available = False  # Service is not available, for example, when its state is being transferred
        self.being_provisioned = False

        # List that stores metadata about each migration experienced by the service throughout the simulation
        self.__migrations = []

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
                "state": self.state,
                "_available": self._available,
                "cpu_demand": self.cpu_demand,
                "memory_demand": self.memory_demand,
                "image_digest": self.image_digest,
            },
            "relationships": {
                "application": {"class": type(self.application).__name__, "id": self.application.id},
                "server": {"class": type(self.server).__name__, "id": self.server.id} if self.server else None,
            },
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """

        if len(self._Service__migrations) > 0:

            last_migration = {
                "status": self._Service__migrations[-1]["status"],
                "origin": str(self._Service__migrations[-1]["origin"]),
                "target": str(self._Service__migrations[-1]["target"]),
                "start": self._Service__migrations[-1]["start"],
                "end": self._Service__migrations[-1]["end"],
                "waiting": self._Service__migrations[-1]["waiting_time"],
                "pulling": self._Service__migrations[-1]["pulling_layers_time"],
                "migr_state": self._Service__migrations[-1]["migrating_service_state_time"],
            }
        else:
            last_migration = None

        metrics = {
            "Instance ID": self.id,
            "Available": self._available,
            "Server": self.server.id if self.server else None,
            "Being Provisioned": self.being_provisioned,
            "Last Migration": last_migration,
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        if len(self._Service__migrations) > 0 and self._Service__migrations[-1]["end"] == None:
            migration = self._Service__migrations[-1]

            # Gathering information about the service's image
            image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)

            # Gathering layers present in the target server (layers, download_queue, waiting_queue)
            layers_downloaded = [l for l in migration["target"].container_layers if l.digest in image.layers_digests]
            layers_on_download_queue = [
                flow.metadata["object"]
                for flow in migration["target"].download_queue
                if flow.metadata["object"].digest in image.layers_digests
            ]

            # Setting the migration status to "pulling_layers" once any of the service layers start being downloaded
            if migration["status"] == "waiting":
                layers_on_target_server = layers_downloaded + layers_on_download_queue

                if len(layers_on_target_server) > 0:
                    migration["status"] = "pulling_layers"

            if migration["status"] == "pulling_layers" and len(image.layers_digests) == len(layers_downloaded):
                # Once all the layers that compose the service's image are pulled, the service container is deprovisioned on its
                # origin host even though it still is in there (that's why it is still on the origin's services list). This action
                # is only taken in case the current provisioning process regards a migration.
                if self.server:
                    self.server.cpu_demand -= self.cpu_demand
                    self.server.memory_demand -= self.memory_demand

                # Once all service layers have been pulled, creates a ContainerImage object representing
                # the service image on the target host if that host didn't already have such image
                if not any([image.digest == self.image_digest for image in migration["target"].container_images]):
                    # Finding similar image provisioned on the infrastructure to get metadata from it when creating the new image
                    template_image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)
                    if template_image is None:
                        raise Exception(f"Could not find any container image with digest: {self.image_digest}")

                    # Creating the new image on the target host
                    image = ContainerImage()
                    image.name = template_image.name
                    image.digest = template_image.digest
                    image.tag = template_image.tag
                    image.architecture = template_image.architecture
                    image.layers_digests = template_image.layers_digests

                    # Connecting the new image to the target host
                    image.server = migration["target"]
                    migration["target"].container_images.append(image)

                if self.state == 0 or self.server == None:
                    # Stateless Services: migration is set to finished immediately after layers are pulled
                    migration["status"] = "finished"
                else:
                    # Stateful Services: state must be migrated to the target host after layers are pulled
                    migration["status"] = "migrating_service_state"

                    # Services are unavailable during the period where their states are being migrated
                    self._available = False

                    # Selecting the path that will be used to transfer the service state
                    path = nx.shortest_path(
                        G=self.model.topology,
                        source=self.server.base_station.network_switch,
                        target=migration["target"].base_station.network_switch,
                    )

                    # Creating network flow representing the service state that will be migrated to its target host
                    flow = NetworkFlow(
                        topology=self.model.topology,
                        source=self.server,
                        target=migration["target"],
                        start=self.model.schedule.steps + 1,
                        path=path,
                        data_to_transfer=self.state,
                        metadata={"type": "service_state", "object": self},
                    )
                    self.model.initialize_agent(agent=flow)

            # Incrementing the migration time metadata
            if migration["status"] == "waiting":
                migration["waiting_time"] += 1
            elif migration["status"] == "pulling_layers":
                migration["pulling_layers_time"] += 1
            elif migration["status"] == "migrating_service_state":
                migration["migrating_service_state_time"] += 1

            if migration["status"] == "finished":
                # Storing when the migration has finished
                migration["end"] = self.model.schedule.steps + 1

                # Updating the service's origin server metadata
                if self.server:
                    self.server.services.remove(self)
                    self.server.ongoing_migrations -= 1

                # Updating the service's target server metadata
                self.server = migration["target"]
                self.server.services.append(self)
                self.server.ongoing_migrations -= 1

                # Tagging the service as available once their migrations finish
                self._available = True
                self.being_provisioned = False

                # Changing the routes used to communicate the application that owns the service to its users
                app = self.application
                users = app.users
                for user in users:
                    user.set_communication_path(app)

    def provision(self, target_server: object):
        """Starts the service's provisioning process. This process comprises both placement and migration. In the former, the
        service is not initially hosted by any server within the infrastructure. In the latter, the service is already being
        hosted by a server and we want to relocate it to another server within the infrastructure.

        Args:
            target_server (object): Target server.
        """
        # Gathering layers present in the target server (layers, download_queue, waiting_queue)
        layers_downloaded = [layer for layer in target_server.container_layers]
        layers_on_download_queue = [flow.metadata["object"] for flow in target_server.download_queue]
        layers_on_waiting_queue = [layer for layer in target_server.waiting_queue]

        layers_on_target_server = layers_downloaded + layers_on_download_queue + layers_on_waiting_queue

        # Gathering the list of layers that compose the service image that are not present in the target server
        image = ContainerImage.find_by(attribute_name="digest", attribute_value=self.image_digest)
        for layer_digest in image.layers_digests:
            if not any(layer.digest == layer_digest for layer in layers_on_target_server):
                # As the image only stores its layers digests, we need to get information about each of its layers
                layer_metadata = ContainerLayer.find_by(attribute_name="digest", attribute_value=layer_digest)

                # Creating a new layer object that will be pulled to the target server
                layer = ContainerLayer(
                    digest=layer_metadata.digest,
                    size=layer_metadata.size,
                    instruction=layer_metadata.instruction,
                )
                self.model.initialize_agent(agent=layer)

                # Reserving the layer disk demand inside the target server
                target_server.disk_demand += layer.size

                # Adding the layer to the target server's waiting queue (layers it must download at some point)
                target_server.waiting_queue.append(layer)

        # Telling EdgeSimPy that this service is being provisioned
        self.being_provisioned = True

        # Telling EdgeSimPy the service's current server is now performing a migration. This action is only triggered in case
        # this method is called for performing a migration (i.e., the service is already within the infrastructure)
        if self.server:
            self.server.ongoing_migrations += 1

        # Reserving the service demand inside the target server and telling EdgeSimPy that server will receive a service
        target_server.ongoing_migrations += 1
        target_server.cpu_demand += self.cpu_demand
        target_server.memory_demand += self.memory_demand

        # Updating the service's migration status
        self._Service__migrations.append(
            {
                "status": "waiting",
                "origin": self.server,
                "target": target_server,
                "start": self.model.schedule.steps + 1,
                "end": None,
                "waiting_time": 0,
                "pulling_layers_time": 0,
                "migrating_service_state_time": 0,
            }
        )
