import unittest  # The test framework
import warnings
from unittest import TestCase

import pandas as pd
from api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor


class Test_sensorCommunitySensor(TestCase):
    """Tests that the SensorCommunitySensor class can be instantiated and that the data is correctly parsed into a dataframe."""

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        pass

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

        expected_columns = ["particulatePM10", "particulatePM2.5", "ambPressure", "humidity", "latitude", "longitude", "tempC", "timestamp"]

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, SensorCommunitySensor))
        self.assertEqual(sensor.id, sensor_id)
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe contains the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(expected_columns),
        )


if __name__ == "__main__":
    unittest.main()
