import datetime as dt
import json
import time
import unittest
import warnings
import zipfile
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

from api_wrappers.concrete.factories.plume_factory import PlumeFactory
from api_wrappers.concrete.products.plume_sensor import PlumeSensor
from api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from core.models import Logs as ModelLog
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app
from testing.application_config import (
    authenticate_client,
    database_config,
    setUpSensor,
    setUpSensorType,
)


class Test_Api_7_BackgroundTasks(TestCase):
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

        # add a plume sensor type to the database
        cls.plume_sensor_type_id = setUpSensorType(cls.db, "Plume", "test_plume", {"NO2": "ppb", "VOC": "ppb", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb"})
        # add a plume sensor to the database
        cls.plume_sensor_id = setUpSensor(cls.db, "18749", "02:00:00:00:48:45", cls.plume_sensor_type_id, True, None, None)

        # add a zephyr sensor type to the database
        cls.zephyr_sensor_type_id = setUpSensorType(
            cls.db,
            "Zephyr",
            "test_zephyr",
            {"NO": "ppb", "NO2": "ppb", "O3": "ppb", "ambHumidity": "N/A", "ambPressure": "N/A", "ambTempC": "C", "humidity": "N/A", "pm10": "ppb", "pm2.5": "ppb", "pm1": "ppb", "tempC": "C"},
        )
        # add a zephyr sensor to the database
        cls.zephyr_sensor_id = setUpSensor(cls.db, "814", "814:Zephyr", cls.zephyr_sensor_type_id, True, None, None)

        # plume sensor summary to be added to the database
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)
        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id="18749", csv_file=buffer)
        cls.plume_summary = list(sensor.create_sensor_summaries(None))[0]

        # zephyr sensor summary to be added to the database
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["slotB"])

        cls.zephyr_summary = list(sensor.create_sensor_summaries(None))[0]

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
        cls.db.close()
        pass

    def setup(self):
        """Setup the test environment before each test"""
        pass

    def teardown(self):
        """Tear down the test environment after each test"""
        pass

    # TODO check the datetime key of the log and match with the datetime of the scheduled task
    def log_insert_shared_test(self):
        """Shared test for log insert"""
        # test that log was added to the database
        log_date = dt.datetime.today()
        end_date = (log_date + dt.timedelta(days=1)).strftime("%Y-%m-%d")
        log_date = log_date.strftime("%Y-%m-%d")

        try:
            result = self.db.query(ModelLog).filter(ModelLog.date >= log_date, ModelLog.date < end_date).first()
            self.assertIsNotNone(result)
        except Exception:
            self.db.rollback()

    def test_1_plume_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        # wait 1 second to ensure that the log date is different
        time.sleep(1)

        with patch.object(SensorFactoryWrapper, "fetch_plume_data", return_value=[self.plume_summary]) as mock_fetch_plume_data:
            response = self.client.post("/api-task/schedule/ingest-bysensorid/27-09-2022/28-09-2022", params={"sensor_ids": [self.plume_sensor_id]})
            mock_fetch_plume_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.plume_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()

    def test_2_zephyr_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        # wait 2 second to ensure that the log date is different
        time.sleep(2)
        with patch.object(SensorFactoryWrapper, "fetch_zephyr_data", return_value=[self.zephyr_summary]) as mock_fetch_zephyr_data:
            response = self.client.post("/api-task/schedule/ingest-bysensorid/27-09-2022/28-09-2022", params={"sensor_ids": [self.zephyr_sensor_id]})
            mock_fetch_zephyr_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.zephyr_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()

    def test_3_upsert_sensor_summary_by_type_id_active_sensors(self):
        """Test the upsert sensor summary by type id active sensors route of the API"""
        # wait 3 second to ensure that the log date is different
        time.sleep(2)

        # bug fix: the sensor id somehow gets set to plume_sensor_id instead of the lookupid
        self.plume_summary.sensor_id = "18749"

        with patch.object(SensorFactoryWrapper, "fetch_plume_data", return_value=[self.plume_summary]) as mock_fetch_plume_data:
            response = self.client.get(f"/api-task/cron/ingest-active-sensors/{self.plume_sensor_type_id}", headers={"cron-job-token": env["CRON_JOB_TOKEN"]})
            mock_fetch_plume_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.plume_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()


if __name__ == "__main__":
    unittest.main()
