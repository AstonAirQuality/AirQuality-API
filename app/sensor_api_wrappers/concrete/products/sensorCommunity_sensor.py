import io

import numpy as np
import pandas as pd
from routers.services.formatting import decode_geohash
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class SensorCommunitySensor(SensorProduct, SensorWritable):
    """SensorCommunity Sensor Product object designed to wrap the csv/json files returned by the SensorCommunity API.
    \n currently only supports SHT31, SDS011, and BME280 sensors"""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame):
        """Initializes the SensorCommunitySensor object.
        :param sensor_id: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(sensor_id, dataframe)

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
            columns={"P1": "particulatePM10", "P2": "particulatePM2.5", "temperature": "tempC", "pressure": "ambPressure", "lon": "longitude", "lat": "latitude"},
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
        # resampling with 180 seconds will group most/all valid measurements together even if there are gaps
        df = df.resample("180S").first()

        # drop rows with NaT time values
        df = df.dropna(subset=["time"])
        df.set_index("time", inplace=True)

        # renaming columns
        df = df.rename(columns={"dht22_humidity": "ambHumidity", "dht22_temperature": "ambTempC", "sds011_p1": "particulatePM10", "sds011_p2": "particulatePM2.5"})
        # decode geohash
        df[["latitude", "longitude"]] = decode_geohash(df["geohash"][0])

        # drop geohash column
        df.drop(columns=["geohash"], inplace=True)

        # set all columns to float
        df = df.astype(float)

        # create unix timestamp column
        df["timestamp"] = df.index.astype(np.int64) // 10**9

        return SensorCommunitySensor(sensor_id, df)

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

                try:
                    df.drop(["sensor_id", "sensor_type", "location", "ratioP1", "ratioP2", "durP1", "durP2"], axis=1, inplace=True)
                except KeyError:
                    df.drop(["sensor_id", "sensor_type", "location"], axis=1, inplace=True)

                data[timestamp] = df

        sensorPlatform[id_] = content

        df = SensorCommunitySensor.prepare_measurements(SensorCommunitySensor.ResampleDataAndSortIntoDays(sensorPlatform, "145S"))
        return SensorCommunitySensor(id_, df)
