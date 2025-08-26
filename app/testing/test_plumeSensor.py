import json
import unittest  # The test framework
import warnings
import zipfile
from unittest import TestCase

from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor


class Test_plumeSensor(TestCase):
    """
    The following tests are for the ScraperWraper. Tests send requests to ensure that the API's we are dependent on are working as expected.
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.expected_columns = [
            SensorMeasurementsColumns.NO2.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.TIMESTAMP.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
        ]

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

        for col in self.expected_columns:
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
        self.assertTrue(SensorMeasurementsColumns.TIMESTAMP.value in sensor.df.columns)
        for col in ["latitude", "longitude"]:
            self.assertTrue(col in sensor.df.columns)
            break

        # test for null locations
        self.assertEqual(len(sensor.df), len(sensor.df[sensor.df[SensorMeasurementsColumns.LONGITUDE.value].notna()]))

        # don't test for duplicate rows because we round the datetime to the nearest minute (this is to match the datetime of the measurement data)

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

        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))
        self.assertTrue(isinstance(sensor, PlumeSensor))
        self.assertEqual(sensor.id, "19651")
        for col in self.expected_columns:
            self.assertTrue(col in sensor.df.columns)

    def test_plume_from_json(self):
        file = open("testing/test_data/plume_measurements.json", "r")
        json_ = json.load(file)
        file.close()

        sensor = PlumeSensor.from_json("19651", json_["measures"])

        # asserts
        self.assertIsNotNone(sensor)
        for col in self.expected_columns:
            self.assertTrue(col in sensor.df.columns)
            break

        # NOTE: Given that the presence of null data is unpredictable, we can skip this test
        # test for null data (normally there is significant amount of null data)
        # self.assertEqual(len(sensor.df), len(sensor.df.isna().sum()))

        # test for duplicate rows (where index is the same)
        self.assertEqual(len(sensor.df), len(sensor.df.loc[~sensor.df.index.duplicated()]))


if __name__ == "__main__":
    unittest.main()
