import json
import unittest  # The test framework
import warnings
from io import StringIO
from unittest import TestCase

import pandas as pd
from routers.services.enums import SensorMeasurementsColumns
from sensor_api_wrappers.concrete.products.airGradient_sensor import AirGradientSensor


class Test_airGradientSensor(TestCase):
    """Tests that the airGradient class can be instantiated and that the data is correctly parsed into a dataframe."""

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)

        cls.expeted_columns = [
            SensorMeasurementsColumns.DATE.value,
            SensorMeasurementsColumns.PM1_RAW.value,
            SensorMeasurementsColumns.PM2_5_RAW.value,
            SensorMeasurementsColumns.PM10_RAW.value,
            SensorMeasurementsColumns.PM0_3_COUNT.value,
            SensorMeasurementsColumns.CO2.value,
            SensorMeasurementsColumns.AMBIENT_TEMPERATURE.value,
            SensorMeasurementsColumns.AMBIENT_HUMIDITY.value,
            SensorMeasurementsColumns.VOC.value,
            SensorMeasurementsColumns.VOC_INDEX.value,
            SensorMeasurementsColumns.NOX_INDEX.value,
            SensorMeasurementsColumns.PM1.value,
            SensorMeasurementsColumns.PM2_5.value,
            SensorMeasurementsColumns.PM10.value,
            SensorMeasurementsColumns.LATITUDE.value,
            SensorMeasurementsColumns.LONGITUDE.value,
        ]
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

    def test_airGradientSensor_from_json(self):
        """Test the AirGradientSensor class from a JSON file."""
        file = open("testing/test_data/airgradient_163763_data.json", "r")
        data = json.load(file)
        expected_df = pd.DataFrame(data)
        file.close()

        sensor = AirGradientSensor.from_json("163763", data)

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, AirGradientSensor))
        self.assertEqual(sensor.id, "163763")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        self.assertEqual(sensor.df.shape[0], expected_df.shape[0], "The number of rows in the sensor DataFrame should match the test data.")
        self.assertEqual(sensor.df.shape[1], len(self.expeted_columns), "The number of columns in the sensor DataFrame should match the test data.")

    def test_airGradientSensor_from_csv(self):
        """Test the AirGradientSensor class from a CSV file."""
        # TODO need to fix the decoding of the csv file
        file = open("testing/test_data/airgradient_163763_data.csv", "r", encoding="utf-8")
        csv_data = file.read()
        file.close()

        sensor = AirGradientSensor.from_csv("163763", csv_data)

        self.assertIsNotNone(sensor)
        self.assertTrue(isinstance(sensor, AirGradientSensor))
        self.assertEqual(sensor.id, "163763")
        self.assertTrue(isinstance(sensor.df, pd.DataFrame))
        self.assertEqual(sensor.df.shape[0], 1404, "The number of rows in the sensor DataFrame should match the test data.")
        # latitude and longitude columns are not included in the sensor DataFrame
        self.assertEqual(sensor.df.shape[1], len(self.expeted_columns), "The number of columns in the sensor DataFrame should match the test data.")
