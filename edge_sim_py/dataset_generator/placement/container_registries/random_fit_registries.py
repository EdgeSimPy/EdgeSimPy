""" Contains a method that randomly defines the initial placement of container registries."""
# EdgeSimPy component builder helpers
from edge_sim_py.dataset_generator.builder_helpers import provision_container_registry

# Python libraries
from random import sample


def random_fit_registries(container_registry_specifications: list, servers: list):
    """Provisions container registries on random hosts with enough resources."""
    # Randomly sorting the list of servers
    servers = sample(servers, len(servers))

    for registry in container_registry_specifications:
        for edge_server in servers:
            # Gathering the list of layers from the registry that are not present in the edge server
            new_layers = [
                layer
                for layer in registry["layers"]
                if not any(layer["digest"] == l.digest for l in edge_server.container_layers)
            ]

            # Calculating the amount of disk resources required by all container layers not present in the edge server's disk
            cpu_demand = registry["cpu_demand"]
            memory_demand = registry["memory_demand"]
            additional_disk_demand = sum([layer["size"] for layer in new_layers])

            free_cpu = edge_server.cpu - edge_server.cpu_demand
            free_memory = edge_server.memory - edge_server.memory_demand
            free_disk = edge_server.disk - edge_server.disk_demand

            # Provisioning the container registry in the host if the host has enough resources to host it
            if free_cpu >= cpu_demand and free_memory >= memory_demand and free_disk >= additional_disk_demand:
                provision_container_registry(container_registry_specification=registry, server=edge_server)
                break
