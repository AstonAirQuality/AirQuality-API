import unittest
from unittest import TestCase

from testing.application_config import admin_session, database_config
from testing.test_api_route_sensor import Test_Api_Sensor


class Test_Api_Example(TestCase):
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

    def test_example(self):
        """Test that the database is connected"""
        self.assertEqual(1, 1)

    def test_example2(self):
        """Test that the database is connected"""
        self.assertEqual(1, 1)


if __name__ == "__main__":
    unittest.main()


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
