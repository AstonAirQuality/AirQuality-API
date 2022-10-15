import abc
import datetime as dt

import pandas as pd


class BaseWrapper(abc.ABC):

    # @abc.abstractmethod
    # def get_sensor_ids(self, *args, **kwargs) -> Iterable[str]:
    #     ...

    @abc.abstractmethod
    def get_sensors(self, start: dt.datetime, end: dt.datetime, *args, **kwargs):
        ...
