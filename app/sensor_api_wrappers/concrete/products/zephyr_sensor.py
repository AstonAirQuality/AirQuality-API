import numpy as np
import pandas as pd
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class ZephyrSensor(SensorProduct, SensorWritable):
    """Zephyr Sensor Product object designed to wrap the csv/json files returned by the Zephyr API."""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame, error: str):
        """Initializes the ZephyrSensor object.
        :param sensor_id: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(sensor_id, dataframe, error)
        self.data_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.TEMPERATURE.value,
            SensorMeasurementsColumns.HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
            SensorMeasurementsColumns.NO.value,
            SensorMeasurementsColumns.NO2.value,
            SensorMeasurementsColumns.O3.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
        if dataframe is not None:
            self.df = self.df[self.data_columns]

    @staticmethod
    def prepare_measurements(df: pd.DataFrame) -> pd.DataFrame:
        """Prepares the measurement dataframe for merging with the locations dataframe and renames columns to match other sensor platform types.
        :param df: The measurement dataframe.
        :return: The prepared measurement dataframe."""

        # drop rows with all NaN values
        df.dropna(how="all", inplace=True)

        # infer the data types of the columns
        df = df.infer_objects()

        # set dateTime column to datetime type
        df["dateTime"] = pd.to_datetime(df["dateTime"], unit="ns")

        df.rename(
            columns={
                "dateTime": "date",
                "UTS": SensorMeasurementsColumns.DATE.value,
                "particulatePM25": SensorMeasurementsColumns.PM2_5.value,
                "particulatePM10": SensorMeasurementsColumns.PM10.value,
                "particulatePM1": SensorMeasurementsColumns.PM1.value,
                "ambTempC": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
                "ambHumidity": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
                "ambPressure": SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
                "humidity": SensorMeasurementsColumns.HUMIDITY.value,
                "tempC": SensorMeasurementsColumns.TEMPERATURE.value,
                "NO": SensorMeasurementsColumns.NO.value,
                "NO2": SensorMeasurementsColumns.NO2.value,
                "O3": SensorMeasurementsColumns.O3.value,
            },
            inplace=True,
        )

        df.set_index("date", drop=True, inplace=True)

        df = df.loc[~df.index.duplicated()]

        # add latitude and longitude columns with NaN values, which will be filled by the stationary box later
        df["latitude"] = np.nan
        df["longitude"] = np.nan

        return df

    @staticmethod
    def from_json(sensor_id: str, data: list) -> SensorWritable:
        """Factory method builds ZephyrSensor objects from json list returned by API
        :param sensor_id: sensor id
        :param data: json list
        :return: ZephyrSensor object
        """
        df = pd.DataFrame.from_records(data)
        df.drop("header", axis=0, inplace=True)
        df.drop("data_hash", axis=0, inplace=True)
        df.drop("localDateTime", axis=1, inplace=True)

        # explode function transform each element of a list to a row.
        # we can apply it to all the columns assuming they have the same number of elements in each list
        df = df.apply(pd.Series.explode)

        df = ZephyrSensor.prepare_measurements(df)

        return ZephyrSensor(sensor_id, dataframe=df, error=None)

    @staticmethod
    def from_csv(sensor_id: str, *args, **kwargs):
        pass


if __name__ == "__main__":
    import json

    file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
    json_ = json.load(file)
    file.close()
    sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])
    # print dataframe columns
    print(sensor.df.head())
    print(sensor.df.columns.tolist())

    # summaries = list(sensor.create_sensor_summaries(None))
    # print(summaries[0])
