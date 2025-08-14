import datetime as dt
import json
import unittest  # The test framework
import warnings
from os import environ as env
from unittest import TestCase
from unittest.mock import MagicMock, patch

import pandas as pd
import requests
from dotenv import load_dotenv
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.factories.sensorCommunity_factory import SensorCommunityFactory
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor


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
        cls.expected_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_PRESSURE.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
        cls.expected_columns_2 = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
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

    def test_get_sensors_csv(self):
        """Test fetch the correct sensor data from csv.
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

            sensors = list(self.scf.get_sensors_from_csv(sensor_dict, start, end))

            self.assertEqual(len(sensors), 1)

            sensor = sensors[0]
            self.assertTrue(isinstance(sensor, SensorCommunitySensor))
            self.assertEqual(sensor.id, sensor_id)
            self.assertTrue(isinstance(sensor.df, pd.DataFrame))
            # check that the dataframe contains the correct columns in any order
            self.assertEqual(
                set(sensor.df.columns.tolist()),
                set(self.expected_columns),
            )

    def test_prepare_sensor_platform_dict(self):
        """Test prepare the correct sensor platform dictionary.
        \n Uses mock data"""

        start = dt.datetime(2023, 4, 1)
        sensor_dict = {"60641,SDS011,60642,BME280": {"stationary_box": None, "time_updated": None}}

        sensor_platforms = self.scf.prepare_sensor_platform_dict(sensor_dict, start)
        expected = {"60641,SDS011,60642,BME280": {"60641": "SDS011", "60642": "BME280", "startDate": start}}
        self.assertEqual(sensor_platforms, expected)

    @patch.object(requests, "get")
    def test_get_sensor_columns_from_db(self, mocked_get):
        """Test fetch the correct sensor columns from the API/database.
        \n Uses mock data"""

        mocked_get.return_value.ok = True

        file = open("testing/test_data/sensorCommunityColumns.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        sensor_columns = self.scf.get_columns_from_db()
        expected = {
            "bme280_humidity": "float",
            "bme280_pressure": "float",
            "bme280_pressure_at_sealevel": "float",
            "bme280_temperature": "float",
            "bmp180_pressure": "float",
            "bmp180_pressure_at_sealevel": "float",
            "bmp180_temperature": "float",
            "bmp280_pressure": "float",
            "bmp280_pressure_at_sealevel": "float",
            "bmp280_temperature": "float",
            "dht22_humidity": "float",
            "dht22_temperature": "float",
            "ds18b20_temperature": "float",
            "hpm_p1": "float",
            "hpm_p2": "float",
            "htu21d_humidity": "float",
            "htu21d_temperature": "float",
            "ips7100_p0": "float",
            "ips7100_p1": "float",
            "ips7100_p2": "float",
            "noise_LA_max": "float",
            "noise_LA_min": "float",
            "noise_LAeq": "float",
            "noise_LAeq_delog": "float",
            "npm_p0": "float",
            "npm_p1": "float",
            "npm_p2": "float",
            "pms_p0": "float",
            "pms_p1": "float",
            "pms_p2": "float",
            "ppd42ns_p1": "float",
            "ppd42ns_p2": "float",
            "sds011_p1": "float",
            "sds011_p2": "float",
            "sht_humidity": "float",
            "sht_temperature": "float",
            "sps30_p0": "float",
            "sps30_p1": "float",
            "sps30_p2": "float",
            "sps30_p4": "float",
        }
        self.assertEqual(sensor_columns, expected)

    @patch.object(requests, "get")
    def test_get_sensors(self, mocked_get):
        """Test fetch the correct sensor data from the API.
        \n Uses mock data"""

        mocked_get.return_value.ok = True

        file = open("testing/test_data/sensorCommunity.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        start = dt.datetime(2023, 10, 30)
        end = dt.datetime(2023, 10, 31)
        sensor_dict = {"83636,SDS011,83637,DHT22": {"stationary_box": None, "time_updated": None}}

        sensors = list(self.scf.get_sensors(sensor_dict, start, end))
        self.assertEqual(len(sensors), 1)

        sensor = sensors[0]
        self.assertTrue(isinstance(sensor, SensorCommunitySensor))
        self.assertEqual(sensor.id, "83636,SDS011,83637,DHT22")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        # check that the dataframe contains the correct columns in any order
        self.assertEqual(
            set(sensor.df.columns.tolist()),
            set(self.expected_columns_2),
        )


if __name__ == "__main__":
    unittest.main()
