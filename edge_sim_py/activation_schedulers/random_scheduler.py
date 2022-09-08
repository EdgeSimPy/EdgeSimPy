""" Contains an agent activation scheduler inspired on Mesa's Base Scheduler."""
# EdgeSimPy components
from edge_sim_py.components import *

# Mesa modules
from mesa.time import BaseScheduler as MesaBaseScheduler

# Python libraries
import random


def was_activated(agent, current_step):
    return hasattr(agent, "last_activation") and agent.last_activation == current_step


class RandomScheduler(MesaBaseScheduler):
    """Class responsible for scheduling the events that take place at each step of the simulation model. This scheduler is based
    on Mesa's RandomActivation. It activates each agent once per step, in random order, with the order reshuffled every step. This
    is equivalent to the NetLogo 'ask agents...' and is generally the default behavior for an ABM.
    """

    def step(self) -> None:
        """Defines what happens at each step of the simulation model."""
        agents = list(self._agents.values())
        agents = random.sample(agents, len(agents))

        while any([not was_activated(agent, self.steps) for agent in agents]):
            agent = next((agent for agent in agents if not was_activated(agent, self.steps)), None)
            agent.last_activation = self.steps

            agent.step()

            agents = list(self._agents.values())
            agents = random.sample(agents, len(agents))

        # Advancing simulation
        self.steps += 1
        self.time += 1
