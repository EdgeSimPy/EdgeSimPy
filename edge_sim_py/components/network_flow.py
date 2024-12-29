from edge_sim_py.component_manager import ComponentManager


class NetworkFlow(ComponentManager):

    # Class attributes that allow this class to use helper methods from the
    # ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        obj_id: int = None,
        topology: object = None,
        status: str = "active",
        source: object = None,
        target: object = None,
        start: int = 0,
        path: list = [],
        data_to_transfer: int = 0,
        metadata: dict = {},
    ):
        """Creates a NetworkFlow object.

        Args:
            obj_id (int, optional): Object identifier. Defaults to None.
            topology (object, optional): Network topology. Defaults to None.
            status (int, optional): Flow status. Defaults to "active".
            source (object, optional): Node where the flow starts. Defaults to None.
            target (object, optional): Node where the flow ends. Defaults to None.
            start (int, optional): Time step in which the flow started. Defaults to 0.
            path (list, optional): Network path used to pass the flow over the list of
              network nodes. Defaults to [].
            data_to_transfer (int, optional): Amount of data transferred by the self.
              Defaults to 0.
            metadata (dict, optional): Custom flow metadata. Defaults to {}.
        """
        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

        # Object's class instance ID
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Reference to the network topology object
        self.topology = topology

        # Flow status. Valid options: "active" (default) and "finished"
        self.status = status

        # Network nodes and path used by the flow
        self.source = source
        self.target = target
        self.path = path

        # Network capacity available to the flow
        self.bandwidth = {}
        self.last_updated_bandwidth = {}

        # Temporal information about the flow
        self.start = start
        self.end = None

        # Amount of data transferred by the flow
        self.data_to_transfer = data_to_transfer

        # Custom flow metadata
        self.metadata = metadata

        # Adding a reference to the flow inside the network links that comprehend the
        # "path" attribute
        for i in range(0, len(path) - 1):
            link = self.topology[path[i]][path[i + 1]]
            link["active_flows"].append(self)
            self.bandwidth[link["id"]] = None
            self.last_updated_bandwidth[link["id"]] = None

        # Model-specific attributes (defined inside the model's "initialize()" method)
        self.model = None
        self.unique_id = None

    def _to_dict(self) -> dict:
        """Method that overrides the way the object is formatted to JSON."

        Returns:
            dict: JSON-friendly representation of the object as a dictionary.
        """
        dictionary = {
            "id": self.id,
            "status": self.status,
            "nodes": [
                {"type": type(node).__name__, "id": node.id} for node in self.nodes
            ],
            "path": self.path,
            "start": self.start,
            "end": self.end,
            "data_to_transfer": self.data_to_transfer,
            "bandwidth": self.bandwidth,
            "metadata": self.metadata,
        }
        return dictionary

    def collect(self) -> dict:
        """Method that collects a set of metrics for the object.

        Returns:
            metrics (dict): Object metrics.
        """
        bw = list(self.bandwidth.values())
        actual_bw = (
            min(bw)
            if len([bw for bw in self.bandwidth.values() if bw is None]) == 0
            else None
        )

        if self.metadata["type"] == "layer":
            object_being_transferred = (
                f"{str(self.metadata['object'])}"
                f" ({self.metadata['object'].instruction})"
            )
        else:
            object_being_transferred = str(self.metadata["object"])

        metrics = {
            "Instance ID": self.id,
            "Object being Transferred": object_being_transferred,
            "Object Type": self.metadata["type"],
            "Start": self.start,
            "End": self.end,
            "Source": self.source.id if self.source else None,
            "Target": self.target.id if self.target else None,
            "Path": [node.id for node in self.path],
            "Links Bandwidth": bw,
            "Actual Bandwidth": actual_bw,
            "Status": self.status,
            "Data to Transfer": self.data_to_transfer,
        }
        return metrics

    def step(self):
        """Method that executes the events involving the object at each time step."""
        if self.status == "active":
            # Updating the flow progress according to the available bandwidth
            if not any([bw is None for bw in self.bandwidth.values()]):
                self.data_to_transfer -= min(self.bandwidth.values())

            if self.data_to_transfer <= 0:
                # Updating the completed flow's properties
                self.data_to_transfer = 0

                # Storing the current step as when the flow ended
                self.end = self.model.schedule.steps + 1

                # Updating the flow status to "finished"
                self.status = "finished"

                # Releasing links used by the completed flow
                for i in range(0, len(self.path) - 1):
                    link = self.model.topology[self.path[i]][self.path[i + 1]]
                    link["active_flows"].remove(self)

                # When container layer flows finish: Adds the container layer to its
                # target host
                if self.metadata["type"] == "layer":
                    # Removing the flow from its target host's download queue
                    self.target.download_queue.remove(self)

                    # Adding the layer to its target host
                    layer = self.metadata["object"]
                    layer.server = self.target
                    self.target.container_layers.append(layer)

                # When service state flows finish: change the service migration status
                elif self.metadata["type"] == "service_state":
                    service = self.metadata["object"]
                    service._migrations[-1]["status"] = "finished"
