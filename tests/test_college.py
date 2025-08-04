from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import datetime, UTC

class CollegeTestCase(TestCase):
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
            "faculty_id": "TEST123",
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
        
        if register_response.status_code != 201:
            raise ValueError(f"Registration failed: {register_response.data}")
        
        # Login and get token
        login_response = self.client.post("/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        
        login_data = json.loads(login_response.data)
        
        if login_response.status_code != 200 or 'access_token' not in login_data:
            raise ValueError(f"Login failed: {login_data}")
            
        return f"Bearer {login_data['access_token']}"

    # College Test Cases
    def test_create_college_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/colleges/", 
                json={
                    "abbreviation": "CE",
                    "name": "College of Engineering",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_college_unauthorized(self):
        response = self.client.post("/colleges/", 
            json={
                "abbreviation": "COC",
                "name": "College of Communication",
                "created_by": "system",
                "updated_by": "system"
            }
        )
        self.assertIn(response.status_code, [400, 401])
    
    def test_create_college_incomplete_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/colleges/", 
                json={
                    "abbreviation": "CCIS"  # Missing required fields
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_college_duplicate_abbreviation_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CAF",
                    "name": "College of Accountancy and Finance",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Try duplicate
            response = self.client.post("/colleges/", 
                json={
                    "abbreviation": "CAF",
                    "name": "Another Accountancy College",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_college_duplicate_name_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CBA1",
                    "name": "College of Business Administration",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.post("/colleges/", 
                json={
                    "abbreviation": "CBA2",
                    "name": "College of Business Administration",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_college_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create college first
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CCIS",
                    "name": "College of Computer and Information Sciences",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Update the college
            response = self.client.put("/colleges/1", 
                json={
                    "name": "College of Computing and Information Sciences",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_colleges(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.get("/colleges/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_college_by_id_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create college first
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CE",
                    "name": "College of Engineering",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.get("/colleges/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_college_by_id_not_found(self):
        auth_header = {"Authorization": self._register_and_login()}
        response = self.client.get("/colleges/999", headers=auth_header)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_college_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create college first
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "COC",
                    "name": "College of Communication",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.delete("/colleges/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_restore_college_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete college first
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CAF",
                    "name": "College of Accountancy and Finance",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/colleges/1", headers=auth_header)

            # Restore the college
            response = self.client.post("/colleges/1/restore", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_deleted_colleges(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete a college
            self.client.post("/colleges/", 
                json={
                    "abbreviation": "CBA",
                    "name": "College of Business Administration",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/colleges/1", headers=auth_header)

            # Get deleted colleges
            response = self.client.get("/colleges/deleted", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(len(data) > 0)
        except ValueError as e:
            self.fail(str(e))