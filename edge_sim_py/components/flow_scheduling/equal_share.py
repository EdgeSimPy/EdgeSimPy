def equal_share(topology: object, flows: list):
    """Manages the execution of a equal bandwidth share algorithm for network flows.

    Args:
        topology (object): Network topology object.
        flows (list): List of flows in the topology.
    """
    # Gathering the links of used by flows that either started or finished or that have more bandwidth than needed
    links_to_recalculate_bandwidth = []
    for flow in flows:
        flow_just_started = len([bw for bw in flow.bandwidth.values() if bw == None]) > 0
        flow_just_ended = flow.data_to_transfer == 0

        if flow_just_started or flow_just_ended:
            for i in range(0, len(flow.path) - 1):
                # Gathering link nodes
                link = (flow.path[i], flow.path[i + 1])

                # Checking if the link is not already included in "links_to_recalculate_bandwidth"
                if link not in links_to_recalculate_bandwidth:
                    links_to_recalculate_bandwidth.append(link)

    # Calculating the bandwidth shares for the active flows
    for link_nodes in links_to_recalculate_bandwidth:
        link = topology[link_nodes[0]][link_nodes[1]]

        # Recalculating bandwidth shares for the flows as some of them have changed
        flow_demands = [f.data_to_transfer for f in link["active_flows"]]
        if sum(flow_demands) > 0:
            bw_shares = calculate_bandwidth_allocation(capacity=link["bandwidth"], demands=flow_demands)

            for index, affected_flow in enumerate(link["active_flows"]):
                affected_flow.bandwidth[link["id"]] = bw_shares[index]


def calculate_bandwidth_allocation(capacity: int, demands: list) -> list:
    """Calculates network shares using the simple notion of equal sharing, where the allocated bandwidth
    for each flow is equal to the available bandwidth divided by the number of active flows.

    Args:
        capacity (int): Network bandwidth to be shared.
        demands (list): List of demands (e.g.: list of demands of services that will be migrated).

    Returns:
        list: Network allocation scheme.
    """
    # Giving a equal slice of bandwidth to each item in the demands list
    allocated_bandwidth = [capacity / len(demands)] * len(demands)

    return allocated_bandwidth
