# dependacies
# csv data fetch
import csv
import io
from typing import Any, List

import numpy as np
import pandas as pd
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class PlumeSensor(SensorProduct, SensorWritable):
    """Plume Sensor Product object designed to wrap the csv/json files returned by the Plume API.
    Per sensor object designed to wrap the csv/json files returned by the Plume API.
    Extends the SensorWritable class.
    :param SensorWritable: SensorWritable class to inherit from.
    """

    def __init__(self, id_, dataframe: pd.DataFrame, error: str):
        """Initializes the PlumeSensor object.
        Args:
            id_ (str): The sensor id.
            dataframe (pd.DataFrame): The sensor data as a DataFrame.
            error (str, optional): Error message if any. Defaults to None.
        """
        super().__init__(id_, dataframe, error)
        self.data_columns = [
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.NO2.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]

    def join_dataframes(self, mdf: pd.DataFrame):
        """Combines the measurement dataframe with the existing dataframe.
        :param mdf: The measurement dataframe."""

        # drop timestamps for measurement dataframe
        mdf.drop(columns="timestamp", inplace=True)
        self.df = self.df.join(mdf, how="outer")

        # fill in null timestamps by converting the index to timestamp
        self.df["filled_timestamps"] = self.df.index.astype(np.int64) // 10**9
        # merge timestamp and timestamps columns on null timestamps
        self.df["timestamp"] = self.df["timestamp"].fillna(self.df["filled_timestamps"])
        # drop filled_timestamps column
        self.df.drop(columns="filled_timestamps", inplace=True)

        # create a new datetime column using the timestamps in format YYYY-MM-DD HH:MM:SS
        self.df["datetime"] = pd.to_datetime(self.df["timestamp"], unit="s")
        # set the datetime column as the index
        self.df.set_index("datetime", inplace=True)

        # rename datetime column to date
        self.df.rename(columns={"datetime": "date"}, inplace=True)

        # convert timestamp column to int
        self.df["timestamp"] = self.df["timestamp"].astype(int)

        # sort indexes
        self.df.sort_index(inplace=True)

    # measurement data
    def add_measurements_json(self, data: list):
        """Extracts the measurement data from the Plume API JSON and adds it to the dataframe.
        :param data: The Plume API JSON data."""
        dfList = []

        for measurements in data:
            temp_df = pd.DataFrame.from_records(measurements)
            dfList.append(temp_df)

        # concatenate all measurement dataframes and prepare dataframe.
        # ignore_index=True to prevent duplicate index errors
        df = pd.concat(dfList, ignore_index=True)
        df = PlumeSensor.prepare_measurements(df)
        self.join_dataframes(df)

        self.df = self.df[self.data_columns]

    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe from the Plume API JSON to make it ready for merging with the locations dataframe.\n
        Addtionally it handles renaming columns to match other sensor platform types.\n
        :param df: The measurement dataframe.
        :return: The prepared measurement dataframe."""

        df.drop(["id"], axis=1, inplace=True)
        df.rename(
            columns={
                "date": SensorMeasurementsColumns.TIMESTAMP.value,
                "no2": SensorMeasurementsColumns.NO2.value,
                "voc": SensorMeasurementsColumns.VOC.value,
                "pm1": SensorMeasurementsColumns.PM1.value,
                "pm10": SensorMeasurementsColumns.PM10.value,
                "pm25": SensorMeasurementsColumns.PM2_5.value,
            },
            inplace=True,
        )
        df.insert(0, "date", pd.to_datetime(df["timestamp"], unit="s"))
        df["date"] = df["date"].dt.floor("Min")  # used to match datetime of measurement data to the datetime of location data
        df.set_index("date", drop=True, inplace=True)
        df = df[~df.index.duplicated(keep="first")]  # remove any duplicated index (this will remove the extra hour recorded for daylight saving)
        df = df.sort_index()

        return df

    @staticmethod
    # measurement data
    def from_json(sensor_id: str, data: list) -> SensorWritable:
        """Factory method builds PlumeSensor from file like object
        containing measurement json data.
        :param sensor_id: id number of sensor
        :param data: List of lists containing measurement data
        :return:
        """
        dfList = []

        try:
            for measurements in data:
                temp_df = pd.DataFrame.from_records(measurements)
                dfList.append(temp_df)

            # concatenate all dataframes and prepare dataframe
            df = pd.concat(dfList, ignore_index=True)

        except (IndexError, ValueError):
            # print("No data found for sensor: {}".format(sensor_id))
            return PlumeSensor(sensor_id, dataframe=None, error="No data found for sensor")

        if df.empty:
            return PlumeSensor(sensor_id, dataframe=None, error="No data found for sensor")
        else:
            df = PlumeSensor.prepare_measurements(df)
            return PlumeSensor(sensor_id, dataframe=df, error=None)

    @staticmethod
    def from_csv(sensor_id: str, csv_file: io.StringIO) -> SensorWritable:
        """Factory method builds PlumeSensor from file like object
        containing location csv data.
        :param sensor_id: id number of sensor
        :param csv_file: csv file like object
        :return:
        """

        df = pd.read_csv(csv_file, dialect=csv.unix_dialect)
        df["date"] = pd.to_datetime(df["date"]).dt.floor("Min")
        df.set_index("date", inplace=True)

        # round the datetime to the nearest minute (this is to match the datetime of the measurement data)
        df.index.floor("60S")

        # drop rows with no location data
        df = df[df["latitude"].notna()]

        if df.empty:
            return None
        else:
            return PlumeSensor(sensor_id, df, error=None)

    @staticmethod
    def from_zip(sensor_id: str, csv_file: io.StringIO) -> SensorWritable:
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
                    "NO2 (ppb)": SensorMeasurementsColumns.NO2.value,
                    "VOC (ppb)": SensorMeasurementsColumns.VOC.value,
                    "pm 1 (ug/m3)": SensorMeasurementsColumns.PM1.value,
                    "pm25 (ug/m3)": SensorMeasurementsColumns.PM2_5.value,
                    "pm 10 (ug/m3)": SensorMeasurementsColumns.PM10.value,
                },
            )

            for col in df.columns:
                if "(Plume AQI)" in col:
                    df.drop(col, axis=1, inplace=True)

            df.set_index("date", inplace=True)

            return PlumeSensor(sensor_id, df, error=None)
