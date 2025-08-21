import json
import unittest  # The test framework
import warnings
from unittest import TestCase

import pandas as pd
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor


class Test_sensorCommunitySensor(TestCase):
    """Tests that the SensorCommunitySensor class can be instantiated and that the data is correctly parsed into a dataframe."""

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.expected_columns_1 = [
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
        cls.expected_columns_2 = [
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        pass

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    def test_sensorCommunity_from_csv(self):
        """Tests that the SensorCommunitySensor class can be instantiated and that the csv data is correctly parsed into a dataframe."""

        csv_files = {60641: {0: None}, 60642: {0: None}}
        sensor_id = "60641,SDS011,60642,BME280"

        file = open("testing/test_data/2023-04-01_sds011_sensor_60641.csv", "r")
        csv_files[60641][0] = file.read().encode()
        file.close()

        file = open("testing/test_data/2023-04-01_bme280_sensor_60642.csv", "r")
        csv_files[60642][0] = file.read().encode()
        file.close()

        sensor = SensorCommunitySensor.from_csv(sensor_id, csv_files)

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, SensorCommunitySensor))
        self.assertEqual(sensor.id, sensor_id)
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe contains the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(self.expected_columns_1),
        )

    def test_sensorCommunity_from_json(
        self,
    ):
        """Tests that the SensorCommunitySensor class can be instantiated and that the json data is correctly parsed into a dataframe."""

        file = open("testing/test_data/sensorCommunity.json", "r")
        json_ = json.load(file)
        file.close()

        sensor_id = "83636,SDS011,83637,DHT22"
        sensor = SensorCommunitySensor.from_json(sensor_id, json_)

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, SensorCommunitySensor))
        self.assertEqual(sensor.id, sensor_id)
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe contains the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(self.expected_columns_2),
        )


if __name__ == "__main__":
    unittest.main()
