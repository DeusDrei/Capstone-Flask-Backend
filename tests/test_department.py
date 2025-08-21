from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import date
from api.models.users import User
from api.models.colleges import College
from werkzeug.security import generate_password_hash

class DepartmentTestCase(TestCase):
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
        """Create test data for colleges and users"""
        # Create test college
        test_college = College(
            abbreviation="TESTCOL",
            name="Test College",
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_college)
        
        # Create test admin user
        test_user = User(
            role="Technical Admin",
            staff_id="TEST123",
            first_name="Test",
            last_name="User",
            email="testuser@example.com",
            password=generate_password_hash("testpassword"),
            phone_number="1234567890",
            birth_date=date(1990, 1, 1),
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_user)
        db.session.commit()
        self.test_college_id = test_college.id
        self.test_user_id = test_user.id

    def _register_and_login(self):
        # Login with the pre-created user
        login_response = self.client.post("/auth/login", json={
            "email": "testuser@example.com",
            "password": "testpassword"
        })
        login_data = json.loads(login_response.data)
        if login_response.status_code != 200 or 'access_token' not in login_data:
            raise ValueError(f"Login failed: {login_data}")
        return f"Bearer {login_data['access_token']}"

    # Department Test Cases
    def test_create_department_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "CS",
                    "name": "Computer Science Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_department_unauthorized(self):
        response = self.client.post("/departments/", 
            json={
                "college_id": self.test_college_id,
                "abbreviation": "MATH",
                "name": "Mathematics Department",
                "created_by": "system",
                "updated_by": "system"
            }
        )
        self.assertIn(response.status_code, [400, 401])
    
    def test_create_department_incomplete_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/departments/", 
                json={
                    "abbreviation": "ENG"  # Missing required fields
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_department_duplicate_abbreviation_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "PHYS",
                    "name": "Physics Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Try duplicate
            response = self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "PHYS",
                    "name": "Another Physics Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_department_duplicate_name_fail(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "CHEM1",
                    "name": "Chemistry Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "CHEM2",
                    "name": "Chemistry Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 409)
        except ValueError as e:
            self.fail(str(e))
    
    def test_update_department_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create department first
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "BIO",
                    "name": "Biology Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            # Update the department
            response = self.client.put("/departments/1", 
                json={
                    "name": "Biological Sciences Department",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_departments(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.get("/departments/", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_department_by_id_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create department first
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "ENG",
                    "name": "Engineering Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.get("/departments/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_department_by_id_not_found(self):
        auth_header = {"Authorization": self._register_and_login()}
        response = self.client.get("/departments/999", headers=auth_header)
        self.assertEqual(response.status_code, 404)
    
    def test_delete_department_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create department first
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "PHIL",
                    "name": "Philosophy Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )

            response = self.client.delete("/departments/1", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_restore_department_successful(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete department first
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "HIST",
                    "name": "History Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/departments/1", headers=auth_header)

            # Restore the department
            response = self.client.post("/departments/1/restore", headers=auth_header)
            self.assertEqual(response.status_code, 200)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_deleted_departments(self):
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create and delete a department
            self.client.post("/departments/", 
                json={
                    "college_id": self.test_college_id,
                    "abbreviation": "ART",
                    "name": "Art Department",
                    "created_by": "testuser@example.com",
                    "updated_by": "testuser@example.com"
                },
                headers=auth_header
            )
            self.client.delete("/departments/1", headers=auth_header)

            # Get deleted departments
            response = self.client.get("/departments/deleted", headers=auth_header)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            # The deleted departments are now under 'departments' key due to pagination
            self.assertTrue(len(data.get('departments', [])) > 0)
        except ValueError as e:
            self.fail(str(e))