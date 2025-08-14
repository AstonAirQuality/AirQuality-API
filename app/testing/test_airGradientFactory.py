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
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.factories.airGradient_factory import AirGradientFactory
from sensor_api_wrappers.concrete.products.airGradient_sensor import AirGradientSensor


class Test_airGradientFactory(TestCase):
    """
    The following tests are for the airGradient API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        warnings.simplefilter("ignore", ResourceWarning)
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.agf = AirGradientFactory(
            api_key=env["AIR_GRADIENT_API_KEY"],
        )
        cls.expected_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.PM1_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM0_3_COUNT.value,
            SensorMeasurementsColumns.CO2.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.VOC_INDEX.value,
            SensorMeasurementsColumns.NOX_INDEX.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests
        :param cls: The class object
        """

    @patch.object(requests, "get")
    def test_get_sensors(self, mocked_get):
        """Test the get_sensors method of the AirGradientFactory.

        Args:
            mocked_get: Mocked requests.get method.
        """

        mocked_get.return_value.status_code = 200
        mocked_get.return_value.ok = True

        file = open("testing/test_data/airgradient_163763_data.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        start_date = dt.datetime(2025, 7, 20)
        end_date = dt.datetime(2025, 7, 25)
        sensor_id = "163763"
        sensor_dict = {sensor_id: {"stationary_box": None, "time_updated": None}}

        sensors = list(self.agf.get_sensors(sensor_dict, start_date, end_date))
        # assert called 3 times
        mocked_get.assert_called()
        self.assertEqual(len(sensors), 3)
        self.assertIsInstance(sensors[0], AirGradientSensor)
        self.assertEqual(sensors[0].id, sensor_id)
        self.assertIsNotNone(sensors[0].df)
        # Check if the DataFrame has the expected columns (16 columns)
        self.assertEqual(sensors[0].df.shape[1], 16)
        # Check if the DataFrame has the expected columns
        self.assertListEqual(list(sensors[0].df.columns), self.expected_columns)
