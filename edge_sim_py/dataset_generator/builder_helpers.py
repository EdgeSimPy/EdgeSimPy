"""Contains a set of helper methods used when creating datasets for EdgeSimPy."""
# EdgeSimPy components
from edge_sim_py.components.container_registry import ContainerRegistry
from edge_sim_py.components.container_image import ContainerImage
from edge_sim_py.components.container_layer import ContainerLayer


def create_container_registries(container_image_specifications: list, container_registry_specifications: list) -> list:
    """Creates a list of dictionaries representing container registries based on user-informed specifications.
    The output list can used by container registry placement policies employed to create datasets for EdgeSimPy.

    Args:
        container_image_specifications (list): Container image specifications.
        container_registry_specifications (list): Container registry specifications.

    Returns:
        registries (list): Container registry specifications.
    """
    registries = []
    for spec in container_registry_specifications:
        for _ in range(spec["number_of_objects"]):
            # Creating dictionary with registry's metadata
            registry = dict(spec)

            # Removing keys that will not be turned into ContainerRegistry attributes
            del registry["number_of_objects"]

            # Creating key with container registry's image metadata
            images = []
            for image in registry["images"]:
                image = next(
                    (i for i in container_image_specifications if i["name"] == image["name"] and i["tag"] == image["tag"]), None
                )
                images.append(image)
            registry["images"] = images

            layers = []
            for img_spec in registry["images"]:
                for layer_spec in img_spec["layers"]:
                    if layer_spec not in layers:
                        layers.append(layer_spec)

            disk_demand = sum([layer_spec["size"] for layer_spec in layers])

            registry["layers"] = layers
            registry["disk_demand"] = disk_demand

            registries.append(registry)

    return registries


def provision_container_registry(container_registry_specification: dict, server: object) -> object:
    """Creates a container registry from a dictionary with technical specifications and provisions it inside a server object.

    Args:
        container_registry_specification (dict): Container registry specification.
        server (object): Server that will host the container registry.

    Returns:
        registry (object): Provisioned container registry.
    """
    # Creating registry object
    registry = ContainerRegistry(
        cpu_demand=container_registry_specification["cpu_demand"],
        memory_demand=container_registry_specification["memory_demand"],
    )

    # Creating relationship between the edge server and the registry
    registry.server = server
    server.container_registries.append(registry)

    # Updating the host's resource usage
    server.cpu_demand += registry.cpu_demand
    server.memory_demand += registry.memory_demand

    # Creating objects representing the images and their layers, now hosted by the chosen edge server
    for image_spec in container_registry_specification["images"]:
        image = ContainerImage()
        image.name = image_spec["name"] if "name" in image_spec else ""
        image.digest = image_spec["digest"] if "digest" in image_spec else ""
        image.tag = image_spec["tag"] if "tag" in image_spec else ""
        image.architecture = image_spec["architecture"] if "architecture" in image_spec else ""
        image.layers_digests = [layer["digest"] for layer in image_spec["layers"]]

        # Creating relationship between the edge server and the image
        image.server = server
        server.container_images.append(image)

    for layer_spec in container_registry_specification["layers"]:
        layer = ContainerLayer()
        layer.digest = layer_spec["digest"] if "digest" in layer_spec else None
        layer.size = int(layer_spec["size"]) if "size" in layer_spec else 0
        layer.instruction = layer_spec["instruction"] if "instruction" in layer_spec else ""

        # Updating edge server's resource usage based on the layer size
        server.disk_demand += layer.size

        # Creating relationship between the edge server and the layer
        layer.server = server
        server.container_layers.append(layer)
