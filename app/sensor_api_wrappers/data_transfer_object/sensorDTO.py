from abc import ABC, abstractmethod

import pandas as pd


class SensorDTO(ABC):
    def __init__(self, id_, merged_df: pd.DataFrame):
        """Initialises the SensorDTO object
        :param id_: sensor id
        :param merged_df: dataframe of sensor data"""
        self.id = id_
        self.df = merged_df

    def __iter__(self):
        """Iterator for the SensorDTO object
        :return: a tuple of the sensor id and the sensor summary"""
        return iter((self.id, self.df))
