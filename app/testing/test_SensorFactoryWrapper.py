import datetime as dt
import unittest  # The test framework
from unittest import TestCase
from unittest.mock import Mock, patch

from api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from requests import Session


class Test_SensorFactoryWrapper(TestCase):
    """
    The following tests are for the SensorFactoryWrapper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.apiWrapper = SensorFactoryWrapper()
        pass

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        # cls.apiWrapper.pf.__session.close()
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

    def test_fetch_zephyr_lookup_ids(self):
        sensor_platforms = self.apiWrapper.fetch_zephyr_platform_lookupids()
        # assert contains 814 and 821
        self.assertIn("814", sensor_platforms)
        self.assertIn("821", sensor_platforms)


if __name__ == "__main__":
    unittest.main()
