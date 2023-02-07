import datetime as dt
import unittest  # The test framework

# enviroment variables dependacies
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

import requests
from core.models import Sensors as ModelSensor

# sqlalchemy dependacies
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


class Test_Api(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.session = requests.Session()
        response = requests.post("http://localhost:8000/auth/dev-login", params={"uid": "admin", "role": "admin"})
        cls.session.headers.update({"Content-Type": "application/json"})
        cls.session.headers.update({"Authorization": f"Bearer {response.json()}"})

        # docker database connection
        engine = create_engine("postgresql+psycopg2://postgres:password@localhost:5432/air_quality_db")
        # Base = declarative_base()
        SessionLocal = sessionmaker(bind=engine)
        cls.db = SessionLocal()

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
        assert self.db is not None
        self.db.query(ModelSensor).first()
        db_sensor = self.db.query(ModelSensor).first()
        assert db_sensor is not None

    def test_root(self):
        """Test the main route of the API."""
        response = requests.get("http://localhost:8000/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    def test_get_user(self):
        """Test the get user route of the API."""

        response = self.session.get("http://localhost:8000/user")
        assert response.status_code == 200

    def test_add_sensor(self):
        """Test the main route of the API."""

        sensor = {"lookup_id": "test_sensor", "serial_number": "test_sensor", "type_id": 1, "active": True, "user_id": None, "stationary_box": None}

        response = self.session.post("http://localhost:8000/sensor", json=sensor)
        assert response.status_code == 200
        assert response.json() == sensor

        # check that the sensor was added to the database
        db_sensor = self.db.query(ModelSensor).filter(ModelSensor.lookup_id == "test_sensor").first()
        assert db_sensor.lookup_id == "test_sensor"


if __name__ == "__main__":
    unittest.main()


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
