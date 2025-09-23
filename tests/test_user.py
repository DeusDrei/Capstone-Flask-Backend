from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import datetime, UTC

class UserTestCase(TestCase):
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
    
    def _register_and_login(self):
        # Register a test user
        register_response = self.client.post("/auth/register", json={
            "role": "Technical Admin",
            "staff_id": "TEST123",
            "first_name": "Test",
            "middle_name": "T.",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "testpassword",
            "phone_number": "1234567890",
            "birth_date": "1990-01-01",
            "created_by": "system",
            "updated_by": "system"
        })
        
        # Check if registration was successful
        if register_response.status_code != 201:
            raise ValueError(f"Registration failed: {register_response.data}")
        
        # Login and get token
        login_response = self.client.post("/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        
        # Parse the JSON response
        login_data = json.loads(login_response.data)
        
        # Check if login was successful and contains token
        if login_response.status_code != 200 or 'access_token' not in login_data:
            raise ValueError(f"Login failed: {login_data}")
            
        return f"Bearer {login_data['access_token']}"

    # Test cases with authentication
    def test_create_user_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/users/", 
                json={
                    "role": "Faculty",
                    "staff_id": "FAC001",
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "john.doe@example.com",
                    "password": "password123",
                    "phone_number": "0987654321",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_user_unauthorized(self):
        response = self.client.post("/users/", 
            json={
                "role": "Faculty",
                "staff_id": "FAC001",
                "first_name": "Jane",
                "last_name": "Doe",
                "email": "jane.doe@example.com",
                "password": "password123",
                "phone_number": "0987654321",
                "birth_date": "2000-01-01",
                "created_by": "system",
                "updated_by": "system"
            }
        )
        self.assertIn(response.status_code, [400, 401])
    
    def test_create_user_incomplete_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/users/", 
                json={
                    "staff_id": "FAC003",
                    "first_name": "Incomplete",
                    "last_name": "User"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_user_duplicate_email_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            self.client.post("/users/", 
                json={
                    "role": "Faculty",
                    "staff_id": "FAC001",
                    "first_name": "Original",
                    "last_name": "User",
                    "email": "duplicate@example.com",
                    "password": "password123",
                    "phone_number": "1234567890",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Try duplicate
            response = self.client.post("/users/", 
                json={
                    "role": "PIMEC",
                    "staff_id": "EVAL005",
                    "first_name": "Duplicate",
                    "last_name": "User",
                    "email": "duplicate@example.com",
                    "password": "password123",
                    "phone_number": "0987654321",
                    "birth_date": "2001-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_user_duplicate_staff_id_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            self.client.post("/users/", 
                json={
                    "role": "Faculty",
                    "staff_id": "DUPLICATE001",
                    "first_name": "First",
                    "last_name": "User",
                    "email": "first@example.com",
                    "password": "password123",
                    "phone_number": "1234567890",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.post("/users/", 
                json={
                    "role": "Faculty",
                    "staff_id": "DUPLICATE001",
                    "first_name": "Second",
                    "last_name": "User",
                    "email": "second@example.com",
                    "password": "password123",
                    "phone_number": "0987654321",
                    "birth_date": "2001-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_user_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create user first
            self.client.post("/users/", 
                json={
                    "role": "Faculty",
                    "staff_id": "UPDATE001",
                    "first_name": "Original",
                    "last_name": "Name",
                    "email": "update@example.com",
                    "password": "password123",
                    "phone_number": "1234567890",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Update the user
            response = self.client.put("/users/2", 
                json={
                    "role": "Faculty",
                    "staff_id": "UPDATE001",
                    "first_name": "Updated",
                    "last_name": "Name",
                    "email": "update@example.com",
                    "phone_number": "0987654321",
                    "birth_date": "2000-01-01",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_users(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.get("/users/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_user_by_id_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create user first
            self.client.post("/users/", 
                json={
                    "role": "student",
                    "staff_id": "GET001",
                    "first_name": "Get",
                    "last_name": "User",
                    "email": "get@example.com",
                    "password": "password123",
                    "phone_number": "1234567890",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.get("/users/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_user_by_id_not_found(self):
        auth_header = {"Authorization": self._register_and_login()}
        response = self.client.get("/users/999", headers=auth_header)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_user_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create user first
            self.client.post("/users/", 
                json={
                    "role": "student",
                    "staff_id": "DELETE001",
                    "first_name": "Delete",
                    "last_name": "Me",
                    "email": "delete@example.com",
                    "password": "password123",
                    "phone_number": "1234567890",
                    "birth_date": "2000-01-01",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.delete("/users/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))