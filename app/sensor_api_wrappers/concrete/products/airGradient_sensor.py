from io import StringIO

import numpy as np
import pandas as pd
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from sensor_api_wrappers.interfaces.sensor_product import SensorProduct


class AirGradientSensor(SensorProduct, SensorWritable):
    """AirGradient Sensor Product object designed to wrap the csv/json files returned by the AirGradient API."""

    def __init__(self, sensor_id: str, dataframe: pd.DataFrame):
        """Initializes the AirGradientSensor object.
        :param sensor_id: The sensor id.
        :param dataframe: The sensor data.
        """
        super().__init__(sensor_id, dataframe)
        self.data_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.PM1_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM0_3_COUNT.value,
            SensorMeasurementsColumns.CO2.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.VOC_INDEX.value,
            SensorMeasurementsColumns.NOX_INDEX.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
        self.df = self.df[self.data_columns]

    @staticmethod
    def from_json(sensor_id: str, data: list) -> SensorWritable:
        """Factory method builds AirGradientSensor objects from json list returned by API

        Args:
            sensor_id (str): Sensor id.
            data (list): JSON list containing sensor data.
        Returns:
            AirGradientSensor: An AirGradientSensor object with the data.
        """
        df = pd.DataFrame.from_records(data)

        # rename columns to match the SensorMeasurementsColumns enum
        df.rename(
            columns={
                "pm01": SensorMeasurementsColumns.PM1_RAW.value,
                "pm02": SensorMeasurementsColumns.PM2_5_RAW.value,
                "pm10": SensorMeasurementsColumns.PM10_RAW.value,
                "pm01_corrected": SensorMeasurementsColumns.PM1.value,
                "pm02_corrected": SensorMeasurementsColumns.PM2_5.value,
                "pm10_corrected": SensorMeasurementsColumns.PM10.value,
                "pm003Count": SensorMeasurementsColumns.PM0_3_COUNT.value,
                "atmp_corrected": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
                "rhum_corrected": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
                "rco2": SensorMeasurementsColumns.CO2.value,
                "tvoc": SensorMeasurementsColumns.VOC.value,
                "tvocIndex": SensorMeasurementsColumns.VOC_INDEX.value,
                "noxIndex": SensorMeasurementsColumns.NOX_INDEX.value,
            },
            inplace=True,
        )

        # drop rows with all NaN values
        df.dropna(how="all", inplace=True)

        # infer the data types of the columns
        df = df.infer_objects()

        # rename timestamp column to date and make a timestamp column
        df.rename(columns={"timestamp": "date"}, inplace=True)
        df[SensorMeasurementsColumns.DATE.value] = pd.to_datetime(df["date"], unit="ns").astype("int64") // 10**9  # convert to seconds

        df.set_index("date", drop=True, inplace=True)

        # add latitude and longitude columns with NaN values, which will be filled by the stationary box later
        df["latitude"] = np.nan
        df["longitude"] = np.nan

        return AirGradientSensor(sensor_id, df)

    @staticmethod
    def from_csv(sensor_id: str, csv_data: str) -> SensorWritable:
        """Factory method builds AirGradientSensor objects from csv data.
        Args:
            sensor_id (str): Sensor id.
            csv_data (str): CSV data as a string.
        Returns:
            AirGradientSensor: An AirGradientSensor object with the data loaded into a DataFrame.
        """
        df = pd.read_csv(StringIO(csv_data))

        df.rename(
            columns={
                "PM1 (μg/m³)": SensorMeasurementsColumns.PM1_RAW.value,
                "PM2.5 (μg/m³) raw": SensorMeasurementsColumns.PM2_5_RAW.value,
                "PM10 (μg/m³)": SensorMeasurementsColumns.PM10_RAW.value,
                "0.3um particle count": SensorMeasurementsColumns.PM0_3_COUNT.value,
                "CO2 (ppm) raw": SensorMeasurementsColumns.CO2.value,
                "Temperature (°C) raw": SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
                "Humidity (%) raw": SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
                "TVOC avg (ppb)": SensorMeasurementsColumns.VOC.value,
                "TVOC index": SensorMeasurementsColumns.VOC_INDEX.value,
                "NOX index": SensorMeasurementsColumns.NOX_INDEX.value,
            },
            inplace=True,
        )

        # unbucketed csv data does not have PM1, PM2.5, and PM10 columns, so we add them with NaN values
        df[SensorMeasurementsColumns.PM1.value] = np.nan
        df[SensorMeasurementsColumns.PM2_5.value] = np.nan
        df[SensorMeasurementsColumns.PM10.value] = np.nan

        # drop rows with all NaN values
        df.dropna(how="all", inplace=True)

        # infer the data types of the columns
        df = df.infer_objects()

        # make a timestamp column from the UTC Date/Time column
        df[SensorMeasurementsColumns.DATE.value] = pd.to_datetime(df["UTC Date/Time"], unit="ns").astype("int64") // 10**9

        df.set_index("UTC Date/Time", drop=True, inplace=True)
        # add latitude and longitude columns with NaN values, which will be filled by the stationary box later
        df["latitude"] = np.nan
        df["longitude"] = np.nan

        print(df.columns.tolist())

        return AirGradientSensor(sensor_id, df)


# 'particulatePM1Raw', 'particulatePM2.5Raw', 'particulatePM10Raw', 'ambTempC' are not being found in the final df


if __name__ == "__main__":
    import json

    file = open("testing/test_data/airgradient_163763_data.json", "r")
    json_ = json.load(file)
    file.close()

    sensor = AirGradientSensor.from_json("123456", json_)
    # print(sensor.df.head())
    print(sensor.df.columns.tolist())

    # csv test

    file = open("testing/test_data/airgradient_163763_data.csv", "r", encoding="utf-8")
    csv_data = file.read()
    file.close()

    sensor = AirGradientSensor.from_csv("123456", csv_data)
    # print(sensor.df.head())
    print(sensor.df.columns.tolist())
