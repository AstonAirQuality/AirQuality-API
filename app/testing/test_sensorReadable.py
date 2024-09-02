import datetime as dt
import json
import unittest  # The test framework
import warnings
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from core.schema import SensorSummary as SchemaSensorSummary
from routers.services.formatting import JsonToSensorReadable
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor
from sensor_api_wrappers.data_transfer_object.sensor_readable import SensorReadable


class Test_sensorReadable(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.stationaryBox = "POLYGON ((-1.8364709615707395 52.42585638758735, -1.8365299701690674 52.42562740611671, -1.8360203504562376 52.42557179615147, -1.8359881639480589 52.42583676065077, -1.8364709615707395 52.42585638758735))"
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

    def test_SensorReadable_from_db(self):
        file = open("./testing/test_data/test_sensor_fromdb.json", "r")
        results = json.load(file)
        file.close()
        sensors = JsonToSensorReadable(results)

        for sensor in sensors:
            self.assertTrue(isinstance(sensor[0], SensorReadable))
            self.assertEqual(sensor[1], "test_sensor_type")

    def test_AveragesConversion_from_db(self):
        file = open("./testing/test_data/test_sensor_fromdb.json", "r")
        results = json.load(file)
        file.close()
        sensors = JsonToSensorReadable(results)

        for sensor, sensorType in sensors:
            self.assertEqual(sensorType, "test_sensor_type")
            self.assertTrue(isinstance(sensor, SensorReadable))
            measurements_columns = sensor.ConvertDFToAverages(["mean", "count"], "H")
            for column in measurements_columns:
                self.assertTrue((column, "mean") in sensor.df.columns)
                self.assertTrue((column, "count") in sensor.df.columns)

    def test_SensorReadable_to_geojson(self):
        file = open("./testing/test_data/test_sensor_fromdb.json", "r")
        results = json.load(file)
        file.close()
        sensors = JsonToSensorReadable(results)

        for sensor, sensorType in sensors:
            self.assertEqual(sensorType, "test_sensor_type")
            self.assertTrue(isinstance(sensor, SensorReadable))
            geojson = sensor.to_geojson(["mean", "count"], "H")
            self.assertTrue(isinstance(geojson, dict))
            self.assertTrue("features" in geojson)
            self.assertTrue("type" in geojson)
            self.assertTrue("geometry" in geojson["features"][0])
            self.assertTrue("properties" in geojson["features"][0])

            # # NOTE: if you want to write the output to file, comment out the following lines
            # with open("./testing/test_data/output/geojson.json", "w") as file:
            #     file.write(json.dumps(geojson, indent=4, default=str))


if __name__ == "__main__":
    unittest.main()
