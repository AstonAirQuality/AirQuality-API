# dependacies
# csv data fetch
import csv
import io
from typing import Any, List

import pandas as pd

from api_wrappers.Sensor_DTO import SensorDTO


class PlumeSensor(SensorDTO):
    """Per sensor object designed to wrap the csv files returned by the Plume API.

    Example Usage:
        ps = PlumeSensor.from_csv("16397", open("sensor_measures_20211004_20211008_1.csv"))
        print(ps.dataFrame)
    """

    def __init__(self, id_, dataframe: pd.DataFrame):
        super().__init__(id_, dataframe)

    def join_dataframes(self, mdf):
        """Combines the measurement dataframe with the existing dataframe."""
        self.df = pd.concat([self.df, mdf], axis=1)

        # drop rows where there is no measurement data
        self.df = self.df[self.df["timestamp"].notna()]

        # covert datatypes to correct types
        self.df["timestamp"] = self.df["timestamp"].astype(int)

        # sort indexes
        self.df.sort_index(inplace=True)

    # measurement data
    def add_measurements_json(self, data: list):
        """Extracts the measurement data from the Plume API JSON and adds it to the dataframe."""
        try:
            dfList = []

            for measurements in data[0]:
                temp_df = pd.DataFrame([measurements])
                dfList.append(temp_df)

            # concatenate all dataframes and prepare dataframe
            df = pd.concat(dfList, ignore_index=True)
            df = PlumeSensor.prepare_measurements(df)
            self.join_dataframes(df)

        except (IndexError, ValueError):
            # print("No data found for sensor: {}".format(sensor_id))
            return

    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe for use"""

        df.drop(["id"], axis=1, inplace=True)
        df.rename(
            columns={
                "date": "timestamp",
                "no2": "NO2",
                "voc": "VOC",
                "pm1": "particulatePM1",
                "pm10": "particulatePM10",
                "pm25": "particulatePM2.5",
            },
            inplace=True,
        )
        df.insert(0, "date", pd.to_datetime(df["timestamp"], unit="s"))
        df["date"] = df["date"].dt.floor("Min")
        df.set_index("date", drop=True, inplace=True)
        df = df.loc[~df.index.duplicated()]

        return df

    @staticmethod
    # measurement data
    def from_json(sensor_id: str, data: list) -> Any:
        """Factory method builds PlumeSensor from file like object
        containing measurement json data.
        :param sensor_id: id number of sensor
        :param data: List of lists containing measurement data
        :return:
        """
        dfList = []

        # print(data[0])
        try:
            for measurements in data[0]:
                temp_df = pd.DataFrame([measurements])
                dfList.append(temp_df)

            # concatenate all dataframes and prepare dataframe
            df = pd.concat(dfList, ignore_index=True)

        except (IndexError, ValueError):
            # print("No data found for sensor: {}".format(sensor_id))
            return None

        if df.empty:
            return None
        else:
            df = PlumeSensor.prepare_measurements(df)
            return PlumeSensor(sensor_id, df)

    @staticmethod
    def from_csv(sensor_id: str, csv_file: io.StringIO) -> Any:
        """Factory method builds PlumeSensor from file like object
        containing location csv data.
        :param sensor_id: id number of sensor
        :param csv_file: csv file like object
        :return:
        """

        df = pd.read_csv(csv_file, dialect=csv.unix_dialect)
        df["date"] = pd.to_datetime(df["date"]).dt.floor("Min")
        df.set_index("date", inplace=True)
        # keeps only the median values of the location data
        df = df.rolling("1Min").median().loc[~df.index.duplicated(keep="last")]
        df.drop(["timestamp"], axis=1, inplace=True)

        # drop all null rows with no location data
        df = df[df["latitude"].notna()]

        if df.empty:
            return None
        else:
            return PlumeSensor(sensor_id, df)
