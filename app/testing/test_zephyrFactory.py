import datetime as dt
import json
import unittest  # The test framework
from os import environ as env
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import requests
from api_wrappers.concrete.factories.zephyr_factory import ZephyrFactory
from api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from dotenv import load_dotenv


class Test_zephyrFactory(TestCase):
    """
    The following tests are for the Zephyr API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.zf = ZephyrFactory(env["ZEPHYR_USERNAME"], env["ZEPHYR_PASSWORD"])
        pass

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
        start = dt.datetime(2023, 1, 1)
        end = dt.datetime(2023, 1, 2)
        slot = "B"
        mocked_get.return_value.ok = True

        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        sensors = list(self.zf.get_sensors([id_], start, end, slot))

        mocked_get.assert_called_with(
            f"https://data.earthsense.co.uk/dataForViewBySlots/{self.zf.username}/{self.zf.password}/{id_}/{start.strftime('%Y%m%d%H%M')}/{end.strftime('%Y%m%d%H%M')}/{slot}/def/json/api"
        )

        self.assertEqual(len(sensors), 1)
        expected_columns = [
            "NO",
            "NO2",
            "O3",
            "ambHumidity",
            "ambPressure",
            "ambTempC",
            "timestamp",
            "humidity",
            "latitude",
            "longitude",
            "particulatePM1",
            "particulatePM10",
            "particulatePM2.5",
            "tempC",
        ]
        for sensor in sensors:
            self.assertTrue(isinstance(sensor, ZephyrSensor))
            self.assertEqual(sensor.id, "814")
            self.assertTrue(isinstance(sensor.df, pd.DataFrame))
            # check that the dataframe has the correct columns
            self.assertEqual(
                sensor.df.columns.tolist(),
                expected_columns,
            )


if __name__ == "__main__":
    unittest.main()
