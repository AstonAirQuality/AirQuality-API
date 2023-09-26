import unittest
import warnings
import zipfile
from unittest import TestCase

from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from fastapi.testclient import TestClient
from main import app
from routers.sensorSummaries import upsert_sensorSummary
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor
from testing.application_config import (
    authenticate_client,
    database_config,
    setUpSensor,
    setUpSensorType,
)


class Test_Api_6_SensorSummary(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.client = TestClient(app)
        cls.client = authenticate_client(cls.client, role="admin")
        cls.db = database_config()

        # get/add a sensor type to the database
        cls.sensor_type_id = setUpSensorType(cls.db, "Plume", "test_plume", {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})

        # get/add a sensor to the database
        cls.sensor_id = setUpSensor(cls.db, "test_sensor", "test_sensor", cls.sensor_type_id, True, None, None)

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
                if summary.measurement_count > 0:
                    upsert_sensorSummary(summary)
        except Exception as e:
            cls.db.rollback()

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        # try:
        #     cls.db.delete(cls.db.query(ModelSensorType).filter(ModelSensorType.id == cls.sensor_type_id).first())
        #     cls.db.delete(cls.db.query(ModelSensor).filter(ModelSensor.id == cls.sensor_id).first())
        #     cls.db.delete(cls.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == cls.sensor_id).all())
        #     cls.db.commit()
        # except Exception as e:
        #     cls.db.rollback()
        cls.db.close()

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
        response = self.client.get("/sensor-summary", params={"start": "27-09-2022", "end": "28-09-2022", "columns": ["sensor_id", "measurement_count", "geom", "timestamp"]})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_3_get_sensorSummary_with_measurement_data(self):
        """Test that the sensor summary is returned"""

        response = self.client.get("/sensor-summary", params={"start": "27-09-2022", "end": "28-09-2022", "columns": ["sensor_id", "measurement_data", "geom", "timestamp"]})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_4_get_sensorSummary_with_deserialized_data(self):
        """Test that the sensor summary is returned"""

        response = self.client.get("/sensor-summary", params={"start": "27-09-2022", "end": "28-09-2022", "columns": ["sensor_id", "measurement_data", "geom", "timestamp"], "deserialized": True})
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_5_get_sensorSummary_spatial_intersect(self):
        response = self.client.get(
            "/sensor-summary",
            params={
                "start": "27-09-2022",
                "end": "28-09-2022",
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "intersects",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_6_get_sensorSummary_spatial_within(self):
        response = self.client.get(
            "/sensor-summary",
            params={
                "start": "27-09-2022",
                "end": "28-09-2022",
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "within",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_7_get_sensorSummary_spatial_contains(self):
        response = self.client.get(
            "/sensor-summary",
            params={
                "start": "27-09-2022",
                "end": "28-09-2022",
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "contains",
                "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

    def test_8_get_sensorSummary_invalid_spatial_contains(self):
        response = self.client.get(
            "/sensor-summary",
            params={
                "start": "27-09-2022",
                "end": "28-09-2022",
                "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
                "spatial_query_type": "contains",
                "geom": "POINT(-1.83631 52.425392)",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) == 0)

    # def test_9_get_sensorSummary_spatial_overlaps(self):
    #     response = self.client.get(
    #         "/sensor-summary",
    #         params={
    #             "start": "27-09-2022",
    #             "end": "28-09-2022",
    #             "columns": ["sensor_id", "measurement_count", "geom", "timestamp"],
    #             "spatial_query_type": "overlaps",
    #             "geom": "POLYGON ((-1.83631 52.425392, -1.83631 52.425603, -1.836288 52.425603, -1.836288 52.425392, -1.83631 52.425392))",
    #         },
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIsNotNone(response.json())
    #     self.assertTrue(len(response.json()) > 0)

    # TODO - assert geojson is valid
    def test_10_get_sensorSummary_as_geojson(self):
        """Test that the sensor summary is returned as a valid geojson"""
        response = self.client.get(
            "/sensor-summary/as-geojson",
            params={"start": "27-09-2022", "end": "28-09-2022", "columns": ["sensor_id", "measurement_count", "geom", "timestamp"], "averaging_methods": ["mean", "count"], "averaging_frequency": "H"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.json())
        self.assertTrue(len(response.json()) > 0)

        # assert geojson content is valid
        geojson = response.json()[0]["geojson"]

        self.assertTrue(geojson["type"] == "FeatureCollection")
        self.assertTrue(isinstance(geojson["features"], list))
        for feature in geojson["features"]:
            self.assertTrue("geometry" in feature)
            self.assertTrue("properties" in feature)
            self.assertTrue("type" in feature)


if __name__ == "__main__":
    unittest.main()
