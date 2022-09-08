"""Contains a function that creates network switch objects with the power specifications provided in [1].

[1] Conterato, Marcelo da Silva, et al. "Reducing energy consumption in SDN-based data center
    networks through flow consolidation strategies." ACM/SIGAPP Symposium on Applied Computing. 2019.
"""
# EdgeSimPy components
from edge_sim_py.components.network_switch import NetworkSwitch
from edge_sim_py.components.power_models.network.conterato_network_power_model import ConteratoNetworkPowerModel


def sample_switch() -> object:
    """Creates network switch objects based on the power parameters provided in [1].

    Returns:
        network_switch (object): Created network switch object.
    """
    # Creating the network switch object
    network_switch = NetworkSwitch()

    # Assigning power-related properties to the network switch
    network_switch.power_model = ConteratoNetworkPowerModel
    network_switch.power_model_parameters = {"chassis_power": 60, "ports_power_consumption": {"125": 1, "12.5": 0.3}}

    return network_switch
