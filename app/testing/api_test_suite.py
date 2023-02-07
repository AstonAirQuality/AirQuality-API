import unittest
from unittest import TestCase, TestSuite

from testing.application_config import admin_session, database_config
from testing.test_api_route_sensor import Test_Api_Sensor
from testing.test_example import Test_Api_Example


def suite():
    """Test suite for all tests in the testing directory."""
    example_tests = unittest.TestLoader().loadTestsFromTestCase(Test_Api_Example)
    sensor_tests = unittest.TestLoader().loadTestsFromTestCase(Test_Api_Sensor)
    suite = unittest.TestSuite([sensor_tests, example_tests])
    return suite


if __name__ == "__main__":
    # run docker container with tests
    unittest.TextTestRunner().run(suite())
    # teardown docker container


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
