# dependacies
# csv data fetch
import csv
import io
from typing import Any, List

import pandas as pd

from api_wrappers.Sensor_DTO import SensorDTO


class PlumeSensor(SensorDTO):
    """Per sensor object designed to wrap the csv files returned by the Plume API.
    Extends the SensorDTO class.
    :param SensorDTO: SensorDTO class to inherit from.
    """

    def __init__(self, id_, dataframe: pd.DataFrame):
        """Initializes the PlumeSensor object.
        :param id_: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(id_, dataframe)

    def join_dataframes(self, mdf):
        """Combines the measurement dataframe with the existing dataframe.
        :param mdf: The measurement dataframe."""
        self.df = pd.concat([self.df, mdf], axis=1)

        # drop rows where there is no measurement data
        self.df = self.df[self.df["timestamp"].notna()]

        # covert datatypes to correct types
        self.df["timestamp"] = self.df["timestamp"].astype(int)

        # sort indexes
        self.df.sort_index(inplace=True)

    # measurement data
    def add_measurements_json(self, data: list):
        """Extracts the measurement data from the Plume API JSON and adds it to the dataframe.
        :param data: The Plume API JSON data."""
        try:
            dfList = []

            for measurements in data[0]:
                temp_df = pd.DataFrame([measurements])
                dfList.append(temp_df)

            # concatenate all dataframes and prepare dataframe. Ignore index to keep the original index.
            df = pd.concat(dfList, ignore_index=True)
            df = PlumeSensor.prepare_measurements(df)
            self.join_dataframes(df)

        except (IndexError, ValueError):
            # print("No data found for sensor: {}".format(sensor_id))
            return

    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe for merging with the locations dataframe and renames columns to match other sensor platform types.
        :param df: The measurement dataframe.
        :return: The prepared measurement dataframe."""

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
        df["date"] = df["date"].dt.floor("Min")  # used to match datetime of measurement data to the datetime of location data
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
        # keeps only the median values of the location data (there are multiple values for each minute)
        df = df.rolling("1Min").median().loc[~df.index.duplicated(keep="last")]
        df.drop(["timestamp"], axis=1, inplace=True)

        # drop all null rows with no location data
        df = df[df["latitude"].notna()]

        if df.empty:
            return None
        else:
            return PlumeSensor(sensor_id, df)

    @staticmethod
    def from_zip(sensor_id: str, csv_file: io.StringIO) -> Any:
        """Factory method builds PlumeSensor from  file like object
        containing location csv data.
        :param sensor_id: id number of sensor
        :param csv_file: csv file like object
        :return:
        """
        # NOTE: merged csv does not contain pm1?
        df = pd.read_csv(csv_file, dialect=csv.unix_dialect)

        if df.empty:
            return None

        else:
            df = df.rename(
                columns={
                    "date (UTC)": "date",
                    "NO2 (ppb)": "NO2",
                    "VOC (ppb)": "VOC",
                    "pm 1 (ug/m3)": "particulatePM1",
                    "pm 10 (ug/m3)": "particulatePM10",
                    "pm25 (ug/m3)": "particulatePM2.5",  # There is a typo in the csv file
                },
            )

            for col in df.columns:
                if "(Plume AQI)" in col:
                    df.drop(col, axis=1, inplace=True)

            df.set_index("date", inplace=True)

            return PlumeSensor(sensor_id, df)
