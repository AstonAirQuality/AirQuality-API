import unittest
import zipfile
from unittest import TestCase

from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from fastapi.testclient import TestClient
from main import app
from routers.helpers.sensorSummarySharedFunctions import upsert_sensorSummary
from testing.application_config import authenticate_client, database_config


class Test_Api_6_SensorSummary(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.client = TestClient(app)
        cls.client = authenticate_client(cls.client, role="admin")
        cls.db = database_config()

        # add a sensor type to the database
        try:
            result = cls.db.query(ModelSensorType).first()
            # if the sensor type does not exist then add it to the database and get the id
            if result is None:
                sensorType = ModelSensorType(name="test_plume", description="test_plume", properties={"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
                cls.db.add(sensorType)
                cls.db.commit()
                cls.sensor_type_id = sensorType.id
            else:
                cls.sensor_type_id = result.id

        except Exception as e:
            cls.db.rollback()

        # add a plume sensor to the database
        try:
            result = cls.db.query(ModelSensor).filter(ModelSensor.lookup_id == "18749").first()
            # if the sensor type does not exist then add it to the database and get the id
            if result is None:
                sensor = ModelSensor(lookup_id="18749", serial_number="02:00:00:00:48:45", type_id=cls.sensor_type_id, active=True, user_id=None, stationary_box=None)
                cls.db.add(sensor)
                cls.db.commit()
                cls.sensor_id = sensor.id
            else:
                cls.sensor_id = result.id
        except Exception as e:
            cls.db.rollback()

        # add a plume sensor summary to the database
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)

        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id=id_, csv_file=buffer)
        sensor = PlumeSensor(id_=id_, dataframe=sensor.df)
        summaries = sensor.create_sensor_summaries(None)

        try:
            # add a sensor summary to the database
            for summary in summaries:
                summary.sensor_id = cls.sensor_id
                upsert_sensorSummary(summary)
        except Exception as e:
            cls.db.rollback()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        try:
            cls.db.delete(cls.db.query(ModelSensorType).filter(ModelSensorType.id == cls.sensor_type_id).first())
            cls.db.delete(cls.db.query(ModelSensor).filter(ModelSensor.id == cls.sensor_id).first())
            cls.db.delete(cls.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == cls.sensor_id).all())
            cls.db.commit()
        except Exception as e:
            cls.db.rollback()

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    def test_1_db_connection(self):
        """Test that the database is connected"""
        self.assertIsNotNone(self.db)

    def test_2_get_sensorSummary(self):
        """Test that the sensor summary is returned"""
        response = self.client.get("/sensor-summary/27-09-2022/28-09-2022", params={"columns": ["sensor_id", "measurement_count", "geom", "timestamp"]})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_3_get_sensorSummary_with_measurement_data(self):
        """Test that the sensor summary is returned"""

        response = self.client.get("/sensor-summary/27-09-2022/28-09-2022", params={"columns": ["sensor_id", "measurement_data", "geom", "timestamp"]})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_3_get_sensorSummary_spatial_intersect(self):

        response = self.client.get(
            "/sensor-summary/27-09-2022/28-09-2022",
            params={
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "intersect",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_4_get_sensorSummary_spatial_within(self):
        response = self.client.get(
            "/sensor-summary/27-09-2022/28-09-2022",
            params={
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "within",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_5_get_sensorSummary_spatial_contains(self):
        response = self.client.get(
            "/sensor-summary/27-09-2022/28-09-2022",
            params={
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "contains",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    # def test_6_get_sensorSummary_spatial_overlaps(self):
    #     response = self.client.get(
    #         "/sensor-summary/27-09-2022/28-09-2022",
    #         params={
    #             "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
    #             "spatial_query_type": "overlaps",
    #             "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
    #         },
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIsNotNone(response.json())
    #     self.assertTrue(len(response.json()) > 0)

    # TODO - fix this test
    def test_7_get_sensorSummary_as_geojson(self):
        """Test that the sensor summary is returned as geojson"""
        # 27/09/2022 23:00

        response = self.client.get(
            "/sensor-summary/as-geojson/27-09-2022/28-09-2022",
            params={"columns": ["sensor_id", "measurement_count", "geom", "timestamp"], "averaging_method": ["mean", "count"], "averaging_frequency": "D"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)


if __name__ == "__main__":
    unittest.main()
