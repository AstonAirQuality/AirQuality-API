import datetime as dt
import unittest
import zipfile
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor
from api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from core.models import Logs as ModelLog
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app
from testing.application_config import authenticate_client, database_config


class Test_Api_7_BackgroundTasks(TestCase):
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
                sensorType = ModelSensorType(name="Plume", description="test_plume", properties={"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
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
        cls.summaries = sensor.create_sensor_summaries(None)

        # get the first summary
        for summary in cls.summaries:
            cls.summary = summary
            break

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        try:
            cls.db.delete(cls.db.query(ModelSensorType).filter(ModelSensorType.id == cls.sensor_type_id).first())
            cls.db.delete(cls.db.query(ModelSensor).filter(ModelSensor.id == cls.sensor_id).first())
            cls.db.commit()
        except Exception as e:
            cls.db.rollback()

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    def test_1_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        with patch.object(SensorFactoryWrapper, "fetch_plume_data", return_value=[self.summary]) as mock_fetch_plume_data:
            response = self.client.get("/api-task/schedule/ingest-bysensorid/27-09-2022/28-09-2022", params={"sensor_ids": [self.sensor_type_id]})
            mock_fetch_plume_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        log_date = dt.datetime.today()
        end_date = (log_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
        log_date = log_date.strftime("%Y-%m-%d")

        try:
            result = self.db.query(ModelLog).filter(ModelLog.date >= log_date, ModelLog.date < end_date).first()
            self.assertIsNotNone(result)
        except Exception:
            self.db.rollback()

    def test_2_upsert_sensor_summary_by_type_id_active_sensors(self):
        """Test the upsert sensor summary by type id active sensors route of the API"""
        with patch.object(SensorFactoryWrapper, "fetch_plume_data", return_value=[self.summary]) as mock_fetch_plume_data:
            response = self.client.get("/api-task/cron/ingest-active-sensors", headers={"cron-job-token": env["CRON_JOB_TOKEN"]})
            mock_fetch_plume_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        log_date = dt.datetime.today()
        end_date = (log_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
        log_date = log_date.strftime("%Y-%m-%d")

        try:
            result = self.db.query(ModelLog).filter(ModelLog.date >= log_date, ModelLog.date < end_date).first()
            self.assertIsNotNone(result)
        except Exception:
            self.db.rollback()


if __name__ == "__main__":
    unittest.main()
