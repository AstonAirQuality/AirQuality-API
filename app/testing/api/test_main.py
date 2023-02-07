import datetime as dt
import unittest  # The test framework
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from main import app

# from routers.sensors import get_sensors

client = TestClient(app)


class Test_Api(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        pass

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

    # TODO do api endpoint tests by making a request to the endpoint and checking the response
    # create a test for each endpoint
    # create a test docker container to run the tests in

    """Example test reading sensor"""

    def test_read_main(self):
        """Test the main route of the API."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}

    # @patch("main.root", return_value={"message": "Hello World"})
    # def test_root(self, mocked_get):
    #     """Test the main route of the API."""
    #     response = client.get("/")
    #     mocked_get.assert_called_once()
    #     assert response.status_code == 200
    #     assert response.json() == {"message": "Hellos World"}

    # @patch("routers.bgtasks.get_background_tasks", return_value={"message": "Hello World"})
    # def test_bg(self, mocked_get):
    #     """Test the main route of the API."""
    #     response = client.get("/api-task")
    #     log_timestamp = dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")

    #     mocked_get.assert_called_once()
    #     assert response.status_code == 200
    #     assert response.json() == {"task_id": log_timestamp, "task_message": "task sent to backend"}

    # @patch("routers.sensors.get_sensors", return_value={"message": "Hello World"})
    # def test_read_Sensor(self, mocked_get):
    #     """Test the sensor route of the API."""
    #     response = client.get("/sensor")

    #     assert response.status_code == 200
    #     assert response.json() == {"message": "Hello World"}


if __name__ == "__main__":
    unittest.main()
