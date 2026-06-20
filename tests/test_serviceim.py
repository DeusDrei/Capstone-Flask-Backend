from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from api.models.subjects import Subject 
from datetime import datetime, UTC

class ServiceIMTestCase(TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.testing = True

        with self.app.app_context():
            db.create_all()
            self._create_test_data()
    
    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            for table in reversed(db.metadata.sorted_tables):
                db.session.execute(table.delete())
            db.session.commit()
    
    def _create_test_data(self):
        """Create test data for colleges and subjects"""
        from api.models.colleges import College
        from api.models.subjects import Subject
        
        # Create test college
        test_college = College(
            abbreviation="TESTCOL",
            name="Test College",
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_college)
        
        # Create test subject
        test_subject = Subject(
            code="TEST101",
            name="Test Subject",
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_subject)
        
        db.session.commit()
        
        # Store IDs for later use
        self.test_college_id = test_college.id
        self.test_subject_id = test_subject.id
    
    def _register_and_login(self):
        """Helper method to register and login a test user"""
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

    def test_create_serviceim_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    "subject_id": self.test_subject_id
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertIn("id", data)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_serviceim_missing_fields(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    # Missing subject_id
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_serviceim_invalid_foreign_keys(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/serviceims/", 
                json={
                    "college_id": 9999,  # Invalid college
                    "subject_id": 9999   # Invalid subject
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_serviceim_by_id(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            create_response = self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    "subject_id": self.test_subject_id
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Then get
            response = self.client.get(f"/serviceims/{create_data['id']}", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["college_id"], self.test_college_id)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_all_serviceims(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create a test record
            self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    "subject_id": self.test_subject_id
                },
                headers=auth_header
            )
            
            response = self.client.get("/serviceims/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertGreater(len(data), 0)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_serviceim(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create first
            create_response = self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    "subject_id": self.test_subject_id
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Create new subject within app context
            with self.app.app_context():
                new_subject = Subject(
                    code="TEST102",
                    name="Another Test Subject",
                    created_by="system",
                    updated_by="system"
                )
                db.session.add(new_subject)
                db.session.commit()
                new_subject_id = new_subject.id
            
            # Then update
            response = self.client.put(f"/serviceims/{create_data['id']}", 
                json={
                    "subject_id": new_subject_id
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify update
            get_response = self.client.get(f"/serviceims/{create_data['id']}", headers=auth_header)
            updated_data = json.loads(get_response.data)
            self.assertEqual(updated_data["subject_id"], new_subject_id)
            
        except ValueError as e:
            self.fail(str(e))
    
    def test_delete_serviceim(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create first
            create_response = self.client.post("/serviceims/", 
                json={
                    "college_id": self.test_college_id,
                    "subject_id": self.test_subject_id
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Then delete
            response = self.client.delete(f"/serviceims/{create_data['id']}", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            
            # Verify deletion
            get_response = self.client.get(f"/serviceims/{create_data['id']}", headers=auth_header)
            self.assertEqual(get_response.status_code, 404)
        except ValueError as e:
            self.fail(str(e))
    
    def test_serviceim_unauthorized_access(self):
        # Test without authentication
        response = self.client.post("/serviceims/", 
            json={
                "college_id": self.test_college_id,
                "subject_id": self.test_subject_id
            }
        )
        self.assertIn(response.status_code, [401, 403])