""" Contains a method that defines initial placement of services based on a Random-Fit heuristic."""
# EdgeSimPy components
from edge_sim_py.components.edge_server import EdgeServer
from edge_sim_py.components.container_layer import ContainerLayer
from edge_sim_py.components.service import Service
from edge_sim_py.components.user import User

# Python libraries
from random import sample


def random_fit_services():
    """Allocates services based on the Random-Fit heuristic procedure. Random Fit randomly sorts edge servers
    and then starts looking for edge servers with enough available resources to host the services.

    Args:
        services (list): Services that must be accommodated inside the edge servers.
        hosts (list): Edge servers that must accommodate the services.
    """
    for service in Service.all():
        # Shuffling the list of edge servers
        edge_servers = sample(EdgeServer.all(), EdgeServer.count())

        for edge_server in edge_servers:
            # Checking if the host would have resources to host the service and its (additional) layers
            if edge_server.has_capacity_to_host(service=service):
                # Updating the host's resource usage
                edge_server.cpu_demand += service.cpu_demand
                edge_server.memory_demand += service.memory_demand

                # Creating relationship between the host and the registry
                service.server = edge_server
                edge_server.services.append(service)

                for layer_metadata in edge_server._get_uncached_layers(service=service):
                    layer = ContainerLayer(
                        digest=layer_metadata.digest,
                        size=layer_metadata.size,
                        instruction=layer_metadata.instruction,
                    )

                    # Updating host's resource usage based on the layer size
                    edge_server.disk_demand += layer.size

                    # Creating relationship between the host and the layer
                    layer.server = edge_server
                    edge_server.container_layers.append(layer)

                break

    # Calculating user communication paths and application delays
    for user in User.all():
        for application in user.applications:
            user.set_communication_path(app=application)
