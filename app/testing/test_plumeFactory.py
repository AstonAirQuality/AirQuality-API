import datetime as dt
import json
import unittest  # The test framework
import zipfile
from io import StringIO
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

# from requests import Session
import pandas as pd
import requests
from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor
from dotenv import load_dotenv


class Test_plumeFactory(TestCase):
    """
    The following tests are for the Plume API Wrapper. Tests use mock data to ensure that the API wrapper is working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests
        :param cls: The class object
        """
        load_dotenv()
        # the env variables are set in the .env file. They must match the ones in the .env file
        cls.pf = PlumeFactory(env["PLUME_EMAIL"], env["PLUME_PASSWORD"], env["PLUME_FIREBASE_API_KEY"], env["PLUME_ORG_NUM"])
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

    @patch.object(requests.Session, "get")
    def test_fetch_lookup_ids_from_serial_Numbers(self, mocked_get):
        """Test fetch the correct lookup ids from a list of serial numbers.
        \n Uses mock data"""

        # with patch("requests.get") as mocked_get:
        mocked_get.return_value.ok = True

        file = open("testing/test_data/plume_LookupIds.json", "r")
        mocked_get.return_value.json.return_value = json.load(file)
        file.close()

        sensor_platforms = self.pf.fetch_lookup_ids(["02:00:00:00:48:45", "02:00:00:00:48:13"])

        mocked_get.assert_called_with("https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors".format(org=self.pf.org))

        expected = {"02:00:00:00:48:45": 18749, "02:00:00:00:48:13": 18699}
        self.assertEqual(sensor_platforms, expected)

    @patch.object(requests.Session, "get")
    def test_fetch_measurements_data_only(self, mocked_get):
        """Test fetch the sensor measurement data.
        \n Uses mock data"""

        sensor_id = "18749"
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

        file = open("testing/test_data/plume_measurements.json", "r")
        json_ = json.load(file)
        file.close()
        mocked_get.return_value.json.return_value = json_

        sensor_data = self.pf.get_sensor_measurement_data(sensor_id, start, end)

        mocked_get.assert_called_with(
            "https://api-preprod.plumelabs.com/2.0/user/organizations/{org}/sensors/{sensorId}/measures?start_date={start}&end_date={end}&offset={offset}".format(
                org=self.pf.org, sensorId=18749, start=int(start.timestamp()), end=int(end.timestamp()), offset=2000
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

        mocked_get.return_value.ok = True
        mocked_get.return_value.content = sensor_zip_bytes

        sensors = self.pf.extract_zip("https://example.com", include_measurements=False)

        mocked_get.assert_called_with("https://example.com", stream=True)

        for (sensor_id, sensor_data) in sensors:
            self.assertEqual(sensor_id, "18749")
            self.assertTrue(isinstance(sensor_data, StringIO))

    def test_fetch_location_data(self):
        """Test fetch the sensor data"""
        sensor_id = "18749"
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)
        link = "https://example.com"

        with patch.object(PlumeFactory, "extract_zip") as mocked_sensors_from_zip:
            mocked_sensors_from_zip.return_value = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

            sensors = self.pf.get_sensor_location_data([sensor_id], start, end, link)

            mocked_sensors_from_zip.assert_called_with(link, include_measurements=False)

            for sensor in sensors:
                self.assertEqual(sensor.id, "18749")
                self.assertTrue(len(sensor.df) > 0)
                self.assertEqual(sensor.df.columns.tolist(), ["latitude", "longitude"])
                break

    def test_fetch_sensor_stationary_no_gps(self):
        """Test fetch the sensor data"""
        sensor_id = "18749"
        stationary_box = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        sensor_dict = {sensor_id: stationary_box}
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

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

                mocked_sensor_location_only.assert_called_with([sensor_id], start, end, link=None)
                mocked_append_measurements.assert_not_called()
                # because this is a stationary sensor we expect the sensor to be returned with the measurement data only
                mocked_sensor_measurement_only.assert_called_with([sensor_id], start, end)

                self.assertEqual(len(sensors), 1)

                expectedColumns = [
                    "NO2",
                    "VOC",
                    "timestamp",
                    "particulatePM1",
                    "particulatePM2.5",
                    "particulatePM10",
                ]
                for sensor in sensors:
                    self.assertTrue(isinstance(sensor, PlumeSensor))
                    self.assertEqual(sensor.id, "18749")
                    for col in expectedColumns:
                        self.assertTrue(col in sensor.df.columns)
                    break

    def test_fetch_sensor_stationary_with_gps(self):
        """Test fetch the sensor data"""
        sensor_id = "18749"
        stationary_box = "POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10))"
        sensor_dict = {sensor_id: stationary_box}
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

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

                    mocked_sensor_location_only.assert_called_with([sensor_id], start, end, link=None)
                    mocked_append_measurements.assert_called_with(str(sensor_id), start, end)
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 1)

                    expectedColumns = ["NO2", "VOC", "timestamp", "latitude", "longitude", "particulatePM1", "particulatePM2.5", "particulatePM10"]

                    for sensor in sensors:
                        self.assertTrue(isinstance(sensor, PlumeSensor))
                        self.assertEqual(sensor.id, "18749")
                        for col in expectedColumns:
                            self.assertTrue(col in sensor.df.columns)
                        break

    def test_fetch_sensor_not_stationary_with_gps(self):
        """Same as above but with a non-stationary sensor"""
        sensor_id = "18749"
        stationary_box = None
        sensor_dict = {sensor_id: stationary_box}
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

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

                    mocked_sensor_location_only.assert_called_with([sensor_id], start, end, link=None)
                    mocked_append_measurements.assert_called_with(str(sensor_id), start, end)
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 1)

                    expectedColumns = ["NO2", "VOC", "timestamp", "latitude", "longitude", "particulatePM1", "particulatePM2.5", "particulatePM10"]

                    for sensor in sensors:
                        self.assertTrue(isinstance(sensor, PlumeSensor))
                        self.assertEqual(sensor.id, "18749")
                        for col in expectedColumns:
                            self.assertTrue(col in sensor.df.columns)
                        break

    def test_fetch_sensor_not_stationary_no_gps(self):
        """Same as above but with a non-stationary sensor"""
        sensor_id = "18749"
        stationary_box = None
        sensor_dict = {sensor_id: stationary_box}
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

        with patch.object(PlumeFactory, "get_sensor_location_data") as mocked_sensor_location_only:
            # bad zip data will be empty or will throw a bad zip file error so we set the return value to be empty to imitate this behavior
            mocked_sensor_location_only.return_value = []
            with patch.object(PlumeFactory, "get_sensor_measurement_data") as mocked_append_measurements:
                mocked_append_measurements.return_value = []

                with patch.object(PlumeFactory, "get_sensors_measurement_only") as mocked_sensor_measurement_only:

                    mocked_sensor_measurement_only.return_value = None

                    sensors = self.pf.get_sensors(sensor_dict, start, end)

                    mocked_sensor_location_only.assert_called_with([sensor_id], start, end, link=None)
                    mocked_append_measurements.assert_not_called()
                    mocked_sensor_measurement_only.assert_not_called()

                    self.assertEqual(len(sensors), 0)

    def test_fetch_sensor_merged_data_zip(self):
        """Test fetch the sensor data"""
        sensor_id = "18749"
        start = dt.datetime(2022, 9, 10)
        end = dt.datetime(2022, 9, 12)

        with patch.object(PlumeFactory, "extract_zip") as mocked_sensors_from_zip:
            mocked_sensors_from_zip.return_value = self.pf.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

            with patch.object(PlumeFactory, "get_zip_file_link") as mocked_get_zip_link:

                mocked_get_zip_link.return_value = "https://example.com"

                sensors = self.pf.get_sensors_merged_from_zip([sensor_id], start, end)

                mocked_get_zip_link.assert_called_with([sensor_id], start, end, include_measurements=True)
                mocked_sensors_from_zip.assert_called_with("https://example.com", include_measurements=True)

                self.assertTrue(isinstance(sensors, list))
                self.assertEqual(len(sensors), 1)

                expectedColumns = ["NO2", "VOC", "timestamp", "latitude", "longitude", "particulatePM1", "particulatePM2.5", "particulatePM10"]
                for sensor in sensors:
                    self.assertTrue(isinstance(sensor, PlumeSensor))
                    self.assertEqual(sensor.id, "18749")
                    for col in expectedColumns:
                        self.assertTrue(col in sensor.df.columns)
                    break


if __name__ == "__main__":
    unittest.main()
