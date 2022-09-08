def get_overprovisioned_slices(demands: list, allocated: list) -> list:
    """Calculates the leftover demand and finds items with satisfied bandwidth.
    Args:
        demands (list): List of demands (or the demand of services that will be migrated).
        allocated (list): Allocated demand for each service within the list.
    Returns:
        list, int: Flows that were overprovisioned and their leftover bandwidth, respectively.
    """
    overprovisioned_slices = []
    leftover_bandwidth = 0

    for i in range(len(demands)):
        if allocated[i] >= demands[i]:
            leftover_bandwidth += allocated[i] - demands[i]
            overprovisioned_slices.append(demands[i])

    return overprovisioned_slices, leftover_bandwidth


def max_min_fairness(topology: object, flows: list):
    """Manages the execution of the Max-Min Fairness algorithm for sharing the bandwidth of links among network flows.

    Args:
        topology (object): Network topology object.
        flows (list): List of flows in the topology.
    """
    # Gathering the links of used by flows that either started or finished or that have more bandwidth than needed
    links_to_recalculate_bandwidth = []
    for flow in flows:
        flow_just_started = len([bw for bw in flow.bandwidth.values() if bw == None]) > 0
        flow_just_ended = flow.data_to_transfer == 0
        flow_wasting_bandwidth = (
            False if flow_just_started else any([flow.data_to_transfer < bw for bw in flow.bandwidth.values()])
        )

        if flow_just_started or flow_just_ended or flow_wasting_bandwidth:
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
            bw_shares = calculate_fair_allocation(capacity=link["bandwidth"], demands=flow_demands)

            for index, affected_flow in enumerate(link["active_flows"]):
                affected_flow.bandwidth[link["id"]] = bw_shares[index]


def calculate_fair_allocation(capacity: int, demands: list) -> list:
    """Calculates network shares using the Max-Min Fairness algorithm [1].

    [1] Gebali, F. (2008). Scheduling Algorithms. In: Analysis of Computer and Communication
    Networks. Springer, Boston, MA. https://doi.org/10.1007/978-0-387-74437-7_12.

    Args:
        capacity (int): Network bandwidth to be shared.
        demands (list): List of demands (e.g.: list of demands of services that will be migrated).

    Returns:
        list: Fair network allocation scheme.
    """
    # Giving an equal slice of bandwidth to each item in the demands list
    allocated_bandwidth = [capacity / len(demands)] * len(demands)

    # Calculating leftover demand and gathering items with satisfied bandwidth
    fullfilled_items, leftover_bandwidth = get_overprovisioned_slices(demands=demands, allocated=allocated_bandwidth)

    while leftover_bandwidth > 0 and len(fullfilled_items) < len(demands):
        bandwidth_to_share = leftover_bandwidth / (len(demands) - len(fullfilled_items))

        for index, demand in enumerate(demands):
            if demand in fullfilled_items:
                # Removing overprovisioned bandwidth
                allocated_bandwidth[index] = demand
            else:
                # Giving a larger slice of bandwidth to items that are not fullfilled
                allocated_bandwidth[index] += bandwidth_to_share

        # Recalculating leftover demand and gathering items with satisfied bandwidth
        fullfilled_items, leftover_bandwidth = get_overprovisioned_slices(demands=demands, allocated=allocated_bandwidth)

    return allocated_bandwidth
