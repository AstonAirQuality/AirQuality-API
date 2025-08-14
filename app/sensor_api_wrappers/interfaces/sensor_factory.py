import datetime as dt
from abc import ABC, abstractmethod
from typing import Iterator

from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable

# from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class SensorFactory(ABC):
    @abstractmethod
    def get_sensors(self, start: dt.datetime, end: dt.datetime, *args, **kwargs) -> Iterator[SensorWritable]:
        """Factory method for creating sensor objects by fetching data from their sensor type's respective API."""
        ...
