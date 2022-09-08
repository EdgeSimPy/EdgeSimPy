""" Contains an agent activation scheduler inspired on Mesa's Base Scheduler."""
# EdgeSimPy components
from edge_sim_py.components import *

# Mesa modules
from mesa.time import BaseScheduler as MesaBaseScheduler


def was_activated(agent, current_step):
    return hasattr(agent, "last_activation") and agent.last_activation == current_step


class BaseScheduler(MesaBaseScheduler):
    """Class responsible for scheduling the events that take place at each step of the simulation model. This scheduler
    is based on Mesa's BaseScheduler. It activates agents one at a time, in the order they were added. This is explicitly
    meant to replicate the scheduler in MASON"""

    def step(self) -> None:
        """Defines what happens at each step of the simulation model."""
        while any([not was_activated(agent, self.steps) for agent in list(self._agents.values())]):
            agent = next((agent for agent in list(self._agents.values()) if not was_activated(agent, self.steps)), None)
            agent.last_activation = self.steps

            agent.step()

        # Advancing simulation
        self.steps += 1
        self.time += 1
