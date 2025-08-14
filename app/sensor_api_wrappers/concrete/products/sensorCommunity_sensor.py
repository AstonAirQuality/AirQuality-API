import io

import numpy as np
import pandas as pd
from routers.services.enums import SensorMeasurementsColumns
from routers.services.formatting import decode_geohash
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct

mappings = {
    "bme280_humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
    "bme280_pressure": SensorMeasurementsColumns.PRESSURE.value,
    "bme280_pressure_at_sealevel": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
    "bme280_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "bmp180_pressure": SensorMeasurementsColumns.PRESSURE.value,
    "bmp180_pressure_at_sealevel": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
    "bmp180_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "bmp280_pressure": SensorMeasurementsColumns.PRESSURE.value,
    "bmp280_pressure_at_sealevel": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
    "bmp280_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "dht22_humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
    "dht22_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "ds18b20_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "hpm_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "hpm_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "htu21d_humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
    "htu21d_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "ips7100_p0": SensorMeasurementsColumns.PM10_RAW.value,
    "ips7100_p1": SensorMeasurementsColumns.PM1_RAW.value,
    "ips7100_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "noise_LA_max": SensorMeasurementsColumns.NOISE_LA_MAX.value,
    "noise_LA_min": SensorMeasurementsColumns.NOISE_LA_MIN.value,
    "noise_LAeq": SensorMeasurementsColumns.NOISE_LA_EQ.value,
    "noise_LAeq_delog": SensorMeasurementsColumns.NOISE_LA_EQ_DELOG.value,
    "npm_p0": SensorMeasurementsColumns.PM1_RAW.value,
    "npm_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "npm_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "pms_p0": SensorMeasurementsColumns.PM1_RAW.value,
    "pms_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "pms_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "ppd42ns_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "ppd42ns_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "sds011_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "sds011_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "sht_humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
    "sht_temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
    "sps30_p0": SensorMeasurementsColumns.PM1_RAW.value,
    "sps30_p1": SensorMeasurementsColumns.PM10_RAW.value,
    "sps30_p2": SensorMeasurementsColumns.PM2_5_RAW.value,
    "sps30_p4": SensorMeasurementsColumns.PM_4_RAW.value,
}


class SensorCommunitySensor(SensorProduct, SensorWritable):
    """SensorCommunity Sensor Product object designed to wrap the csv/json files returned by the SensorCommunity API.
    \n currently only supports SHT31, SDS011, and BME280 sensors"""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame, error: str):
        """Initializes the SensorCommunitySensor object.
        :param sensor_id: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(sensor_id, dataframe, error)

    # @DeprecationWarning
    @staticmethod
    def ResampleDataAndSortIntoDays(sensorPlatform: dict[str, dict[int, pd.DataFrame]], intervalString: str) -> pd.DataFrame:
        """Resamples data and combines all sensor data into one sensor platform. A unique key contains the sensor ids of each sensor in the sensor platform.
        :param sensorPlatform: A dictionary of sensor ids as the keys for a dictionary of dataframes split amongst day intervals with a unique timestamp key to identify each day of data
        :param intervalString: The interval string to resample the data by
        :return: A dataframe containing all the sensor data for the sensor platform
        """

        dfList = []

        combinedDataframe = None
        # for each sensor in the sensorPlatform dictionary
        for sensorPairs in sensorPlatform.values():
            # for each dataframe dictionary in the sensor dictionary
            for dataframeDict in sensorPairs.values():
                # for each dataframe in the dataframe dictionary
                for dataframe in dataframeDict.values():
                    # append the dataframe to the list and resample the data
                    dataframe = dataframe.resample(intervalString).nearest()
                    dfList.append(dataframe)
                    if combinedDataframe is None:
                        combinedDataframe = dataframe
                    else:
                        combinedDataframe = combinedDataframe.combine_first(dataframe)

        # drop null columns
        combinedDataframe.dropna(axis=1, how="all", inplace=True)

        return combinedDataframe

    # @DeprecationWarning
    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe to match the column names of the other sensors (zephyr)
        :param df: The measurement dataframe.
        :return: The prepared measurement dataframe."""

        # infer the data types of the columns
        df = df.infer_objects()

        # rename the index column and create a timestamp column from the index
        df.index.name = "date"
        df["timestamp"] = df.index
        df["timestamp"] = df["timestamp"].astype("int64") // 10**9

        df.rename(
            columns={
                "P1": SensorMeasurementsColumns.PM10_RAW.value,
                "P2": SensorMeasurementsColumns.PM2_5_RAW.value,
                "humidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
                "temperature": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
                "pressure": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
                "lon": SensorMeasurementsColumns.LONGITUDE.value,
                "lat": SensorMeasurementsColumns.LATITUDE.value,
            },
            inplace=True,
        )

        # drop any duplicate rows
        df = df.loc[~df.index.duplicated()]

        return df

    @staticmethod
    def from_json(sensor_id: str, data: dict) -> SensorWritable:
        df = pd.DataFrame(data["results"][0]["series"][0]["values"], columns=data["results"][0]["series"][0]["columns"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df = df.set_index("time")

        # data aggregation
        df = df.reset_index()
        df["datetime"] = pd.to_datetime(df["time"], unit="ms")
        df.set_index("datetime", inplace=True)

        # measurements are taken every 145 seconds, sometimes there are gaps of variable length ranging from 1 to 30 seconds
        # resampling with 180 seconds will group most/all valid measurements together even if there are gaps, but for consistency we use 145 seconds
        df = df.resample("145S").first()

        # drop rows with NaT time values
        df = df.dropna(subset=["time"])
        df.set_index("time", inplace=True)

        # rename columns that exist in the df using the mapping
        df.rename(columns={key: value for key, value in mappings.items() if key in df.columns}, inplace=True, errors="ignore")

        # decode geohash
        df[["latitude", "longitude"]] = decode_geohash(df["geohash"][0])

        # drop geohash column
        df.drop(columns=["geohash"], inplace=True)

        # set all columns to float
        df = df.astype(float)

        # create unix timestamp column
        df["timestamp"] = df.index.astype(np.int64) // 10**9

        return SensorCommunitySensor(sensor_id, df, error=None)

    # @DeprecationWarning
    @staticmethod
    def from_csv(id_: str, content: dict[int, bytes]) -> SensorWritable:
        """Creates a SensorCommunitySensor object from a dictionary of csv files.
        :param content: dictionary of csv files with a unique timestamp key to identify each day of data
        :return: Dataframe of sensor data
        """
        sensorPlatform = {}
        for data in content.values():
            for timestamp, csvData in data.items():
                file_ = io.BytesIO(csvData)
                buffer = io.StringIO(file_.read().decode("UTF-8"))

                df = pd.read_csv(buffer, sep=";", parse_dates=True, index_col="timestamp")
                df.drop(["sensor_id", "sensor_type", "location", "ratioP1", "ratioP2", "durP1", "durP2"], axis=1, inplace=True, errors="ignore")
                data[timestamp] = df

        sensorPlatform[id_] = content

        df = SensorCommunitySensor.prepare_measurements(SensorCommunitySensor.ResampleDataAndSortIntoDays(sensorPlatform, "145S"))
        return SensorCommunitySensor(id_, df, error=None)
