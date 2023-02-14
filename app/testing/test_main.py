import datetime as dt
import unittest  # The test framework
import warnings
from unittest import TestCase
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from main import app


class Test_Api_Main(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.client = TestClient(app)
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
        response = self.client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello World"}


if __name__ == "__main__":
    unittest.main()
