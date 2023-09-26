import datetime as dt
import unittest  # The test framework
import warnings
from os import environ as env
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
from dotenv import load_dotenv
from sensor_api_wrappers.concrete.factories.sensorCommunity_factory import (
    SensorCommunityFactory,
)
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import (
    SensorCommunitySensor,
)


class MockResponse:
    def __init__(self, content):
        self.content = content
        self.status_code = 200
        self.ok = True


class Test_sensorCommunityFactory(TestCase):
    """The following tests are for the sensorCommunity API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected."""

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        warnings.simplefilter("ignore", ResourceWarning)
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.scf = SensorCommunityFactory(env["SC_USERNAME"], env["SC_PASSWORD"])
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

    # @patch.object(requests, "get")
    # def test_fetch_lookup_ids(self, mocked_get):
    #     """Test fetch the correct lookup ids.
    #     \n Uses mock data"""

    #     mocked_get.return_value.ok = True

    #     file = open("testing/test_data/Zephyr_LookupIds.json", "r")
    #     mocked_get.return_value.json.return_value = json.load(file)
    #     file.close()

    #     sensor_platforms = list(self.zf.fetch_lookup_ids())

    #     mocked_get.assert_called_with(f"https://data.earthsense.co.uk/zephyrsForUser/{self.zf.username}/{self.zf.password}")

    #     expected = ["814", "821"]
    #     self.assertEqual(sensor_platforms, expected)

    def test_get_sensors(self):
        """Test fetch the correct sensor data.
        \n Uses mock data"""

        responses = []

        file = open("testing/test_data/2023-04-01_sds011_sensor_60641.csv", "r")
        responses.append(file.read().encode())
        file.close()

        file = open("testing/test_data/2023-04-01_bme280_sensor_60642.csv", "r")
        responses.append(file.read().encode())
        file.close()

        # with patch.multiple("requests", get=MagicMock(side_effect=MockResponse.generateMockResponses)) as mock_requests:
        with patch.multiple("requests", get=MagicMock(side_effect=[MockResponse(content=responses[0]), MockResponse(content=responses[1])])) as mock_requests:
            start = dt.datetime(2023, 4, 1)
            end = dt.datetime(2023, 4, 1)
            sensor_id = "60641,SDS011,60642,BME280"
            sensor_dict = {sensor_id: {"stationary_box": "POLYGON ((-1.5 53.5, -1.5 54.5, -0.5 54.5, -0.5 53.5, -1.5 53.5))", "time_updated": None}}
            # filename = "2023-04-01_bme280_sensor_60642.csv"

            sensors = list(self.scf.get_sensors(sensor_dict, start, end))

            self.assertEqual(len(sensors), 1)

            expected_columns = ["particulatePM10", "particulatePM2.5", "ambPressure", "humidity", "latitude", "longitude", "tempC", "timestamp"]

            for sensor in sensors:
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
