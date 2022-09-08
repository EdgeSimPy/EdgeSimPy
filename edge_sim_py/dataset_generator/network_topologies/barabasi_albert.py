"""Contains a method that creates a network topology according to the Barabási-Albert model [1].

[1] Barabási, Albert-László, and Réka Albert. "Emergence of scaling in random networks." Science (1999): 509-512.
"""
# EdgeSimPy components
from edge_sim_py.components.topology import Topology
from edge_sim_py.components.network_link import NetworkLink

# Python libraries
import random
import networkx as nx


def barabasi_albert(network_nodes: list, link_specifications: list = [], min_links_per_node: int = 1, seed: int = 1) -> object:
    """Creates a network topology according to the Barabási-Albert model.

    Args:
        network_nodes (list): List of network nodes that will compose the network topology.
        link_specifications (list): List of specifications for the network links.
        min_links_per_node (int, optional): Minimum number of links connecting each node in the topology. Defaults to 1.
        seed (int, optional): Seed value used when randomly generating links between the network nodes. Defaults to 1.

    Returns:
        topology (object): Created topology
    """
    # Creating the network topology using the NetworkX's generator function
    topology = nx.barabasi_albert_graph(n=len(network_nodes), m=min_links_per_node, seed=seed)

    # Replacing network nodes (int values by default) with user-specified objects
    topology = nx.relabel_nodes(topology, dict(zip(topology.nodes(), network_nodes)))

    # Creating a topology object from the default NetworkX graph object
    topology = Topology(existing_graph=topology)

    # Checking if the number of link specifications is equal to the number of links in the network topology
    if len(link_specifications) > 0 and sum([spec["number_of_objects"] for spec in link_specifications]) != len(topology.edges()):
        raise Exception(
            f"You must specify the properties for {len(topology.edges())} links or ignore the 'link_specifications' parameter."
        )

    # Replacing default NetworkX links with NetworkLink objects
    for link in topology.edges(data=True):
        link_object = NetworkLink()
        link_object.topology = topology

        # List of network nodes connected by the link
        link_object.nodes = [link[0], link[1]]

        # Replacing NetworkX's default link dictionary with the NetworkLink object
        topology._adj[link[0]][link[1]] = link_object
        topology._adj[link[1]][link[0]] = link_object

    # Applying the user-specified attributes to the network links
    links = (link for link in random.sample(NetworkLink.all(), NetworkLink.count()))
    for spec in link_specifications:
        for _ in range(spec["number_of_objects"]):
            link = next(links)
            for key, value in spec.items():
                if key != "number_of_objects":
                    link[key] = value

    return topology
