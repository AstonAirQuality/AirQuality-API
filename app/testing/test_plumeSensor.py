import json
import unittest  # The test framework
import warnings
import zipfile
from unittest import TestCase

from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor


class Test_plumeSensor(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
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

    def test_plume_from_mergedcsv(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)

        # asserts
        self.assertIsNotNone(sensor)
        expectedColumns = ["NO2", "VOC", "timestamp", "latitude", "longitude", "particulatePM1", "particulatePM2.5", "particulatePM10"]
        for col in expectedColumns:
            self.assertTrue(col in sensor.df.columns)
            break

        # test for null locations
        self.assertEqual(len(sensor.df), len(sensor.df[sensor.df.notna()]))

        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))

    def test_plume_from_csv(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_csv(sensor_id=id_, csv_file=buffer)

        # asserts
        self.assertIsNotNone(sensor)
        self.assertTrue("timestamp" not in sensor.df.columns)
        expectedColumns = ["latitude", "longitude"]
        for col in expectedColumns:
            self.assertTrue(col in sensor.df.columns)
            break

        # test for null locations
        self.assertEqual(len(sensor.df), len(sensor.df[sensor.df["longitude"].notna()]))

        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))

    def test_add_measurements_to_plume_from_csv(self):
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=False)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_csv(sensor_id=id_, csv_file=buffer)

        # asserts
        self.assertIsNotNone(sensor)

        file = open("testing/test_data/plume_measurements.json", "r")
        json_ = json.load(file)
        file.close()

        sensor.add_measurements_json(json_["measures"])

        expectedColumns = ["NO2", "VOC", "timestamp", "latitude", "longitude", "particulatePM1", "particulatePM2.5", "particulatePM10"]
        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))
        self.assertTrue(isinstance(sensor, PlumeSensor))
        self.assertEqual(sensor.id, "18749")
        for col in expectedColumns:
            self.assertTrue(col in sensor.df.columns)

    def test_plume_from_json(self):
        file = open("testing/test_data/plume_measurements.json", "r")
        json_ = json.load(file)
        file.close()

        sensor = PlumeSensor.from_json("18749", json_["measures"])

        # asserts
        self.assertIsNotNone(sensor)
        expectedColumns = ["timestamp", "NO2", "VOC", "particulatePM1", "particulatePM10", "particulatePM2.5"]
        for col in expectedColumns:
            self.assertTrue(col in sensor.df.columns)
            break

        # NOTE: Given that the presence of null data is unpredictable, we can skip this test
        # test for null data (normally there is significant amount of null data)
        # self.assertEqual(len(sensor.df), len(sensor.df.isna().sum()))

        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))


if __name__ == "__main__":
    unittest.main()
