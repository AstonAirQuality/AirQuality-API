import datetime as dt
import unittest  # The test framework

# enviroment variables dependacies
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

from core.models import SensorTypes as ModelSensorType
from testing.application_config import admin_session, database_config


class Test_Api_Sensor_Type(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.session = admin_session()
        cls.db = database_config()
        cls_sensor_type_id = 1

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

    def test_db_connection(self):
        """Test that the database is connected"""
        self.assertIsNotNone(self.db)
        self.db.query(ModelSensorType).first()

    def test_post_sensor_type(self):
        """Test the post sensor type route of the API."""

        sensorType = {"name": "plume", "description": "single sensor platform", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}

        response = self.session.post("http://localhost:8000/sensor-type", json=sensorType)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensorType)

        # check that the sensor was added to the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.name == "plume").first()
        self.assertEqual(db_sensor_type.name, "plume")

    def test_get_sensor_type(self):
        """Test the get sensor type route of the API."""

        expected_response = [{"id": 1, "name": "plume", "description": "single sensor platform", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}]
        response = self.session.get("http://localhost:8000/sensor-type")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    def test_get_sensor_type_paginated(self):
        """Test the get sensor type paginated route of the API."""

        expected_response = [{"id": 1, "name": "plume", "description": "single sensor platform", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}]
        response = self.session.get("http://localhost:8000/sensor-type/1/1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected_response)

    def test_put_sensor_type(self):
        """Test the put sensor type route of the API."""

        sensorType = {"name": "plume", "description": "updated description", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}

        response = self.session.put("http://localhost:8000/sensor-type/1", json=sensorType)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensorType)

        # check that the sensor was updated to the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.name == "plume").first()
        self.assertEqual(db_sensor_type.description, "updated description")

    def test_delete_sensor_type(self):
        """Test the delete sensor type route of the API."""

        response = self.session.delete("http://localhost:8000/sensor-type/1")
        self.assertEqual(response.status_code, 200)

        # check that the sensor was deleted from the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.name == "plume").first()
        self.assertIsNone(db_sensor_type)


if __name__ == "__main__":
    unittest.main()


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
