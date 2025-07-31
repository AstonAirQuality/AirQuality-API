import json
import unittest  # The test framework
import warnings
from unittest import TestCase

import pandas as pd
from sensor_api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns


class Test_zephyrSensor(TestCase):
    """Tests that the ZephyrSensor class can be instantiated and that the data is correctly parsed into a dataframe."""

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.expected_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.TEMPERATURE.value,
            SensorMeasurementsColumns.HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
            SensorMeasurementsColumns.NO.value,
            SensorMeasurementsColumns.NO2.value,
            SensorMeasurementsColumns.O3.value,
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

    def test_zephyr_from_json(self):
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])

        self.assertIsNotNone(sensor)

        self.assertTrue(isinstance(sensor, ZephyrSensor))
        self.assertEqual(sensor.id, "814")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe has the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(self.expected_columns),
        )


if __name__ == "__main__":
    unittest.main()
