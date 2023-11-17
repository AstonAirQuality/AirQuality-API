import datetime as dt
import json
import unittest  # The test framework
import warnings
import zipfile
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, patch

from core.schema import SensorSummary as SchemaSensorSummary
from parameterized import parameterized
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor
from sensor_api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from sensor_api_wrappers.data_transfer_object.sensor_writeable import SensorWritable

# parameterized tests
bad_stationaryBox = "POLYGON ((-1.836323 52.425392, -1.836323 52.425726, -1.836288 52.425726, -1.836288 52.425392, -1.836323 52.425392))"
stationaryBox = "POLYGON ((-1.8968080000000005 52.452656000000005, -1.8968080000000005 52.455859, -1.889424 52.455859, -1.889424 52.452656000000005, -1.8968080000000005 52.452656000000005))"


class Test_sensorWriteable(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.bad_stationaryBox = bad_stationaryBox
        cls.stationaryBox = stationaryBox
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

    def larger_than_two(self, value):
        return value > 2

    @parameterized.expand(
        [
            ("bad_stationaryBox", bad_stationaryBox),
            ("good_stationaryBox", stationaryBox),
        ]
    )
    def test_sensorSummary_from_plume_with_stationaryBox_with_gps(self, test_type: str, value: str):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)
        # subset df to only get data between 23-24 September string. There is location data in this time period
        sensor.df = sensor.df.loc["2023-09-23 00:00:00":"2023-09-24 00:00:00"]
        sensor = SensorWritable(sensor.id, sensor.df)  # type cast to SensorWritable for readability

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=value)
        self.assertIsNotNone(sensor_summaries)

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)
            if test_type == "bad_stationaryBox":
                self.assertFalse(sensor_summary.geom == self.stationaryBox)
                self.assertFalse(sensor_summary.stationary)
            else:
                self.assertTrue(sensor_summary.geom == self.stationaryBox)
                self.assertTrue(sensor_summary.stationary)
            self.assertTrue(sensor_summary.measurement_count > 0)
            self.assertIsNotNone(sensor_summary.measurement_data)

    def test_sensorSummary_from_plume_no_stationaryBox_with_gps(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)

        # subset df to only get data between 23-24 September string. There is location data in this time period
        sensor.df = sensor.df.loc["2023-09-23 00:00:00":"2023-09-24 00:00:00"]
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
                expectedGeom = "POLYGON((-1.912562 52.446574,-1.912562 52.455859,-1.8892 52.455859,-1.8892 52.446574,-1.912562 52.446574))"
                self.assertEqual(sensor_summary.geom, expectedGeom)
                self.assertTrue(sensor_summary.measurement_count > 0)
                self.assertIsNotNone(sensor_summary.measurement_data)
                self.assertEqual(sensor_summary.stationary, False)

    def test_sensorSummary_from_plume_with_stationaryBox_no_gps(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)

        # subset df to only get data between 23-24 September string. There is location data in this time period
        sensor.df = sensor.df.loc["2023-09-23 00:00:00":"2023-09-24 00:00:00"]
        sensor.df.drop(columns=["latitude", "longitude"], inplace=True)
        sensor = SensorWritable(sensor.id, sensor.df)

        self.assertTrue(isinstance(sensor, SensorWritable))
        self.assertTrue(sensor.df.columns.__contains__("latitude") == False)

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=self.stationaryBox)
        self.assertIsNotNone(sensor_summaries)

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)
            self.assertTrue(sensor_summary.geom == self.stationaryBox)
            self.assertTrue(sensor_summary.measurement_count > 0)
            self.assertIsNotNone(sensor_summary.measurement_data)
            self.assertEqual(sensor_summary.stationary, True)

    def test_sensorSummary_from_zephyr_with_stationary_box(self):
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])

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

    def test_sensorSummary_from_zephyr_no_stationary_box(self):
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=None)
        self.assertIsNotNone(sensor_summaries)

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)
            self.assertTrue(sensor_summary.geom == None)
            self.assertTrue(sensor_summary.measurement_count == 0)

    # TODO add sensorCommunity tests
    def test_sensorSummary_from_sensorCommunity_with_stationary_box(self):
        csv_files = {60641: {0: None}, 60642: {0: None}}
        sensor_id = "60641,SDS011,60642,BME280"

        file = open("testing/test_data/2023-04-01_sds011_sensor_60641.csv", "r")
        csv_files[60641][0] = file.read().encode()
        file.close()

        file = open("testing/test_data/2023-04-01_bme280_sensor_60642.csv", "r")
        csv_files[60642][0] = file.read().encode()
        file.close()

        sensor = SensorCommunitySensor.from_csv(sensor_id, csv_files)

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=self.stationaryBox)
        self.assertIsNotNone(sensor_summaries)

        expectedGeom = "POLYGON((-1.9301 52.445899999999995,-1.9301 52.4461,-1.9299 52.4461,-1.9299 52.445899999999995,-1.9301 52.445899999999995))"

        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)
            self.assertFalse(sensor_summary.geom == self.stationaryBox)
            self.assertTrue(sensor_summary.geom == expectedGeom)
            self.assertTrue(sensor_summary.measurement_count > 0)
            self.assertIsNotNone(sensor_summary.measurement_data)
            # because the sensor is not in the original stationary box, it should be marked as not stationary
            self.assertFalse(sensor_summary.stationary)

    def test_sensorSummary_from_sensorCommunity_no_stationary_box(self):
        csv_files = {60641: {0: None}, 60642: {0: None}}
        sensor_id = "60641,SDS011,60642,BME280"

        file = open("testing/test_data/2023-04-01_sds011_sensor_60641.csv", "r")
        csv_files[60641][0] = file.read().encode()
        file.close()

        file = open("testing/test_data/2023-04-01_bme280_sensor_60642.csv", "r")
        csv_files[60642][0] = file.read().encode()
        file.close()

        sensor = SensorCommunitySensor.from_csv(sensor_id, csv_files)

        self.assertTrue(isinstance(sensor, SensorWritable))

        sensor_summaries = sensor.create_sensor_summaries(stationary_box=None)
        self.assertIsNotNone(sensor_summaries)

        expectedGeom = "POLYGON((-1.9301 52.445899999999995,-1.9301 52.4461,-1.9299 52.4461,-1.9299 52.445899999999995,-1.9301 52.445899999999995))"
        for sensor_summary in sensor_summaries:
            self.assertTrue(isinstance(sensor_summary, SchemaSensorSummary))
            self.assertEqual(str(sensor_summary.sensor_id), sensor.id)
            self.assertTrue(sensor_summary.geom == expectedGeom)
            # since a stationary box was not provided, the sensor summary should not be stationary
            self.assertFalse(sensor_summary.stationary)
            self.assertTrue(sensor_summary.measurement_count > 0)


if __name__ == "__main__":
    unittest.main()
