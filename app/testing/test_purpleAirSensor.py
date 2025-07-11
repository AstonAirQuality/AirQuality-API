import json
import unittest  # The test framework
import warnings
from io import StringIO
from unittest import TestCase

import pandas as pd
from sensor_api_wrappers.concrete.products.purpleAir_sensor import PurpleAirSensor


class Test_purpleAirSensor(TestCase):
    """Tests that the purpleAirSensor class can be instantiated and that the data is correctly parsed into a dataframe."""

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

    def test_purpleAirSensor_from_csv(self):
        """Test the PurpleAirSensor class from a CSV file."""
        file = open("testing/test_data/purpleair_sensor_274866.csv", "r")
        data = file.read()
        expected_df = pd.read_csv(StringIO(data), index_col="time_stamp")
        file.close()

        sensor = PurpleAirSensor.from_csv("274866", data)

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, PurpleAirSensor))
        self.assertEqual(sensor.id, "274866")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        self.assertEqual(sensor.df.shape[0], expected_df.shape[0], "The number of rows in the sensor DataFrame should match the test data.")
        self.assertEqual(sensor.df.shape[1], expected_df.shape[1], "The number of columns in the sensor DataFrame should match the test data.")
