import datetime as dt
import json
import unittest  # The test framework
import warnings
from os import environ as env
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import requests
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.zephyr_factory import ZephyrFactory
from sensor_api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from sensor_api_wrappers.data_transfer_object.sensor_measurements import SensorMeasurementsColumns


class Test_zephyrFactory(TestCase):
    """
    The following tests are for the Zephyr API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        warnings.simplefilter("ignore", ResourceWarning)
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])
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
        """Tear down the test environment once after all tests
        :param cls: The class object
        """
        pass

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    @patch.object(requests, "get")
    def test_fetch_lookup_ids(self, mocked_get):
        """Test fetch the correct lookup ids.
        \n Uses mock data"""

        mocked_get.return_value.ok = True

        file = open("testing/test_data/Zephyr_LookupIds.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        sensor_platforms = list(self.zf.fetch_lookup_ids())

        mocked_get.assert_called_with(f"https://data.earthsense.co.uk/zephyrsForUser/{self.zf.username}/{self.zf.password}")

        expected = ["814", "821"]
        self.assertEqual(sensor_platforms, expected)

    @patch.object(requests, "get")
    def test_get_sensors(self, mocked_get):
        """Test fetch the correct sensor data.
        \n Uses mock data"""

        id_ = "814"
        start = dt.datetime(2023, 3, 31)
        end = dt.datetime(2023, 4, 1)
        slot = "B"
        sensor_dict = {id_: {"stationary_box": None, "time_updated": None}}
        mocked_get.return_value.ok = True

        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        sensors = list(self.zf.get_sensors(sensor_dict, start, end, slot))

        mocked_get.assert_called_with(
            f"https://data.earthsense.co.uk/measurementdata/v1/{id_}/{start.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/B/0",
            headers={"username": self.zf.username, "userkey": self.zf.password},
        )

        self.assertEqual(len(sensors), 1)

        for sensor in sensors:
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
