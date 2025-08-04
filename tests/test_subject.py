from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import datetime, UTC

class SubjectTestCase(TestCase):
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

    # Subject Test Cases
    def test_create_subject_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/subjects/", 
                json={
                    "code": "MATH101",
                    "name": "Introduction to Mathematics",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_subject_unauthorized(self):
        response = self.client.post("/subjects/", 
            json={
                "code": "CS101",
                "name": "Introduction to Computer Science",
                "created_by": "system",
                "updated_by": "system"
            }
        )
        self.assertIn(response.status_code, [400, 401])
    
    def test_create_subject_incomplete_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/subjects/", 
                json={
                    "code": "PHYS101"  # Missing required fields
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_subject_duplicate_code_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            self.client.post("/subjects/", 
                json={
                    "code": "ENG101",
                    "name": "Introduction to English",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Try duplicate
            response = self.client.post("/subjects/", 
                json={
                    "code": "ENG101",
                    "name": "Advanced English",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_subject_duplicate_name_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            self.client.post("/subjects/", 
                json={
                    "code": "CHEM101",
                    "name": "Introduction to Chemistry",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.post("/subjects/", 
                json={
                    "code": "CHEM102",
                    "name": "Introduction to Chemistry",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_subject_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create subject first
            self.client.post("/subjects/", 
                json={
                    "code": "CS101",
                    "name": "Introduction to Computer Science",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Update the subject
            response = self.client.put("/subjects/1", 
                json={
                    "name": "Fundamentals of Computer Science",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_subjects(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.get("/subjects/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_subject_by_id_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create subject first
            self.client.post("/subjects/", 
                json={
                    "code": "MATH101",
                    "name": "Introduction to Mathematics",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.get("/subjects/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_subject_by_id_not_found(self):
        auth_header = {"Authorization": self._register_and_login()}
        response = self.client.get("/subjects/999", headers=auth_header)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_subject_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create subject first
            self.client.post("/subjects/", 
                json={
                    "code": "PHYS101",
                    "name": "Introduction to Physics",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.delete("/subjects/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_restore_subject_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete subject first
            self.client.post("/subjects/", 
                json={
                    "code": "CHEM101",
                    "name": "Introduction to Chemistry",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/subjects/1", headers=auth_header)

            # Restore the subject
            response = self.client.post("/subjects/1/restore", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_deleted_subjects(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete a subject
            self.client.post("/subjects/", 
                json={
                    "code": "BIO101",
                    "name": "Introduction to Biology",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/subjects/1", headers=auth_header)

            # Get deleted subjects
            response = self.client.get("/subjects/deleted", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertTrue(len(data) > 0)
        except ValueError as e:
            self.fail(str(e))