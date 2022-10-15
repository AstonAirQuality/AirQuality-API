import datetime as dt
import unittest  # The test framework
from unittest import TestCase
from unittest.mock import Mock, patch

from api_wrappers.scraperWrapper import ScraperWrapper
from requests import Session


class Test_scraperWraper(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.apiWrapper = ScraperWrapper()
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

    def test_fetch_plume_lookup_from_serialnumbers(self):
        sensor_platforms = self.apiWrapper.fetch_plume_platform_lookupids(["02:00:00:00:48:45", "02:00:00:00:48:13"])
        expected = {"02:00:00:00:48:45": 18749, "02:00:00:00:48:13": 18699}
        self.assertEqual(expected, sensor_platforms)

    # def test_fetch_plume_data(self):
    #     """Test fetch data from Plume API

    #     requires recent valid data to be available (location + measurements)
    #     """

    #     sensorsids = {18749: None}
    #     start = dt.datetime(2021, 7, 22)
    #     end = dt.datetime(2021, 7, 23)

    #     sensors = self.apiWrapper.fetch_plume_sensors(start, end, sensorsids)
    #     self.assertIsNotNone(sensors)


if __name__ == "__main__":
    unittest.main()
