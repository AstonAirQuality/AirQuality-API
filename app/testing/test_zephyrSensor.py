import json
import unittest  # The test framework
import warnings
from unittest import TestCase

import pandas as pd
from api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor


class Test_zephyrSensor(TestCase):
    """Tests that the ZephyrSensor class can be instantiated and that the data is correctly parsed into a dataframe."""

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

    def test_zephyr_from_json(self):
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])

        self.assertIsNotNone(sensor)
        expected_columns = [
            "NO",
            "NO2",
            "O3",
            "timestamp",
            "ambHumidity",
            "ambPressure",
            "ambTempC",
            "humidity",
            "particulatePM1",
            "particulatePM10",
            "particulatePM2.5",
            "tempC",
            "latitude",
            "longitude",
        ]
        self.assertTrue(isinstance(sensor, ZephyrSensor))
        self.assertEqual(sensor.id, "814")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe has the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(expected_columns),
        )


if __name__ == "__main__":
    unittest.main()
