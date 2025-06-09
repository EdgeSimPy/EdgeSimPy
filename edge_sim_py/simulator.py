""" Contains all the simulation management functionality."""
# EdgeSimPy components
from edge_sim_py.component_manager import ComponentManager
from edge_sim_py.components import *
from edge_sim_py.activation_schedulers import *

# Mesa modules
from mesa import Model, Agent

# Python libraries
import os
import json
import msgpack
from typing import Callable
from datetime import timedelta
from urllib.parse import urlparse
from urllib.request import urlopen

SUPPORTED_TIME_UNITS = ["seconds", "microseconds", "milliseconds", "minutes"]


class Simulator(ComponentManager, Model):
    """Class responsible for managing the simulation."""

    # Class attributes that allow this class to use helper methods from ComponentManager
    _instances = []
    _object_count = 0

    def __init__(
        self,
        stopping_criterion: Callable = None,
        resource_management_algorithm: Callable = None,
        resource_management_algorithm_parameters: dict = {},
        user_defined_functions: list = [],
        network_flow_scheduling_algorithm: Callable = max_min_fairness,
        tick_duration: int = 1,
        tick_unit: str = "seconds",
        obj_id: int = None,
        scheduler: Callable = DefaultScheduler,
        dump_interval: int = 100,
        logs_directory: str = "logs",
    ) -> object:
        """Creates a Simulator object.

        Args:
            stopping_criterion (Callable, optional): Simulation stopping criterion. Defaults to None.
            resource_management_algorithm (Callable, optional): Main resource management algorithm executed at each step of the simulation. Defaults to None.
            resource_management_algorithm_parameters (dict, optional): User-defined parameters. Defaults to {}.
            user_defined_functions (list, optional): List of user-defined functions.
            network_flow_scheduling_algorithm (Callable, optional): Bandwidth sharing algorithm. Defaults to equal_share.
            obj_id (int, optional): Object identifier. Defaults to None.
            scheduler (Callable, optional): Agent activation scheduler regime.
            dump_interval (int, optional): Interval (in time steps) between each time EdgeSimPy dumps simulation data to disk.
            logs_directory (str, optional): Name of the directory where the simulation logs will be stored.

        Returns:
            object: Created Simulator object.
        """
        # Object identifier
        self.__class__._object_count += 1
        if obj_id is None:
            obj_id = self.__class__._object_count
        self.id = obj_id

        # Calling the Model class constructor
        Model.__init__(self)

        # Defining the simulation clock tick granularity
        if tick_unit not in SUPPORTED_TIME_UNITS:
            raise Exception(f"Unsupported tick unit {tick_unit}. Supported tick units are {SUPPORTED_TIME_UNITS}.")

        seconds = 0 + tick_duration if tick_unit == "seconds" else 0
        microseconds = 0 + tick_duration if tick_unit == "microseconds" else 0
        milliseconds = 0 + tick_duration if tick_unit == "milliseconds" else 0
        minutes = 0 + tick_duration if tick_unit == "minutes" else 0

        if seconds + microseconds + milliseconds + minutes == 0:
            raise Exception("Tick duration attribute must be greater than zero.")

        self.tick_duration = timedelta(
            seconds=seconds, microseconds=microseconds, milliseconds=milliseconds, minutes=minutes
        ).total_seconds()

        # Simulation metrics
        self.model_metrics = {}
        self.agent_metrics = {}

        # Defining the model schedule
        self.schedule = scheduler(self)

        # Resource management algorithm
        self.resource_management_algorithm = resource_management_algorithm
        self.resource_management_algorithm_parameters = resource_management_algorithm_parameters
        self.resource_management_algorithm_parameters["current_step"] = self.schedule.steps + 1

        # User-defined functions (e.g., user mobility models)
        self.user_defined_functions = user_defined_functions
        for function in self.user_defined_functions:
            globals()[function.__name__] = function

        # Function that determines when the simulation must end
        self.stopping_criterion = stopping_criterion

        # Function that manages how network bandwidth is shared among concurrent flows
        self.network_flow_scheduling_algorithm = network_flow_scheduling_algorithm

        # Attributes that EdgeSimPy uses to know when to dump simulation metrics into the disk
        self.last_dump = 0
        self.dump_interval = dump_interval
        self.logs_directory = logs_directory

        # Attribute that stores the network topology used during the simulation
        self.topology = None

        # Storing a reference to the Simulator object inside the ComponentManager class
        ComponentManager._ComponentManager__model = self

        # Adding the new object to the list of instances of its class
        self.__class__._instances.append(self)

    def initialize(self, input_file: str) -> None:
        """Sets up the initial values for state variables, which includes, e.g., loading components from a dataset file.

        Args:
            input_file (str): Dataset file (URL for external JSON file, path for local JSON file, Python dictionary).
        """
        # Resetting the list of instances of EdgeSimPy's component classes
        for component_class in ComponentManager.__subclasses__():
            if component_class.__name__ != "Simulator":
                component_class._object_count = 0
                component_class._instances = []

        # Declaring an empty variable that will receive the dataset metadata (if user passes valid information)
        data = None

        # If "input_file" is a Python dictionary, no additional parsing is needed before starting loading the dataset
        if type(input_file) is dict:
            data = input_file

        # If "input_file" represents a valid URL, parses its response
        elif all([urlparse(input_file).scheme, urlparse(input_file).netloc]):
            data = json.loads(urlopen(input_file).read())

        # If "input_file" points to the local filesystem, checks if the file exists and parses it
        else:
            if os.path.exists(input_file):
                with open(input_file, "r", encoding="UTF-8") as read_file:
                    data = json.load(read_file)

            elif os.path.exists(f"{os.getcwd()}/{input_file}"):
                with open(f"{os.getcwd()}/{input_file}", "r", encoding="UTF-8") as read_file:
                    data = json.load(read_file)

        # Raising exception if the dataset could not be loaded based on the specified arguments
        if type(data) is not dict:
            raise TypeError("EdgeSimPy could not load the dataset based on the specified arguments.")

        # Creating simulator components based on the specified input data
        missing_keys = [key for key in data.keys() if key not in globals()]
        if len(missing_keys) > 0:
            raise Exception(f"\n\nCould not find component classes named: {missing_keys}. Please check your input file.\n\n")

        # Creating a list that will store all the relationships among components
        components = []

        # Creating the topology object and storing a reference to it as an attribute of the Simulator instance
        topology = self.initialize_agent(agent=Topology())
        self.topology = topology

        # Creating simulator components
        for key in data.keys():
            if key != "Simulator" and key != "Topology":
                for object_metadata in data[key]:
                    new_component = globals()[key]._from_dict(dictionary=object_metadata["attributes"])
                    new_component.relationships = object_metadata["relationships"]

                    if hasattr(new_component, "model") and hasattr(new_component, "unique_id"):
                        self.initialize_agent(agent=new_component)

                    components.append(new_component)

        # Defining relationships between components
        for component in components:
            for key, value in component.relationships.items():
                # Defining attributes referencing callables (i.e., functions and methods)
                if type(value) == str and value in globals():
                    setattr(component, f"{key}", globals()[value])

                # Defining attributes referencing lists of components (e.g., lists of edge servers, users, etc.)
                elif type(value) == list:
                    attribute_values = []
                    for item in value:
                        obj = (
                            globals()[item["class"]].find_by_id(item["id"])
                            if type(item) == dict and "class" in item and item["class"] in globals()
                            else None
                        )

                        if obj == None:
                            raise Exception(f"List relationship '{key}' of component {component} has an invalid item: {item}.")

                        attribute_values.append(obj)

                    setattr(component, f"{key}", attribute_values)

                # Defining attributes that reference a single component (e.g., an edge server, an user, etc.)
                elif type(value) == dict and "class" in value and "id" in value:
                    obj = (
                        globals()[value["class"]].find_by_id(value["id"])
                        if type(value) == dict and "class" in value and value["class"] in globals()
                        else None
                    )

                    if obj == None:
                        raise Exception(f"Relationship '{key}' of component {component} references an invalid object: {value}.")

                    setattr(component, f"{key}", obj)

                # Defining attributes that reference a a dictionary of components (e.g., {"1": {"class": "A", "id": 1}} )
                elif type(value) == dict and all(
                    type(entry) == dict and "class" in entry and "id" in entry for entry in value.values()
                ):
                    attribute = {}
                    for k, v in value.items():
                        obj = globals()[v["class"]].find_by_id(v["id"]) if "class" in v and v["class"] in globals() else None
                        if obj == None:
                            raise Exception(
                                f"Relationship '{key}' of component {component} references an invalid object: {value}."
                            )
                        attribute[k] = obj

                    setattr(component, f"{key}", attribute)

                # Defining "None" attributes
                elif value == None:
                    setattr(component, f"{key}", None)

                else:
                    raise Exception(f"Couldn't add the relationship {key} with value {value}. Please check your dataset.")

        # Filling the network topology
        for link in NetworkLink.all():
            # Adding the nodes connected by the link to the topology
            topology.add_node(link.nodes[0])
            topology.add_node(link.nodes[1])

            # Replacing NetworkX's default link dictionary with the NetworkLink object
            topology.add_edge(link.nodes[0], link.nodes[1])
            topology._adj[link.nodes[0]][link.nodes[1]] = link
            topology._adj[link.nodes[1]][link.nodes[0]] = link

    def run_model(self):
        """Executes the simulation."""
        if self.stopping_criterion == None:
            raise Exception("Please assign the 'stopping_criterion' attribute before starting the simulation.")

        if self.resource_management_algorithm == None:
            raise Exception("Please assign the 'resource_management_algorithm' attribute before starting the simulation.")

        # Calls the method that collects monitoring data about the agents
        self.monitor()

        while self.running:
            # Calls the method that advances the simulation time
            self.step()

            # Calls the method that collects monitoring data about the agents
            self.monitor()

            # Checks if the simulation should end according to the stop condition
            self.running = False if self.stopping_criterion(self) else True

        # Dumps simulation data to the disk to make sure no metrics are discarded
        self.dump_data_to_disk()

    def step(self):
        """Advances the model's system in one step."""
        # Running resource management algorithm
        self.resource_management_algorithm(parameters=self.resource_management_algorithm_parameters)

        # Activating agents
        self.schedule.step()

        # Updating the "current_step" attribute inside the resource management algorithm's parameters
        self.resource_management_algorithm_parameters["current_step"] = self.schedule.steps + 1

    def collect(self) -> dict:
        """Method that collects a set of model-level metrics.

        Returns:
            metrics (dict): Model-level metrics.
        """
        metrics = {}
        return metrics

    def monitor(self):
        """Monitors a set of metrics from the model and its agents."""
        # Collecting model-level metrics
        self.collect()

        # Collecting agent-level metrics
        for agent in self.schedule._agents.values():
            metrics = agent.collect()

            if metrics != {}:
                if f"{agent.__class__.__name__}" not in self.agent_metrics:
                    self.agent_metrics[f"{agent.__class__.__name__}"] = []

                metrics = {**{"Object": f"{agent}", "Time Step": self.schedule.steps}, **metrics}
                self.agent_metrics[f"{agent.__class__.__name__}"].append(metrics)

        if self.schedule.steps == self.last_dump + self.dump_interval:
            self.dump_data_to_disk()
            self.last_dump = self.schedule.steps

    def dump_data_to_disk(self, clean_data_in_memory: bool = True) -> None:
        """Dumps simulation metrics to the disk.

        Args:
            clean_data_in_memory (bool, optional): Purges the list of metrics stored in the memory. Defaults to True.
        """
        if self.dump_interval != float("inf"):
            if not os.path.exists(f"{self.logs_directory}/"):
                os.makedirs(f"{self.logs_directory}")

            for key, value in self.agent_metrics.items():
                with open(f"{self.logs_directory}/{key}.msgpack", "ab") as output_file:
                    output_file.write(msgpack.packb(value))

                if clean_data_in_memory:
                    self.agent_metrics[key] = []

    def initialize_agent(self, agent: object) -> object:
        """Initializes an agent object.

        Args:
            agent (object): Agent object.

        Returns:
            object: Initialized agent.
        """
        # Reference to the Simulator object
        agent.model = ComponentManager._ComponentManager__model

        # Agent unique ID
        agent.unique_id = agent.model.next_id()

        # Agent class constructor
        Agent.__init__(self=agent, unique_id=agent.unique_id, model=agent.model)

        # Adding the object to the list of agents of its model
        agent.model.schedule.add(agent)

        return agent
