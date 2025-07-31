from unittest import TestCase
from api import create_app
from api.extensions import db
from datetime import datetime, UTC

class AuthTestCase(TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.testing = True

        with self.app.app_context():
            db.create_all()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()            

    def test_register_successful(self):
        response = self.client.post("/auth/register", json={
            "role": "Faculty",
            "faculty_id": "12345678",
            "first_name": "Good",
            "middle_name": "User",
            "last_name": "Name",
            "email": "validemail123@gmail.com",
            "password": "goodpassword123",
            "phone_number": "1234567890",
            "birth_date": "2000-01-01",
            "created_by": "system",
            "updated_by": "system"
        })

        self.assertEqual(response.status_code, 201, "User should be registered successfully")
    
    def test_register_incomplete_fail(self):
        response = self.client.post("/auth/register", json={
            "faculty_id": "12345678",
            "password": "incompletepassword123"
        })

        self.assertEqual(response.status_code, 400, "Registration should fail when required fields are missing")

    def test_register_email_already_exists_fail(self):
        self.client.post("/auth/register", json={
            "role": "Faculty",
            "faculty_id": "11111111",
            "first_name": "Unique",
            "middle_name": "User",
            "last_name": "Test",
            "email": "duplicateemail@gmail.com",
            "password": "securepass",
            "phone_number": "1234567890",
            "birth_date": "1999-05-05",
            "created_by": "system",
            "updated_by": "system"
        })

        response = self.client.post("/auth/register", json={
            "role": "Faculty",
            "faculty_id": "22222222",
            "first_name": "Another",
            "middle_name": "User",
            "last_name": "Test",
            "email": "duplicateemail@gmail.com",
            "password": "securepass",
            "phone_number": "1234567890",
            "birth_date": "2001-07-07",
            "created_by": "system",
            "updated_by": "system"
        })

        self.assertEqual(response.status_code, 409, "Registration should fail when email already exists")
    
    def test_login_successful(self):
        self.client.post("/auth/register", json={
            "role": "Faculty",
            "faculty_id": "33333333",
            "first_name": "Good",
            "middle_name": "Login",
            "last_name": "User",
            "email": "validemail123@gmail.com",
            "password": "goodpassword123",
            "phone_number": "1234567890",
            "birth_date": "1998-03-03",
            "created_by": "system",
            "updated_by": "system"
        })

        response = self.client.post("/auth/login", json={
            "email": "validemail123@gmail.com",
            "password": "goodpassword123"
        })

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.get_json(), "Login should return a valid JWT token")
    
    def test_login_doesnt_exist_fail(self):
        response = self.client.post("/auth/login", json={
            "email": "nonexistentemail@gmail.com",
            "password": "randompassword"
        })

        self.assertEqual(response.status_code, 401, "Login should fail when email doesn't exist")
    
    def test_login_bad_password_fail(self):
        self.client.post("/auth/register", json={
            "role": "Faculty",
            "faculty_id": "44444444",
            "first_name": "Bad",
            "middle_name": "Password",
            "last_name": "User",
            "email": "validemail123@gmail.com",
            "password": "correctpassword",
            "phone_number": "1234567890",
            "birth_date": "2002-09-09",
            "created_by": "system",
            "updated_by": "system"
        })

        response = self.client.post("/auth/login", json={
            "email": "validemail123@gmail.com",
            "password": "wrongpassword"
        })

        self.assertEqual(response.status_code, 401, "Login should fail when the password is incorrect")