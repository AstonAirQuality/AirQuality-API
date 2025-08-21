import datetime as dt
import json
import unittest  # The test framework
import warnings
import zipfile
from io import StringIO
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

# from requests import Session
import pandas as pd
import requests
from dotenv import load_dotenv
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor


class Test_plumeFactory(TestCase):
    """
    The following tests are for the Plume API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        warnings.simplefilter("ignore", ResourceWarning)
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.pf = PlumeFactory(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])
        cls.expected_columns = [
            SensorMeasurementsColumns.NO2.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
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

    @patch.object(requests.Session, "get")
    def test_fetch_lookup_ids_from_serial_Numbers(self, mocked_get):
        """Test fetch the correct lookup ids from a list of serial numbers.
        \n Uses mock data"""

        # with patch("requests.get") as mocked_get:
        mocked_get.return_value.ok = True

        file = open("testing/test_data/plume_LookupIds.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        self.pf.login()
        sensor_platforms = self.pf.fetch_lookup_ids(["02:00:00:00:48:45", "02:00:00:00:48:13"])

        mocked_get.assert_called_with("https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors".format(org=self.pf.org))

        expected = {"02:00:00:00:48:45": 19651, "02:00:00:00:48:13": 18699}
        self.assertEqual(sensor_platforms, expected)

    @patch.object(requests.Session, "get")
    def test_fetch_measurements_data_only(self, mocked_get):
        """Test fetch the sensor measurement data.
        \n Uses mock data"""

        sensor_id = "19651"
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 22)

        file = open("testing/test_data/plume_measurements.json", "r")
        json_ = json.load(file)
        file.close()
        mocked_get.return_value.json.return_value = json_

        self.pf.login()
        sensor_data = self.pf.get_sensor_measurement_data(sensor_id, start, end)[0]

        mocked_get.assert_called_with(
            "https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors/{sensorId}/measures?start_date={start}&end_date={end}&offset={offset}".format(
                org=self.pf.org, sensorId=19651, start=int(start.timestamp()), end=int(end.timestamp()), offset=0
            )
        )

        expected = json_["measures"]
        self.assertEqual(len(sensor_data), len(expected))
        self.assertTrue(isinstance(sensor_data, list))

    @patch.object(requests, "get")
    def test_extract_zip(self, mocked_get):
        """Test extract the zip file"""

        with open("./testing/test_data/plume_sensorData.zip", "rb") as f:
            sensor_zip_bytes = f.read()
            f.close()

        mocked_get.return_value.ok = True
        mocked_get.return_value.content = sensor_zip_bytes

        sensors = self.pf.extract_zip_from_link("https://example.com", include_measurements=False)

        mocked_get.assert_called_with("https://example.com", stream=True)

        for sensor_id, sensor_data in sensors:
            self.assertEqual(sensor_id, "19651")
            self.assertTrue(isinstance(sensor_data, StringIO))

    def test_fetch_location_data(self):
        """Test fetch the sensor data"""
        sensor_id = "19651"
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)
        link = "https://example.com"
        with patch.object(requests, "get") as mocked_get:
            mocked_get.return_value.ok = True
            mocked_get.return_value.content = open("./testing/test_data/plume_sensorData.zip", "rb").read()
            with patch.object(PlumeFactory, "extract_zip_content") as mocked_sensors_from_zip:
                mocked_sensors_from_zip.return_value = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

                sensors = self.pf.get_sensor_location_data([sensor_id], start, end, link)

                mocked_sensors_from_zip.assert_called()

                for sensor in sensors:
                    self.assertEqual(sensor.id, "19651")
                    self.assertTrue(len(sensor.df) > 0)
                    self.assertEqual(sensor.df.columns.tolist(), ["timestamp", "latitude", "longitude"])
                    break

    def test_fetch_sensor_stationary_no_gps(self):
        """Test fetch the sensor data"""
        sensor_id = "19651"
        stationary_box = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        sensor_dict = {sensor_id: {"stationary_box": stationary_box, "time_updated": None}}
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)

        with patch.object(PlumeFactory, "get_sensor_location_data") as mocked_sensor_location_only:
            # bad zip data will be empty or will throw a bad zip file error so we set the return value to be empty to imitate this behavior
            mocked_sensor_location_only.return_value = []
            with patch.object(PlumeFactory, "get_sensor_measurement_data") as mocked_append_measurements:
                mocked_append_measurements.return_value = []

            with patch.object(PlumeFactory, "get_sensors_measurement_only") as mocked_sensor_measurement_only:
                file = open("testing/test_data/plume_measurements.json", "r")
                json_ = json.load(file)
                file.close()

                mocked_sensor_measurement_only.return_value = [PlumeSensor.from_json(sensor_id, json_["measures"])]

                sensors = self.pf.get_sensors(sensor_dict, start, end)

                mocked_sensor_location_only.assert_called_with(sensor_id, start, end, link=None)
                mocked_append_measurements.assert_not_called()
                # because this is a stationary sensor we expect the sensor to be returned with the measurement data only
                mocked_sensor_measurement_only.assert_called_with([sensor_id], start, end)

                self.assertEqual(len(sensors), 1)

                for sensor in sensors:
                    self.assertTrue(isinstance(sensor, PlumeSensor))
                    self.assertEqual(sensor.id, "19651")
                    for col in self.expected_columns:
                        self.assertTrue(col in sensor.df.columns)
                    break

    def test_fetch_sensor_stationary_with_gps(self):
        """Test fetch the sensor data does not call get measurements only function"""
        sensor_id = "19651"
        stationary_box = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        sensor_dict = {sensor_id: {"stationary_box": stationary_box, "time_updated": None}}
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)

        with patch.object(PlumeFactory, "get_sensor_location_data") as mocked_sensor_location_only:
            sensor_items = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)
            (mock_id, mock_buffer) = next(sensor_items)
            mocked_sensor_location_only.return_value = [PlumeSensor.from_csv(mock_id, mock_buffer)]

            with patch.object(PlumeFactory, "get_sensor_measurement_data") as mocked_append_measurements:
                file = open("testing/test_data/plume_measurements.json", "r")
                json_ = json.load(file)
                file.close()
                mocked_append_measurements.return_value = json_["measures"]

                with patch.object(PlumeFactory, "get_sensors_measurement_only") as mocked_sensor_measurement_only:
                    mocked_sensor_measurement_only.return_value = None

                    sensors = self.pf.get_sensors(sensor_dict, start, end)

                    mocked_sensor_location_only.assert_called_with(sensor_id, start, end, link=None)
                    mocked_append_measurements.assert_called_with(str(sensor_id), start, end)
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 1)

                    for sensor in sensors:
                        self.assertTrue(isinstance(sensor, PlumeSensor))
                        self.assertEqual(sensor.id, "19651")
                        for col in self.expected_columns:
                            self.assertTrue(col in sensor.df.columns)
                        break

    def test_fetch_sensor_not_stationary_with_gps(self):
        """Same as above but with a non-stationary sensor"""
        sensor_id = "19651"
        stationary_box = None
        sensor_dict = {sensor_id: {"stationary_box": stationary_box, "time_updated": None}}
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)

        with patch.object(PlumeFactory, "get_sensor_location_data") as mocked_sensor_location_only:
            sensor_items = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)
            (mock_id, mock_buffer) = next(sensor_items)
            mocked_sensor_location_only.return_value = [PlumeSensor.from_csv(mock_id, mock_buffer)]

            with patch.object(PlumeFactory, "get_sensor_measurement_data") as mocked_append_measurements:
                file = open("testing/test_data/plume_measurements.json", "r")
                json_ = json.load(file)
                file.close()
                mocked_append_measurements.return_value = json_["measures"]

                with patch.object(PlumeFactory, "get_sensors_measurement_only") as mocked_sensor_measurement_only:
                    mocked_sensor_measurement_only.return_value = None

                    sensors = self.pf.get_sensors(sensor_dict, start, end)

                    mocked_sensor_location_only.assert_called_with(sensor_id, start, end, link=None)
                    mocked_append_measurements.assert_called_with(str(sensor_id), start, end)
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 1)

                    for sensor in sensors:
                        self.assertTrue(isinstance(sensor, PlumeSensor))
                        self.assertEqual(sensor.id, "19651")
                        for col in self.expected_columns:
                            self.assertTrue(col in sensor.df.columns)
                        break

    def test_fetch_sensor_not_stationary_no_gps(self):
        """Same as above but with a non-stationary sensor"""
        sensor_id = "19651"
        stationary_box = None
        sensor_dict = {sensor_id: {"stationary_box": stationary_box, "time_updated": None}}
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)

        with patch.object(PlumeFactory, "get_sensor_location_data") as mocked_sensor_location_only:
            # bad zip data will be empty or will throw a bad zip file error so we set the return value to be empty to imitate this behavior
            mocked_sensor_location_only.return_value = []
            with patch.object(PlumeFactory, "get_sensor_measurement_data") as mocked_append_measurements:
                mocked_append_measurements.return_value = []

                with patch.object(PlumeFactory, "get_sensors_measurement_only") as mocked_sensor_measurement_only:
                    mocked_sensor_measurement_only.return_value = None

                    sensors = self.pf.get_sensors(sensor_dict, start, end)

                    mocked_sensor_location_only.assert_called_with(sensor_id, start, end, link=None)
                    mocked_append_measurements.assert_not_called()
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 0)

    def test_fetch_sensor_merged_data_zip(self):
        """Test fetch the sensor data"""
        sensor_id = "19651"
        start = dt.datetime(2023, 9, 21)
        end = dt.datetime(2023, 9, 26)

        data = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        with patch.object(requests, "get") as mocked_get:
            mocked_get.return_value.ok = True
            mocked_get.return_value.content = open("./testing/test_data/plume_sensorData.zip", "rb").read()

            with patch.object(PlumeFactory, "extract_zip_content") as mocked_sensors_from_zip:
                mocked_sensors_from_zip.return_value = data

                with patch.object(PlumeFactory, "get_zip_file_link") as mocked_get_zip_link:
                    mocked_get_zip_link.return_value = "https://example.com"

                    sensors = self.pf.get_sensors_merged_from_zip([sensor_id], start, end)

                    mocked_get_zip_link.assert_called_with([sensor_id], start, end, include_measurements=True)
                    mocked_sensors_from_zip.assert_called_once()

                    self.assertTrue(isinstance(sensors, list))
                    self.assertEqual(len(sensors), 1)
                    for sensor in sensors:
                        self.assertTrue(isinstance(sensor, PlumeSensor))
                        self.assertEqual(sensor.id, "19651")
                        for col in self.expected_columns:
                            self.assertTrue(col in sensor.df.columns)
                        break


if __name__ == "__main__":
    unittest.main()
