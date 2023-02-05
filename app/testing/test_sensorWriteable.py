import datetime as dt
import json
import unittest  # The test framework
import zipfile
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor
from api_wrappers.data_transfer_object.sensor_writeable import SensorWritable
from core.schema import SensorSummary as SchemaSensorSummary


class Test_sensorWritable(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
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

    def test_sensorSummary_from_plume_with_stationaryBox(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)
        sensor = SensorWritable(sensor.id, sensor.df)  # type cast to SensorWritable for readability

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=self.stationaryBox)
        self.assertIsNotNone(sensor_summaries)

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)

            self.assertTrue(sensor_summary.geom == self.stationaryBox)
            self.assertTrue(sensor_summary.measurement_count > 0)
            self.assertIsNotNone(sensor_summary.measurement_data)
            self.assertEqual(sensor_summary.stationary, True)

    def test_sensorSummary_from_plume_no_stationaryBox(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)
        sensor = SensorWritable(sensor.id, sensor.df)  # type cast to SensorWritable for readability

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=None)
        self.assertIsNotNone(sensor_summaries)

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)

            # Skip sensor summaries that have no geometries (These sensors will not be included in the database. They can only exist through fetching merged csv files)
            # TODO validate geomerty is in WKT format
            if sensor_summary.geom != None:
                print(sensor_summary.geom)
                expectedGeom = "POLYGON((-1.83631 52.425392,-1.83631 52.425603,-1.836288 52.425603,-1.836288 52.425392,-1.83631 52.425392))"
                self.assertTrue(sensor_summary.geom == expectedGeom)

            self.assertTrue(sensor_summary.measurement_count > 0)
            self.assertIsNotNone(sensor_summary.measurement_data)
            self.assertEqual(sensor_summary.stationary, False)


if __name__ == "__main__":
    unittest.main()
