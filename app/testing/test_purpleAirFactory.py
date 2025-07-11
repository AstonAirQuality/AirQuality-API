import datetime as dt
import json
import unittest  # The test framework
import warnings
from io import StringIO
from os import environ as env
from unittest import TestCase
from unittest.mock import patch

import pandas as pd
import requests
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.purpleAir_factory import PurpleAirFactory
from sensor_api_wrappers.concrete.products.purpleAir_sensor import PurpleAirSensor


class Test_purpleAirFactory(TestCase):
    """
    The following tests are for the PurpleAir API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        warnings.simplefilter("ignore", ResourceWarning)
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.pf = PurpleAirFactory(
            token_url=env["PURPLE_AIR_TOKEN_URL"],
            referer_url=env["PURPLE_AIR_REFERER_URL"],
            api_key=env["PURPLE_AIR_API_KEY"],
        )
        pass

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests
        :param cls: The class object
        """
        pass

    @patch.object(requests, "get")
    def test_successful_login(self, mocked_get):
        """Test the login method of the PurpleAirFactory."""

        mocked_get.return_value.status_code = 200

        # Mock the response text to simulate a successful login
        mocked_get.return_value.text = (
            "Xm1XnBkWbXoMDmmd6/Eg5WuDvMMDP7rKvIsICpsWUHAuh5xOCce0puuSg9obKXbjxVl/jccVmXL9freup7ji1uWHDyHA2YQ+Nf3EijNNjddXWUj2CR+I9Zekb8kg9YtlzweB8NaeqO25paVU1za5TTpSeVn72nWfYk9YQbjZ2KM="
        )

        initial_api_key = self.pf.api_key
        self.pf.login()

        mocked_get.assert_called_with(
            self.pf.token_url,
            headers={
                "referer": self.pf.referer_url,
            },
            timeout=30,  # wait up to 30 seconds for the API to respond
        )
        # Check if the API key has been updated and is not None
        self.assertIsNotNone(self.pf.api_key, "API key should not be None after login.")
        self.assertNotEqual(initial_api_key, self.pf.api_key, "API key should change after login.")

    @patch.object(requests, "get")
    def test_retry_get_sensors(self, mocked_get):
        """Test the retry mechanism in get_sensors method."""

        mocked_get.return_value.ok = False

        error_response = {
            "api_version": "V3.1.5-1.1.44",
            "time_stamp": 1752188991,
            "error": "DataInitializingError",
            "description": "The server is loading data and you should try again in 10 seconds.",
        }
        mocked_get.return_value.text = json.dumps(error_response)
        mocked_get.return_value.json.return_value = error_response

        sensor_dict = {"132169": {"stationary_box": None, "time_updated": None}}
        start = dt.datetime(2025, 7, 7)
        end = dt.datetime(2025, 7, 8)

        with patch.object(PurpleAirFactory, "get_sensors", wraps=self.pf.get_sensors) as mock_get_sensors:
            # Simulate a retry scenario
            self.pf.retry_count = 0
            list(self.pf.get_sensors(sensor_dict, start, end))

            # Check if the method was retried
            self.assertGreater(mock_get_sensors.call_count, 1, "get_sensors should be retried on failure.")

    @patch.object(requests, "get")
    def test_get_sensors(self, mocked_get):
        """Test the get_sensors method of the PurpleAirFactory."""
        mocked_get.return_value.ok = True
        mocked_get.return_value.status_code = 200

        file = open("testing/test_data/purpleair_sensor_274866.csv", "r")
        mocked_get.return_value.text = file.read()
        file.close()

        start = dt.datetime(2025, 7, 7, 23, 0, 0)
        end = dt.datetime(2025, 7, 8, 0, 0, 0)
        sensor_dict = {"274866": {"stationary_box": None, "time_updated": None}}

        sensors = list(self.pf.get_sensors(sensor_dict, start, end))
        mocked_get.assert_called_once()

        self.assertEqual(len(sensors), 1, "There should be one sensor returned.")
        sensor = sensors[0]
        self.assertIsInstance(sensor, PurpleAirSensor, "The sensor should be an instance of PurpleAirSensor.")
        self.assertEqual(sensor.id, "274866", "The sensor ID should match the one in the test data.")
        self.assertIsNotNone(sensor.df, "The sensor DataFrame should not be None.")

        expected_df = pd.read_csv(StringIO(mocked_get.return_value.text), index_col="time_stamp")
        # check the number of columns and rows matches the sensor.df
        self.assertEqual(sensor.df.shape[0], expected_df.shape[0], "The number of rows in the sensor DataFrame should match the test data.")
        # latitude and longitude columns are not included in the sensor DataFrame
        self.assertEqual(sensor.df.shape[1], expected_df.shape[1] + 2, "The number of columns in the sensor DataFrame should match the test data.")


if __name__ == "__main__":
    unittest.main()
