import unittest
from unittest import TestCase, TestSuite

from testing.api.test_api_route_sensorType import Test_Api_Sensor_Type
from testing.application_config import admin_session, database_config


def suite():
    """Test suite for all tests in the testing directory."""
    sensorType_tests = unittest.TestLoader().loadTestsFromTestCase(Test_Api_Sensor_Type)
    suite = unittest.TestSuite([sensorType_tests])
    return suite


if __name__ == "__main__":
    # run docker container with tests
    unittest.TextTestRunner().run(suite())
    # teardown docker container


# TODO do api endpoint tests by making a request to the endpoint and checking the response
# create a test for each endpoint
# create a test docker container to run the tests in
