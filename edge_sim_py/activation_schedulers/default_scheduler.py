""" Contains the EdgeSimPy's default agent activation scheduler."""
# EdgeSimPy components
from edge_sim_py.components import *

# Mesa modules
from mesa.time import BaseScheduler as MesaBaseScheduler


class DefaultScheduler(MesaBaseScheduler):
    """Class responsible for scheduling the events that take place at each step of the simulation model."""

    def step(self) -> None:
        """Defines what happens at each step of the simulation model.

        Activation Order:
            - Edge Servers
                - Download queue
                - Useless container layers

            - Network Flows
                - Progress and status update

            - Services
                - Migration status update

            - Container Registries
                - Migration (provisioning) status update

            - Users
                - Mobility
                - Handoff

            - Other Agents that have no built-in activation procedures
                - Network Switches
                - Network Links
                - Base Stations
                - Container Layers
                - Container Images
                - Container Registries
                - Applications
        """
        for agent in EdgeServer.all():
            agent.step()

        for agent in Service.all():
            agent.step()

        for agent in Topology.all():
            agent.step()

        for agent in NetworkFlow.all():
            agent.step()

        for agent in User.all():
            agent.step()

        for agent in ContainerRegistry.all():
            agent.step()

        other_agents = (
            NetworkSwitch.all()
            + NetworkLink.all()
            + BaseStation.all()
            + ContainerLayer.all()
            + ContainerImage.all()
            + Application.all()
        )
        for agent in other_agents:
            agent.step()

        # Advancing simulation
        self.steps += 1
        self.time += 1
