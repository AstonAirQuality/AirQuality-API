import datetime as dt
import json
import time
import unittest
import warnings
import zipfile
from os import environ as env
from unittest import TestCase
from unittest.mock import Mock, patch

from core.models import Logs as ModelLog
from core.models import Sensors as ModelSensor
from core.models import SensorSummaries as ModelSensorSummary
from core.models import SensorTypes as ModelSensorType
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app
from sensor_api_wrappers.concrete.factories.plume_factory import PlumeFactory
from sensor_api_wrappers.concrete.products.airGradient_sensor import AirGradientSensor
from sensor_api_wrappers.concrete.products.plume_sensor import PlumeSensor
from sensor_api_wrappers.concrete.products.purpleAir_sensor import PurpleAirSensor
from sensor_api_wrappers.concrete.products.sensorCommunity_sensor import SensorCommunitySensor
from sensor_api_wrappers.concrete.products.zephyr_sensor import ZephyrSensor
from sensor_api_wrappers.SensorFactoryWrapper import SensorFactoryWrapper
from testing.application_config import authenticate_client, database_config, setUpSensor, setUpSensorType


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
        cls.stationary_box = "POLYGON((-1.889767 52.45279,-1.889767 52.45281,-1.889747 52.45281,-1.889747 52.45279,-1.889767 52.45279))"

        # add a plume sensor type to the database
        cls.plume_sensor_type_id = setUpSensorType(
            db=cls.db,
            name="Plume",
            description="test_plume",
            properties={
                "NO2": "ppb",
                "VOC": "ppb",
                "pm10": "ppb",
                "pm2.5": "ppb",
                "pm1": "ppb",
            },
        )
        # add a plume sensor to the database
        cls.plume_sensor_id = setUpSensor(
            db=cls.db, lookup_id="18749", serial_number="02:00:00:00:48:45", type_id=cls.plume_sensor_type_id, active=True, user_id=None, stationary_box=cls.stationary_box
        )

        # add a zephyr sensor type to the database
        cls.zephyr_sensor_type_id = setUpSensorType(
            db=cls.db,
            name="Zephyr",
            description="test_zephyr",
            properties={
                "NO": "µg/m³",
                "NO2": "µg/m³",
                "O3": "µg/m³",
                "ambHumidity": "N/A",
                "ambPressure": "N/A",
                "ambTempC": "C",
                "humidity": "N/A",
                "pm10": "µg/m³",
                "pm2.5": "µg/m³",
                "pm1": "µg/m³",
                "tempC": "C",
            },
        )
        # add a zephyr sensor to the database
        cls.zephyr_sensor_id = setUpSensor(db=cls.db, lookup_id="814", serial_number="814:Zephyr", type_id=cls.zephyr_sensor_type_id, active=True, user_id=None, stationary_box=cls.stationary_box)

        # add a sensorCommunity sensor type to the database
        cls.sensorCommunity_sensor_type_id = setUpSensorType(
            db=cls.db,
            name="SensorCommunity",
            description="test_sensorCommunity",
            properties={
                "NO2": "µg/m³",
                "VOC": "µg/m³",
                "pm10": "µg/m³",
                "pm2.5": "µg/m³",
                "pm1": "µg/m³",
            },
        )
        # add a sensorCommunity sensor to the database
        cls.sensorCommunity_sensor_id = setUpSensor(
            db=cls.db,
            lookup_id="60641,SDS011,60642,BME280",
            serial_number="60641,SDS011,60642,BME280:SensorCommunity",
            type_id=cls.sensorCommunity_sensor_type_id,
            active=True,
            user_id=None,
            stationary_box=cls.stationary_box,
        )

        # plume sensor summary to be added to the database
        zip_contents = PlumeFactory.extract_zip_content(zipfile.ZipFile("./testing/test_data/plume_sensorData.zip", "r"), include_measurements=True)
        (id_, buffer) = next(zip_contents)
        sensor = PlumeSensor.from_zip(sensor_id="18749", csv_file=buffer)
        cls.plume_summary = list(sensor.create_sensor_summaries(None))[0]

        # zephyr sensor summary to be added to the database
        file = open("testing/test_data/zephyr_814_sensor_data.json", "r")
        json_ = json.load(file)
        file.close()
        sensor = ZephyrSensor.from_json("814", json_["data"]["Unaveraged"]["slotB"])
        cls.zephyr_summary = list(sensor.create_sensor_summaries(None))[0]

        # sensorCommunity sensor summary to be added to the database
        csv_files = {60641: {0: None}, 60642: {0: None}}
        sensor_id = "60641,SDS011,60642,BME280"

        file = open("testing/test_data/2023-04-01_sds011_sensor_60641.csv", "r")
        csv_files[60641][0] = file.read().encode()
        file.close()

        file = open("testing/test_data/2023-04-01_bme280_sensor_60642.csv", "r")
        csv_files[60642][0] = file.read().encode()
        file.close()
        sensor = SensorCommunitySensor.from_csv(sensor_id, csv_files)
        cls.sensorCommunity_summary = list(sensor.create_sensor_summaries(None))[0]

        # purple air sensor type to be added to the database
        cls.purpleAir_sensor_type_id = setUpSensorType(
            db=cls.db,
            name="PurpleAir",
            description="test_purpleAir",
            properties={
                "pm1.0_atm_a": "µg/m³",
                "pm1.0_atm_b": "µg/m³",
                "pm2.5_atm_a": "µg/m³",
                "pm2.5_atm_b": "µg/m³",
                "pm10.0_atm_a": "µg/m³",
                "pm10.0_atm_b": "µg/m³",
                "temperature": "C",
                "humidity": "%",
                "pressure": "hPa",
                "voc": "ppb",
                "scattering_coefficient": "Mm-1",
                "deciviews": "n/a",
                "visual_range": "n/a",
            },
        )
        # purple air sensor to be added to the database
        cls.purpleAir_sensor_id = setUpSensor(
            db=cls.db, lookup_id="274866,outdoor", serial_number="zen_2020:PurpleAir", type_id=cls.purpleAir_sensor_type_id, active=True, user_id=None, stationary_box=cls.stationary_box
        )
        # purple air sensor summary to be added to the database
        file = open("testing/test_data/purpleair_sensor_274866.csv", "r")
        data = file.read()
        file.close()
        sensor = PurpleAirSensor.from_csv("274866,outdoor", data)
        cls.purpleAir_summary = list(sensor.create_sensor_summaries(None))[0]

        # airGradient sensor type to be added to the database
        cls.airGradient_sensor_type_id = setUpSensorType(
            db=cls.db,
            name="AirGradient",
            description="test_airGradient",
            properties={
                "pm01": "µg/m³",
                "pm02": "µg/m³",
                "pm10": "µg/m³",
                "pm01_corrected": "µg/m³",
                "pm02_corrected": "µg/m³",
                "pm10_corrected": "µg/m³",
                "pm003Count": "µg/m³",
                "atmp": "C",
                "rhum": "%",
                "rco2": "ppm",
                "atmp_corrected": "C",
                "rhum_corrected": "%",
                "rco2_corrected": "ppm",
                "tvoc": "ppb",
                "tvocIndex": "n/a",
                "noxIndex": "n/a",
            },
        )
        # airGradient sensor to be added to the database
        cls.airGradient_sensor_id = setUpSensor(
            db=cls.db, lookup_id="163763", serial_number="2020:AirGradient", type_id=cls.airGradient_sensor_type_id, active=True, user_id=None, stationary_box=cls.stationary_box
        )
        # airGradient sensor summary to be added to the database
        file = open("testing/test_data/airgradient_163763_data.json", "r")
        json_ = json.load(file)
        file.close()

        sensor = AirGradientSensor.from_json("163763", json_)
        cls.airGradient_summary = list(sensor.create_sensor_summaries(None))[0]

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
            response = self.client.post("/api-task/schedule/ingest-bysensorid/02-04-2023/03-04-2023", params={"sensor_ids": [self.zephyr_sensor_id]})
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

    def test_3_sensorCommunity_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        # wait 3 second to ensure that the log date is different
        time.sleep(2)
        with patch.object(SensorFactoryWrapper, "fetch_sensorCommunity_data", return_value=[self.sensorCommunity_summary]) as mock_fetch_sensorCommunity_data:
            response = self.client.post("/api-task/schedule/ingest-bysensorid/31-03-2023/01-04-2023", params={"sensor_ids": [self.sensorCommunity_sensor_id]})
            mock_fetch_sensorCommunity_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.sensorCommunity_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()

    def test_4_purpleAir_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        # wait 2 second to ensure that the log date is different
        time.sleep(2)

        with patch.object(SensorFactoryWrapper, "fetch_purpleAir_data", return_value=[self.purpleAir_summary]) as mock_fetch_purpleAir_data:
            response = self.client.post("/api-task/schedule/ingest-bysensorid/01-04-2023/02-04-2023", params={"sensor_ids": [self.purpleAir_sensor_id]})
            mock_fetch_purpleAir_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.purpleAir_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()

    def test_6_airGradient_upsert_sensor_summary_by_id_list(self):
        """Test the upsert sensor summary by id list route of the API"""
        # wait 2 second to ensure that the log date is different
        time.sleep(2)

        with patch.object(SensorFactoryWrapper, "fetch_airGradient_data", return_value=[self.airGradient_summary]) as mock_fetch_airGradient_data:
            response = self.client.post("/api-task/schedule/ingest-bysensorid/01-04-2023/02-04-2023", params={"sensor_ids": [self.airGradient_sensor_id]})
            mock_fetch_airGradient_data.assert_called_once()
            self.assertEqual(response.status_code, 200)
            self.assertNotEqual(response, "No active sensors found")

        # test that the sensor summary was added to the database
        try:
            res = self.db.query(ModelSensorSummary).filter(ModelSensorSummary.sensor_id == self.airGradient_sensor_id).first()
            self.assertIsNotNone(res)
        except Exception as e:
            self.db.rollback()

        # test that log was added to the database
        self.log_insert_shared_test()

    def test_6_upsert_sensor_summary_by_type_id_active_sensors(self):
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
