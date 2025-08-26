from io import StringIO

import numpy as np
import pandas as pd
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class GenericSensor(SensorProduct, SensorWritable):
    """Generic Sensor Product object designed to wrap the csv/json files returned by a generic sensor API."""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame, error: str):
        """Initializes the GenericSensor object.
        :param sensor_id: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(sensor_id, dataframe, error)

    @staticmethod
    def prepare_mesaurements(df: pd.DataFrame, column_mappings: dict) -> pd.DataFrame:
        """Prepares the measurements dataframe by renaming columns and ensuring required columns are present."""
        # rename columns to match the SensorMeasurementsColumns enum
        df.rename(
            columns=column_mappings,
            inplace=True,
            errors="ignore",  # ignore errors if columns are not found
        )

        # any missing columns should be added with NaN values
        for column in column_mappings.values():
            if column not in df.columns:
                df[column] = np.nan

        # drop rows with all NaN values
        df.dropna(how="all", inplace=True)

        # infer the data types of the columns
        df = df.infer_objects()

        # detect which column is the date column
        key = next((col for col in df.columns if "date" in col.lower() or "timestamp" in col.lower()), None)
        # in case it is called timestamp make a new column called datetime which we will set to index
        df["datetime"] = df[key]
        df.set_index("datetime", drop=True, inplace=True)
        df[SensorMeasurementsColumns.TIMESTAMP.value] = pd.to_datetime(df.index, unit="ns").astype("int64") // 10**9

        # add latitude and longitude columns with NaN values if not present
        if "latitude" not in df.columns:
            df[SensorMeasurementsColumns.LATITUDE.value] = np.nan
        if "longitude" not in df.columns:
            df[SensorMeasurementsColumns.LONGITUDE.value] = np.nan

        # filter df to only include the keys from the column_mappings
        relevant_columns = list(column_mappings.values()) + [
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]

        filter_columns = [col for col in relevant_columns if col in df.columns]
        df = df[filter_columns]

        return df

    @staticmethod
    def from_json(sensor_id: str, data: list, column_mappings: dict) -> SensorWritable:
        """Factory method builds GenericSensor objects from json list returned by API

        Args:
            sensor_id (str): Sensor id.
            data (list): JSON list containing sensor data.
        Returns:
            GenericSensor: A GenericSensor object with the data.
        """
        df = pd.DataFrame.from_records(data)

        df = GenericSensor.prepare_mesaurements(df, column_mappings)

        return GenericSensor(sensor_id, df, "")

    @staticmethod
    def from_csv(sensor_id: str, csv_data: str, column_mappings: dict) -> SensorWritable:
        """Factory method builds GenericSensor objects from csv data returned by API

        Args:
            sensor_id (str): Sensor id.
            csv_data (str): CSV data as a string.
            column_mappings (dict): Dictionary mapping CSV columns to SensorMeasurementsColumns.
        Returns:
            GenericSensor: A GenericSensor object with the data.
        """
        df = pd.read_csv(StringIO(csv_data))

        df = GenericSensor.prepare_mesaurements(df, column_mappings)

        return GenericSensor(sensor_id, df, "")
