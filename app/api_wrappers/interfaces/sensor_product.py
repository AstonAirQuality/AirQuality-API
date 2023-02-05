from abc import ABC, abstractmethod


# Interface for sensor products
class SensorProduct(ABC):
    @abstractmethod
    def from_json(self, sensor_id: str, *args, **kwargs):
        """Get sensor data from the respective API."""
        ...

    @abstractmethod
    def from_csv(self, sensor_id: str, *args, **kwargs):
        """Get sensor data from the respective API."""
        ...
