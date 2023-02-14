import datetime as dt
import unittest
from unittest import TestCase

from core.models import Logs as ModelLogs
from fastapi.testclient import TestClient
from main import app
from testing.application_config import authenticate_client, database_config


class Test_Api_5_Logs(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        cls.client = TestClient(app)
        cls.client = authenticate_client(cls.client, role="admin")
        cls.db = database_config()

        try:
            cls.dateTime_key = dt.datetime.now() - dt.timedelta(days=1)
            cls.log = ModelLogs(date=cls.dateTime_key, data={"test_key": "test_value"})
            cls.db.add(cls.log)
            cls.db.commit()
        except Exception as e:
            cls.db.rollback()
            raise e

    @classmethod
    def tearDownClass(cls):
        """Tear down the test environment once after all tests"""
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

    def test_2_get_logs(self):
        """Test the get logs route of the API"""
        response = self.client.get("/data-ingestion-logs")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_3_get_logs_by_date(self):
        """Test the get logs by date route of the API"""

        today = dt.datetime.now() - dt.timedelta(days=1)
        todayString = today.strftime("%Y-%m-%d")
        response = self.client.get(f"/data-ingestion-logs/findByDate/{todayString}")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_4_delete_logs(self):
        """Test the delete logs route of the API"""
        response = self.client.delete(f"/data-ingestion-logs/{self.dateTime_key}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Log deleted successfully"})

        # check that the logs were deleted from the database
        db_logs = self.db.query(ModelLogs).filter(ModelLogs.date == self.dateTime_key).all()
        self.assertEqual(len(db_logs), 0)


if __name__ == "__main__":
    unittest.main()
