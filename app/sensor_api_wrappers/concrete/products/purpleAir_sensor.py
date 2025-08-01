from io import StringIO

import numpy as np
import pandas as pd
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class PurpleAirSensor(SensorProduct, SensorWritable):
    """PurpleAirSensor Sensor Product object designed to wrap the csv/json files returned by the Zephyr API."""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame, error: str):
        """Initializes the PurpleAirSensor object.

        Args:
            sensor_id (str): The sensor id.
            dataframe (pd.DataFrame): The sensor data as a DataFrame.
            error (str, optional): Error message if any. Defaults to None.
        """
        super().__init__(sensor_id, dataframe, error)
        self.data_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.PM1_A.value,
            SensorMeasurementsColumns.PM1_B.value,
            SensorMeasurementsColumns.PM2_5_A.value,
            SensorMeasurementsColumns.PM2_5_B.value,
            SensorMeasurementsColumns.PM10_A.value,
            SensorMeasurementsColumns.PM10_B.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.SCATTERING_COEFFICIENT.value,
            SensorMeasurementsColumns.DECIVIEWS.value,
            SensorMeasurementsColumns.VISUAL_RANGE.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
        if dataframe is not None:
            self.df = self.df[self.data_columns]

    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe for merging with the locations dataframe and renames columns to match other sensor platform types.

        Args:
            df (pd.DataFrame): The measurement dataframe.
        Returns:
            pd.DataFrame: The prepared measurement dataframe.
        """

        # drop rows when all columns havs NaN values
        df.dropna(how="all", inplace=True)

        # drop NaN columns
        df.dropna(axis=1, how="all", inplace=True)

        # drop sensor_index column
        if "sensor_index" in df.columns:
            df.drop(columns=["sensor_index"], inplace=True)

        # infer the data types of the columns
        df = df.infer_objects()

        # set dateTime column to datetime type
        df["time_stamp"] = pd.to_datetime(df["time_stamp"], unit="ns")

        # time_stamp,humidity,temperature,pressure,voc,scattering_coefficient,deciviews,visual_range,
        # pm1.0_cf_1_a,pm1.0_cf_1_b,pm1.0_atm_a,pm1.0_atm_b,pm2.5_atm_a,pm2.5_atm_b,pm2.5_cf_1_a,pm2.5_cf_1_b,
        # pm10.0_atm_a,pm10.0_atm_b,pm10.0_cf_1_a,pm10.0_cf_1_b
        df.rename(
            columns={
                "time_stamp": "date",
                "humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
                "temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
                "pressure": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
                "voc": SensorMeasurementsColumns.VOC.value,
                "scattering_coefficient": SensorMeasurementsColumns.SCATTERING_COEFFICIENT.value,
                "deciviews": SensorMeasurementsColumns.DECIVIEWS.value,
                "visual_range": SensorMeasurementsColumns.VISUAL_RANGE.value,
            },
            inplace=True,
        )

        if "pm1.0_cf_1_a" in df.columns:
            df.rename(
                columns={
                    "pm1.0_cf_1_a": SensorMeasurementsColumns.PM1_A.value,
                    "pm1.0_cf_1_b": SensorMeasurementsColumns.PM1_B.value,
                    "pm2.5_cf_1_a": SensorMeasurementsColumns.PM2_5_A.value,
                    "pm2.5_cf_1_b": SensorMeasurementsColumns.PM2_5_B.value,
                    "pm10.0_cf_1_a": SensorMeasurementsColumns.PM10_A.value,
                    "pm10.0_cf_1_b": SensorMeasurementsColumns.PM10_B.value,
                },
                inplace=True,
            )
        elif "pm1.0_atm_a" in df.columns:
            df.rename(
                columns={
                    "pm1.0_atm_a": SensorMeasurementsColumns.PM1_A.value,
                    "pm1.0_atm_b": SensorMeasurementsColumns.PM1_B.value,
                    "pm2.5_atm_a": SensorMeasurementsColumns.PM2_5_A.value,
                    "pm2.5_atm_b": SensorMeasurementsColumns.PM2_5_B.value,
                    "pm10.0_atm_a": SensorMeasurementsColumns.PM10_A.value,
                    "pm10.0_atm_b": SensorMeasurementsColumns.PM10_B.value,
                },
                inplace=True,
            )

        # create an average for pm1.0, pm2.5 and pm10
        df[SensorMeasurementsColumns.PM1.value] = (df[SensorMeasurementsColumns.PM1_A.value] + df[SensorMeasurementsColumns.PM1_B.value]) / 2
        df[SensorMeasurementsColumns.PM2_5.value] = (df[SensorMeasurementsColumns.PM2_5_A.value] + df[SensorMeasurementsColumns.PM2_5_B.value]) / 2
        df[SensorMeasurementsColumns.PM10.value] = (df[SensorMeasurementsColumns.PM10_A.value] + df[SensorMeasurementsColumns.PM10_B.value]) / 2

        df.set_index("date", drop=True, inplace=True)
        # create a new timestamp column using utc timestamps
        df["timestamp"] = df.index.astype("int64") // 10**9  # convert to seconds

        # add latitude and longitude columns with NaN values
        df["latitude"] = np.nan
        df["longitude"] = np.nan

        return df

    @staticmethod
    def from_csv(sensor_id: str, data_string: str) -> SensorWritable:
        """Creates a PurpleAirSensor object from a csv string.

        Args:
            sensor_id (str): The sensor id.
            data_string (str): The csv data as a string.

        Returns:
            PurpleAirSensor: An instance of PurpleAirSensor with the data loaded into a DataFrame.
        """
        # Convert the csv string to a string io and then read it into a DataFrame
        df = PurpleAirSensor.prepare_measurements(pd.read_csv(StringIO(data_string)))
        return PurpleAirSensor(sensor_id, dataframe=df, error=None)

    @staticmethod
    def from_json(sensor_id: str, data: list) -> SensorWritable:
        pass
        # return PurpleAirSensor(sensor_id, dataframe=None, error="Not implemented yet")


# if __name__ == "__main__":
#     # Example usage
#     sensor_id = "12345,outdoor"
#     csv_data = """time_stamp,sensor_index,humidity,temperature,pressure,voc,scattering_coefficient,deciviews,visual_range,pm1.0_cf_1_a,pm1.0_cf_1_b,pm1.0_atm_a,pm1.0_atm_b,pm2.5_atm_a,pm2.5_atm_b,pm2.5_cf_1_a,pm2.5_cf_1_b,pm10.0_atm_a,pm10.0_atm_b,pm10.0_cf_1_a,pm10.0_cf_1_b
# 2025-07-07T23:52:04Z,274866,53,65,999.24,66,17.8,11.4,124.2,6.5,6.6,6.5,6.6,8.8,8.8,8.8,8.8,11.2,9.6,11.2,9.6
# 2025-07-07T15:15:59Z,274866,34,73,998.57,71,14.7,10.2,141.2,4.8,4.8,4.8,4.8,6.3,6.8,6.3,6.8,8.7,8.0,8.7,8.0

#     """
#     # """time_stamp,sensor_index,humidity,temperature,voc
#     #     2023-10-01T00:00:00Z,12345,45.0,22.0,
#     #     2023-10-01T01:00:00Z,12345,46.0,23.0,
#     #     2023-10-01T02:00:00Z,12345,47.0,24.0,
#     #     """

#     sensor = PurpleAirSensor.from_csv(sensor_id, csv_data)
#     print(sensor.df)
#     # for summary in sensor.create_sensor_summaries("POLYGON((-1.889767 52.45279,-1.889767 52.45281,-1.889747 52.45281,-1.889747 52.45279,-1.889767 52.45279))"):
#     #     print(summary.measurement_data)
