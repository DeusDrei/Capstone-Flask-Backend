from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import datetime, UTC

class UniversityIMTestCase(TestCase):
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
        """Create test data for colleges, departments, and subjects"""
        from api.models.colleges import College
        from api.models.departments import Department
        from api.models.subjects import Subject
        
        # Create test college
        test_college = College(
            abbreviation="TESTCOL",
            name="Test College",
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_college)
        
        # Create test department
        test_dept = Department(
            abbreviation="TESTDEPT",
            college_id=1,
            name="Test Department",
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_dept)
        
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
        self.test_dept_id = test_dept.id
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

    def test_create_universityim_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    "subject_id": self.test_subject_id,
                    "year_level": 1
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertIn("id", data)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_universityim_missing_fields(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    # Missing subject_id and year_level
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_universityim_invalid_foreign_keys(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/universityims/", 
                json={
                    "college_id": 9999,  # Invalid college
                    "department_id": 9999,  # Invalid department
                    "subject_id": 9999,  # Invalid subject
                    "year_level": 1
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_universityim_by_id(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            create_response = self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    "subject_id": self.test_subject_id,
                    "year_level": 1
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Then get
            response = self.client.get(f"/universityims/{create_data['id']}", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["college_id"], self.test_college_id)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_all_universityims(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create a test record
            self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    "subject_id": self.test_subject_id,
                    "year_level": 1
                },
                headers=auth_header
            )
            
            response = self.client.get("/universityims/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertGreater(len(data), 0)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_universityim(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create first
            create_response = self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    "subject_id": self.test_subject_id,
                    "year_level": 1
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Then update
            response = self.client.put(f"/universityims/{create_data['id']}", 
                json={
                    "year_level": 2  # Update year level
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify update
            get_response = self.client.get(f"/universityims/{create_data['id']}", headers=auth_header)
            updated_data = json.loads(get_response.data)
            self.assertEqual(updated_data["year_level"], 2)
        except ValueError as e:
            self.fail(str(e))
    
    def test_delete_universityim(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create first
            create_response = self.client.post("/universityims/", 
                json={
                    "college_id": self.test_college_id,
                    "department_id": self.test_dept_id,
                    "subject_id": self.test_subject_id,
                    "year_level": 1
                },
                headers=auth_header
            )
            create_data = json.loads(create_response.data)
            
            # Then delete
            response = self.client.delete(f"/universityims/{create_data['id']}", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            
            # Verify deletion
            get_response = self.client.get(f"/universityims/{create_data['id']}", headers=auth_header)
            self.assertEqual(get_response.status_code, 404)
        except ValueError as e:
            self.fail(str(e))
    
    def test_universityim_unauthorized_access(self):
        # Test without authentication
        response = self.client.post("/universityims/", 
            json={
                "college_id": self.test_college_id,
                "department_id": self.test_dept_id,
                "subject_id": self.test_subject_id,
                "year_level": 1
            }
        )
        self.assertIn(response.status_code, [401, 403])