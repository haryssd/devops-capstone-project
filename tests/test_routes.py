"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman 

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    def test_read_an_account(self):
        """It should read an account"""
        # Create an account first using the helper method
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get the account ID from the response
        account_data = response.get_json()
        account_id = account_data["id"]

        # Read the account
        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check that the returned data matches what we sent
        data = response.get_json()
        self.assertEqual(data["name"], account.name)
        self.assertEqual(data["email"], account.email)
        self.assertEqual(data["address"], account.address)
        self.assertEqual(data["phone_number"], account.phone_number)

    def test_account_not_found(self):
        """It should not read an account that is not found"""
        response = self.client.get(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_list_accounts(self):
        """It should list all accounts"""
        # Create 5 accounts using the helper method
        self._create_accounts(5)

        # List all accounts
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), 5)

    def test_update_account(self):
        """It should update an existing account"""
        # Create an account
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        account_data = response.get_json()
        account_id = account_data["id"]

        # Update the account
        new_account = AccountFactory()
        response = self.client.put(f"{BASE_URL}/{account_id}", json=new_account.serialize())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the update
        updated_account = response.get_json()
        self.assertEqual(updated_account["name"], new_account.name)
        self.assertEqual(updated_account["email"], new_account.email)

    def test_update_account_not_found(self):
        """It should not update an account that is not found"""
        account = AccountFactory()
        response = self.client.put(f"{BASE_URL}/0", json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should delete an account"""
        # Create an account
        account = AccountFactory()
        response = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        account_data = response.get_json()
        account_id = account_data["id"]

        # Delete the account
        response = self.client.delete(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(response.data), 0)

        # Verify it's deleted
        response = self.client.get(f"{BASE_URL}/{account_id}")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should not delete an account that is not found"""
        response = self.client.delete(f"{BASE_URL}/0")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)
