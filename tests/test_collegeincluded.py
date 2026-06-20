from unittest import TestCase
from api import create_app
from api.extensions import db
import json
from datetime import datetime, date
from api.models.users import User
from api.models.colleges import College
from werkzeug.security import generate_password_hash, check_password_hash

class CollegeIncludedTestCase(TestCase):
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
        
        # Create test admin user with proper date object
        test_user = User(
            role="Technical Admin",
            staff_id="TEST123",
            first_name="Test",
            last_name="Admin",
            email="testadmin@example.com",
            password=generate_password_hash("testpassword"), 
            phone_number="1234567890",
            birth_date=date(1990, 1, 1),  # Using date object instead of string
            created_by="system",
            updated_by="system"
        )
        db.session.add(test_user)
        
        db.session.commit()
        
        # Store IDs for later use
        self.test_college_id = test_college.id
        self.test_user_id = test_user.id
    
    def _register_and_login(self):
        """Helper method to register and login the test admin user"""
        # Login with the pre-created user
        login_response = self.client.post("/auth/login", json={
            "email": "testadmin@example.com",
            "password": "testpassword"
        })
        
        login_data = json.loads(login_response.data)
        
        if login_response.status_code != 200 or 'access_token' not in login_data:
            raise ValueError(f"Login failed: {login_data}")
            
        return f"Bearer {login_data['access_token']}"

    def test_create_association_successful(self):
        """Test successful creation of college-user association"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            response = self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 201)
            data = json.loads(response.data)
            self.assertIn("college_id", data)
            self.assertIn("user_id", data)
        except ValueError as e:
            self.fail(str(e))
    
    def test_create_association_duplicate(self):
        """Test duplicate association prevention"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First creation
            self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            
            # Attempt duplicate
            response = self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            self.assertEqual(response.status_code, 400)
            data = json.loads(response.data)
            self.assertIn("error", data)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_association(self):
        """Test retrieving a specific association"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            create_response = self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            
            # Then get
            response = self.client.get(
                f"/college-included/college/{self.test_college_id}/user/{self.test_user_id}", 
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["college_id"], self.test_college_id)
            self.assertEqual(data["user_id"], self.test_user_id)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_colleges_for_user(self):
        """Test retrieving all colleges for a user"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create association
            self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            
            response = self.client.get(
                f"/college-included/user/{self.test_user_id}", 
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertGreater(len(data), 0)
            self.assertEqual(data[0]["college_id"], self.test_college_id)
        except ValueError as e:
            self.fail(str(e))
    
    def test_get_users_for_college(self):
        """Test retrieving all users for a college"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # Create association
            self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            
            response = self.client.get(
                f"/college-included/college/{self.test_college_id}", 
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertGreater(len(data), 0)
            self.assertEqual(data[0]["user_id"], self.test_user_id)
        except ValueError as e:
            self.fail(str(e))
    
    def test_delete_association(self):
        """Test deleting an association"""
        try:
            auth_header = {"Authorization": self._register_and_login()}
            
            # First create
            self.client.post("/college-included/", 
                json={
                    "college_id": self.test_college_id,
                    "user_id": self.test_user_id
                },
                headers=auth_header
            )
            
            # Then delete
            response = self.client.delete(
                f"/college-included/college/{self.test_college_id}/user/{self.test_user_id}", 
                headers=auth_header
            )
            self.assertEqual(response.status_code, 200)
            
            # Verify deletion
            get_response = self.client.get(
                f"/college-included/college/{self.test_college_id}/user/{self.test_user_id}", 
                headers=auth_header
            )
            self.assertEqual(get_response.status_code, 404)
        except ValueError as e:
            self.fail(str(e))
    
    def test_unauthorized_access(self):
        """Test unauthorized access attempts"""
        # Test creation without authentication
        response = self.client.post("/college-included/", 
            json={
                "college_id": self.test_college_id,
                "user_id": self.test_user_id
            }
        )
        self.assertEqual(response.status_code, 401)