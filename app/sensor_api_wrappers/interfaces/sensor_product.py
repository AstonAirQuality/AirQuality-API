from abc import ABC, abstractmethod


# Interface for sensor products
class SensorProduct(ABC):
    @abstractmethod
    def from_json(self, sensor_id: str, *args, **kwargs):
        """Create a sensor product from a json object"""
        ...

    @abstractmethod
    def from_csv(self, sensor_id: str, *args, **kwargs):
        """Create a sensor product from a csv object"""
        ...
