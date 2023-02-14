import unittest
from unittest import TestCase

from core.models import Users as ModelUser
from fastapi.testclient import TestClient
from main import app
from testing.application_config import authenticate_client, database_config


class Test_Api_4_Users(TestCase):
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
            cls.user = ModelUser(uid="test", username="test", email="test@test.com", role="user")
            cls.db.add(cls.user)
            cls.db.commit()
        except Exception as e:
            cls.db.rollback()

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

    def test_2_get_users(self):
        """Test the get users route of the API"""
        response = self.client.get("/user")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_3_get_user_from_column_uid(self):
        """Test the get user from column route of the API"""
        response = self.client.get("/user/read-from/uid", params={"searchvalue": self.user.uid})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["uid"], self.user.uid)

    def test_4_get_user_from_column_email(self):
        """Test the get user from column route of the API"""
        response = self.client.get("/user/read-from/email", params={"searchvalue": self.user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], self.user.email)

    def test_5_get_user_from_column_role(self):
        """Test the get user from column route of the API"""
        response = self.client.get("/user/read-from/role", params={"searchvalue": self.user.role})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["role"], self.user.role)

    def test_6_put_user(self):
        """Test the put user route of the API"""
        updated_user = {"uid": "test", "username": "test_updated", "email": "test@test.com", "role": "user"}
        response = self.client.put(f"/user/{self.user.uid}", json=updated_user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "test_updated")

        # wait for the database to update
        self.db.commit()
        # then check that the user was updated in the database
        db_user = self.db.query(ModelUser).filter(ModelUser.uid == "test").first()
        self.assertEqual(db_user.username, "test_updated")

    def test_7_patch_user_role(self):
        """Test the patch user role route of the API"""
        response = self.client.patch(f"/user/{self.user.uid}/admin")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["role"], "admin")

        # wait for the database to update
        self.db.commit()
        # check that the user was updated in the database
        db_user = self.db.query(ModelUser).filter(ModelUser.uid == "test").first()
        self.assertEqual(db_user.role, "admin")

    def test_8_delete_user(self):
        """Test the delete user route of the API"""
        response = self.client.delete(f"/user/{self.user.uid}")
        self.assertEqual(response.status_code, 200)

        # check that the user was deleted from the database
        db_user = self.db.query(ModelUser).filter(ModelUser.uid == "test").first()
        self.assertIsNone(db_user)


if __name__ == "__main__":
    unittest.main()
