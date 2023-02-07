import datetime as dt
import unittest  # The test framework

# enviroment variables dependacies
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorType
from testing.application_config import admin_session, database_config


class Test_Api_Sensor(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.session = admin_session()
        cls.db = database_config()
        cls.sensor_id = 1

        # add a sensor type to the database
        try:
            result = cls.db.query(ModelSensorType).first()
            if result is None:
                sensorType = ModelSensorType(name="plume", description="description", properties={"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
                cls.db.add(sensorType)
                cls.db.commit()

            # if the test sensor is already in the database then get the id
            res = cls.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
            if res is not None:
                cls.sensor_id = res.id

        except Exception as e:
            cls.db.rollback()

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
        self.db.query(ModelSensor).first()

    def test_post_sensor(self):
        """Test the post sensor route of the API."""

        sensor = {"lookup_id": "test_sensor", "serial_number": "test_sensor", "type_id": 1, "active": True, "user_id": None, "stationary_box": None}

        response = self.session.post("http://localhost:8000/sensor", json=sensor)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensor)

        # check that the sensor was added to the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
        self.assertEqual(db_sensor.lookup_id, "test_sensor")

    def test_post_plume_sensor(self):
        """Test the post sensor route of the API."""

        plume_serial_numbers = {"serial_numbers": ["02:00:00:00:48:45"]}

        response = self.session.post("http://localhost:8000/sensor/plume-sensors", json=plume_serial_numbers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"02:00:00:00:48:45": 18749})

        # check that the sensor was added to the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "18749").first()
        self.assertEqual(db_sensor.lookup_id, "18749")

    def test_get_sensor(self):
        """Test the get sensor route of the API."""
        response = self.session.get("http://localhost:8000/sensor")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("lookup_id" in response.json()[0])

    def test_put_sensor(self):
        """Test the put sensor route of the API, by updating the sensor whose sensor_id is 1, with a stationary box."""
        stationary_box = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
        sensor = {"lookup_id": "test_sensor", "serial_number": "test_sensor", "type_id": 1, "active": True, "user_id": None, "stationary_box": stationary_box}

        response = self.session.put(f"http://localhost:8000/sensor/{self.sensor_id}", json=sensor)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensor)

        # check that the sensor was updated in the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
        self.assertIsNotNone(db_sensor.stationary_box)

    def test_patch_sensor_active_state(self):
        """Test the patch sensor active state route of the API."""
        query_data = {"sensor_serialnumbers": "test_sensor", "active_state": False}
        response = self.session.patch(f"http://localhost:8000/sensor/active-status", params=query_data)
        self.assertEqual(response.status_code, 200)

        # check that the sensor was updated in the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
        self.assertEqual(db_sensor.active, False)

    def test_delete_sensor(self):
        """Test the delete sensor route of the API."""
        response = self.session.delete(f"http://localhost:8000/sensor/{self.sensor_id}")
        self.assertEqual(response.status_code, 200)

        # check that the sensor was deleted from the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.id == self.sensor_id).first()
        self.assertIsNone(db_sensor)


if __name__ == "__main__":
    unittest.main()


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
