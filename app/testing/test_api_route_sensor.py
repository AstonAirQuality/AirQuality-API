import unittest
from unittest import TestCase

from core.models import Sensors as ModelSensor
from core.models import SensorTypes as ModelSensorType
from fastapi.testclient import TestClient
from main import app
from testing.application_config import authenticate_client, database_config


class Test_Api_2_Sensor(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.client = TestClient(app)
        cls.client = authenticate_client(cls.client, role="admin")
        cls.db = database_config()
        cls.sensor_id = 1
        cls.sensor_type_id = 1

        # add a sensor type to the database
        try:
            result = cls.db.query(ModelSensorType).first()
            # if the sensor type does not exist then add it to the database and get the id
            if result is None:
                sensorType = ModelSensorType(name="test_sensor_type", description="test_sensor_type", properties={"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
                cls.db.add(sensorType)
                cls.db.commit()
                cls.sensor_type_id = sensorType.id
            else:
                cls.sensor_type_id = result.id

            # creating a test sensor
            res = cls.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
            if res is None:
                sensor = ModelSensor(lookup_id="test_sensor", serial_number="test_sensor", type_id=cls.sensor_type_id, active=True, user_id=None, stationary_box=None)
                cls.db.add(sensor)
                cls.db.commit()
                cls.sensor_id = sensor.id
            else:
                cls.sensor_id = res.id

        except Exception as e:
            cls.db.rollback()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        try:
            cls.db.delete(cls.db.query(ModelSensor).filter(ModelSensor.id == cls.sensor_id).first())
            cls.db.commit()
        except Exception as e:
            cls.db.rollback()

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    def test_1_db_connection(self):
        """Test that the database is connected"""
        self.assertIsNotNone(self.db)

    def test_2_post_sensor(self):
        """Test the post sensor route of the API."""

        sensor = {"lookup_id": "test_post_sensor", "serial_number": "test_post_sensor", "type_id": self.sensor_type_id, "active": True, "user_id": None, "stationary_box": None}

        response = self.client.post("/sensor", json=sensor)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensor)

        # check that the sensor was added to the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_post_sensor").first()
        self.assertEqual(db_sensor.lookup_id, "test_post_sensor")

    def test_3_post_plume_sensor(self):
        """Test the post sensor route of the API."""

        plume_serial_numbers = {"serial_numbers": ["02:00:00:00:48:45"]}

        response = self.client.post("/sensor/plume-sensors", json=plume_serial_numbers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"02:00:00:00:48:45": 18749})

        # check that the sensor was added to the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "18749").first()
        self.assertEqual(db_sensor.lookup_id, "18749")

    def test_4_post_duplicate_plume_sensor(self):
        """Test the post sensor route of the API."""

        # check that the sensor already exists in the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.serial_number == "02:00:00:00:48:45").first()
        self.assertEqual(db_sensor.serial_number, "02:00:00:00:48:45")

        plume_serial_numbers = {"serial_numbers": ["02:00:00:00:48:45"]}
        response = self.client.post("/sensor/plume-sensors", json=plume_serial_numbers)
        self.assertEqual(response.status_code, 409)

    def test_5_get_sensor(self):
        """Test the get sensor route of the API."""
        response = self.client.get("/sensor")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("lookup_id" in response.json()[0])

    def test_6_get_sensor_joined(self):
        """Test the get sensor route of the API."""
        response = self.client.get(
            "/sensor/joined/1/1", params={"join_sensor_types": True, "join_user": True, "columns": ["lookup_id", "serial_number", "type_id", "active", "user_id", "stationary_box"]}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue("type_name" in response.json()[0])
        self.assertTrue("username" in response.json()[0])

    def test_7_put_sensor(self):
        """Test the put sensor route of the API, by updating the sensor whose sensor_id is 1, with a stationary box."""
        stationary_box = "POLYGON((0 0,0 1,1 1,1 0,0 0))"
        sensor = {"lookup_id": "test_sensor", "serial_number": "test_sensor", "type_id": self.sensor_type_id, "active": True, "user_id": None, "stationary_box": stationary_box}

        response = self.client.put(f"/sensor/{self.sensor_id}", json=sensor)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), sensor)

        # check that the sensor was updated in the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.serial_number == "test_sensor").first()
        self.assertIsNotNone(db_sensor.stationary_box)

    def test_8_patch_sensor_active_state(self):
        """Test the patch sensor active state route of the API."""
        query_data = {"sensor_serialnumbers": "test_sensor", "active_state": False}
        response = self.client.patch(f"/sensor/active-status", params=query_data)
        self.assertEqual(response.status_code, 200)

        # check that the sensor was updated in the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.serial_number == "test_sensor").first()
        self.assertIsNotNone(db_sensor)
        self.assertEqual(db_sensor.active, False)

    def test_9_delete_sensor(self):
        """Test the delete sensor route of the API."""

        # create a sensor to delete
        sensor = ModelSensor(lookup_id="test_delete_sensor", serial_number="test_delete_sensor", type_id=self.sensor_type_id, active=True, user_id=None, stationary_box=None)
        self.db.add(sensor)
        self.db.commit()
        delete_sensor_id = sensor.id

        # delete the sensor
        response = self.client.delete(f"/sensor/{delete_sensor_id}")
        self.assertEqual(response.status_code, 200)

        # check that the sensor was deleted from the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.id == delete_sensor_id).first()
        self.assertIsNone(db_sensor)


if __name__ == "__main__":
    unittest.main()
