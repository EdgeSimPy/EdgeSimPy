""" Contains a network switch power model definition."""


class ConteratoNetworkPowerModel:
    """Network switch power model proposed in [1], which considers the switch's chassis and its ports' bandwidth.

    [1] Conterato, Marcelo da Silva, et al. "Reducing energy consumption in SDN-based data center
    networks through flow consolidation strategies." ACM/SIGAPP Symposium on Applied Computing. 2019.
    """

    @classmethod
    def get_power_consumption(cls, device: object) -> float:
        """Gets the power consumption of a network switch.
        Args:
            device (object): Network switch whose power consumption will be computed.

        Returns:
            power_consumption (float): Network switch's power consumption.
        """
        # Calculating the power consumption of switch ports
        ports_power_consumption = 0
        for link in device.model.topology.edges(data=True, nbunch=device):
            port = link[2]
            if port.active:
                has_power_model_parameters = "ports_power_consumption" in device.power_model_parameters
                knows_port_power_consumption = f"{port.bandwidth}" in device.power_model_parameters["ports_power_consumption"]
                if has_power_model_parameters and knows_port_power_consumption:
                    ports_power_consumption += device.power_model_parameters["ports_power_consumption"][f"{port.bandwidth}"]
                else:
                    ports_power_consumption = None
                    break

        # Calculating the switch's power consumption
        if ports_power_consumption != None and "chassis_power" in device.power_model_parameters:
            power_consumption = device.power_model_parameters["chassis_power"] + ports_power_consumption
        else:
            power_consumption = None

        return power_consumption
