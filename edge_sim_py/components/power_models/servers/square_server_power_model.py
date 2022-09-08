""" Contains a server power model definition."""


class SquareServerPowerModel:
    """Server power model proposed in [1], which assumes a squared correlation between a server's power consumption and demand.

    [1] Anton Beloglazov, and Rajkumar Buyya, "Optimal Online Deterministic Algorithms and Adaptive Heuristics for Energy and
    Performance Efficient Dynamic Consolidation of Virtual Machines in Cloud Data Centers", Concurrency and Computation: Practice
    and Experience (CCPE), Volume 24, Issue 13, Pages: 1397-1420, John Wiley & Sons, Ltd, New York, USA, 2012
    """

    @classmethod
    def get_power_consumption(cls, device: object) -> float:
        """Gets the power consumption of a server.

        Args:
            device (object): Server whose power consumption will be computed.

        Returns:
            power_consumption (float): Server's power consumption.
        """
        if device.active:
            static_power = (
                device.power_model_parameters["static_power_percentage"] * device.power_model_parameters["max_power_consumption"]
            )
            constant = (device.power_model_parameters["max_power_consumption"] - static_power) / 100

            demand = device.cpu_demand
            capacity = device.cpu
            utilization = demand / capacity

            power_consumption = static_power + constant * (utilization * 100) ** 2
        else:
            power_consumption = 0

        return power_consumption
