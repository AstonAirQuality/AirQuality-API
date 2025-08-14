import unittest
import warnings
from unittest import TestCase

from core.models import SensorTypes as ModelSensorType
from fastapi.testclient import TestClient
from main import app
from testing.application_config import authenticate_client, database_config


class Test_Api_1_Sensor_Type(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.client = TestClient(app)
        cls.client = authenticate_client(cls.client, role="admin")
        cls.db = database_config()
        pass

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        cls.db.close()

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    def test_1_db_connection(self):
        """Test that the database is connected"""
        self.assertIsNotNone(self.db)

    def test_2_post_sensor_type(self):
        """Test the post sensor type route of the API."""

        sensorType = {"name": "test_sensor_type", "description": "test_sensor_type", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}

        response = self.client.post("/sensor-platform-type", json=sensorType)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensorType)

        # check that the sensor was added to the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.name == "test_sensor_type").first()
        self.assertEqual(db_sensor_type.name, "test_sensor_type")

    def test_3_get_sensor_type(self):
        """Test the get sensor type route of the API."""
        response = self.client.get("/sensor-platform-type")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("id" in response.json()[0])

    def test_4_get_sensor_type_paginated(self):
        """Test the get sensor type paginated route of the API."""
        response = self.client.get("/sensor-platform-type/1/1")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("id" in response.json()[0])

    def test_5_put_sensor_type(self):
        """Test the put sensor type route of the API."""

        sensorType = {"name": "test_sensor_type", "description": "updated description", "properties": {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"}}

        response = self.client.put("/sensor-platform-type/1", json=sensorType)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensorType)

        # check that the sensor was updated to the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.id == 1).first()
        self.assertEqual(db_sensor_type.description, "updated description")

    def test_6_delete_sensor_type(self):
        """Test the delete sensor type route of the API."""

        # create a sensor type to delete
        sensor_type = ModelSensorType(name="delete_test", description="test", properties={"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
        self.db.add(sensor_type)
        self.db.commit()

        # get the id of the sensor type
        sensor_type_id = self.db.query(ModelSensorType).filter(ModelSensorType.name == "delete_test").first().id

        response = self.client.delete(f"/sensor-type/{sensor_type_id}")
        self.assertEqual(response.status_code, 200)

        # check that the sensor was deleted from the database
        db_sensor_type = self.db.query(ModelSensorType).filter(ModelSensorType.name == "test").first()
        self.assertIsNone(db_sensor_type)


if __name__ == "__main__":
    unittest.main()
