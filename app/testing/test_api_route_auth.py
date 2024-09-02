import unittest
import warnings
from unittest import TestCase

from core.models import Users as ModelUser
from fastapi.testclient import TestClient
from main import app
from testing.application_config import database_config


class Test_Api_3_Auth(TestCase):
    """
    The following tests are for the API endpoints
    """

    @classmethod
    def setUpClass(cls):
        """Setup the test environment once before all tests"""
        warnings.simplefilter("ignore", ResourceWarning)
        cls.client = TestClient(app)
        cls.client.headers.update({"Content-Type": "application/json"})
        cls.db = database_config()
        cls.user_credentials = {"email": "api_test@test.com", "password": "testpassword"}

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

    def test_2_sign_up(self):
        """Test the sign up route of the API (firebase and python web app)"""

        # sign up with firebase
        firebaseResponse = self.client.post("/auth/firebase-signup", params=self.user_credentials)
        self.assertEqual(firebaseResponse.status_code, 200)
        self.assertTrue("idToken" in firebaseResponse.json())
        id_token = firebaseResponse.json()["idToken"]
        # sign up with python web app
        response = self.client.post("/auth/signup", params={"username": "test"}, headers={"firebase-token": id_token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "test")
        self.assertEqual(response.json()["role"], "user")

        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

        # test that the user is in the database
        db_user = self.db.query(ModelUser).filter(ModelUser.email == self.user_credentials["email"]).first()
        self.assertIsNotNone(db_user)

    def test_3_login(self):
        """Test the sign in route of the API (firebase and python web app)"""

        # sign in with firebase
        firebaseResponse = self.client.post("/auth/firebase-login", params=self.user_credentials)
        self.assertEqual(firebaseResponse.status_code, 200)
        self.assertTrue("idToken" in firebaseResponse.json())
        id_token = firebaseResponse.json()["idToken"]

        # sign in with python web app
        response = self.client.post("/auth/login", headers={"firebase-token": id_token})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "test")
        self.assertEqual(response.json()["role"], "user")

        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

    def test_4_delete_user(self):
        """Test the delete user route of the API."""

        # sign in with firebase
        firebaseResponse = self.client.post("/auth/firebase-login", params=self.user_credentials)
        self.assertEqual(firebaseResponse.status_code, 200)
        id_token = firebaseResponse.json()["idToken"]

        # sign in with python web app
        response = self.client.post("/auth/login", headers={"firebase-token": id_token})
        self.assertEqual(response.status_code, 200)
        access_token = response.json()["access_token"]
        self.client.headers.update({"Authorization": f"Bearer {access_token}"})

        # delete user from firebase
        deleteResponse = self.client.delete("/auth/user-account", headers={"firebase-token": id_token})
        self.assertEqual(deleteResponse.status_code, 200)

        # check that user is deleted from db
        result = self.db.query(ModelUser).filter(ModelUser.email == self.user_credentials["email"]).first()
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
