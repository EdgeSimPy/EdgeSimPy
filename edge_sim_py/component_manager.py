""" Adds helper methods to class objects that ease manipulation.

Example:
    'Application.first()' allows you to get the first instance from Application class.
    'User.count()' allows you to get the number of created instances from class User.
    'Service.find_by_id(3)' allows you to find the Service object that has id attribute = 3
"""
# Python libraries
import json


class ComponentManager:
    """This class provides auxiliary methods that facilitate object manipulation."""

    __model = None

    def __str__(self) -> str:
        """Defines how the object is represented inside print statements.

        Returns:
            obj (str): Object representation
        """
        return f"{self.__class__.__name__}_{self.id}"

    def __repr__(self) -> str:
        """Defines how the object is represented inside the console.

        Returns:
            str: Object representation.
        """
        return f"{self.__class__.__name__}_{self.id}"

    @classmethod
    def export_scenario(
        cls, ignore_list: list = ["Simulator", "Topology", "NetworkFlow"], save_to_file: bool = False, file_name: str = "dataset"
    ) -> dict:
        """Exports metadata about the simulation model to a Python dictionary. If the "save_to_file" attribute is set to True, the
        external dataset file generated is saved inside the "datasets/" directory by default.

        Args:
            ignore_list (list, optional): List of entities that will not be included in the output dict. Defaults to ["Simulator", "Topology", "NetworkFlow"].
            save_to_file (bool, optional): Attribute that tells the method if it needs to save the scenario to an external file. Defaults to False.
            file_name (str, optional): Output file name. Defaults to "dataset".

        Returns:
            scenario (dict): Python dictionary representing the simulation model.
        """
        scenario = {}

        for component in ComponentManager.__subclasses__():
            if component.__name__ not in ignore_list:
                scenario[component.__name__] = [instance._to_dict() for instance in component._instances]
                with open(f"datasets/{file_name}.json", "w", encoding="UTF-8") as output_file:
                    json.dump(scenario, output_file, indent=4)

        return scenario

    @classmethod
    def _from_dict(cls, dictionary: dict) -> object:
        """Method that creates an object based on a dictionary specification.

        Args:
            dictionary (dict): Object specification.

        Returns:
            created_object (object): Object created from the dictionary specification.
        """
        created_object = cls()
        for attribute, value in dictionary.items():
            setattr(created_object, attribute, value)

        return created_object

    @classmethod
    def find_by(cls, attribute_name: str, attribute_value: object) -> object:
        """Finds objects from a given class based on an user-specified attribute.

        Args:
            attribute_name (str): Attribute name.
            attribute_value (object): Attribute value.

        Returns:
            object: Class object.
        """
        class_object = next((obj for obj in cls._instances if getattr(obj, attribute_name) == attribute_value), None)
        return class_object

    @classmethod
    def find_by_id(cls, obj_id: int) -> object:
        """Finds a class object based on its ID attribute.

        Args:
            obj_id (int): Object ID.

        Returns:
            class_object (object): Class object found.
        """
        class_object = next((obj for obj in cls._instances if obj.id == obj_id), None)
        return class_object

    @classmethod
    def all(cls) -> list:
        """Returns the list of created objects of a given class.

        Returns:
            list: List of objects from a given class.
        """
        return cls._instances

    @classmethod
    def first(cls) -> object:
        """Returns the first object within the list of instances from a given class.

        Returns:
            object: Class object.
        """
        if len(cls._instances) == 0:
            return None

        return cls._instances[0]

    @classmethod
    def last(cls) -> object:
        """Returns the last object within the list of instances from a given class.

        Returns:
            object: Class object.
        """
        return cls._instances[-1]

    @classmethod
    def count(cls) -> int:
        """Returns the number of instances from a given class.

        Returns:
            int: Number of instances from a given class.
        """
        return len(cls._instances)

    @classmethod
    def remove(cls, obj: object):
        """Removes an object from the list of instances of a given class.

        Args:
            obj (object): Object to be removed.
        """
        if obj not in cls._instances:
            raise Exception(f"Object {obj} is not in the list of instances of the '{cls.__name__}' class.")

        cls._instances.remove(obj)
