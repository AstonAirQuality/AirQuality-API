import datetime as dt
from abc import ABC, abstractmethod


class SensorFactory(ABC):
    @abstractmethod
    def get_sensors(self, start: dt.datetime, end: dt.datetime, *args, **kwargs):
        """Factory method for creating sensor objects by fetching data from their sensor type's respective API."""
        ...
