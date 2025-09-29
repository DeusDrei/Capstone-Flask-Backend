from api.extensions import db
from api.models.departmentsincluded import DepartmentIncluded
from api.models.departments import Department
from api.models.users import User
from sqlalchemy.exc import IntegrityError

class DepartmentIncludedService:
    @staticmethod
    def create_association(department_id, user_id):
        """Create a new department-user association"""
        if not Department.query.get(department_id):
            raise ValueError(f"Department with ID {department_id} does not exist")

        if not User.query.get(user_id):
            raise ValueError(f"User with ID {user_id} does not exist")
        
        try:
            association = DepartmentIncluded(
                department_id=department_id,
                user_id=user_id
            )
            db.session.add(association)
            db.session.commit()
            return association
        except IntegrityError as e:
            db.session.rollback()
            if "department_id" in str(e.orig):
                raise ValueError("Department does not exist")
            elif "user_id" in str(e.orig):
                raise ValueError("User does not exist")
            elif "unique constraint" in str(e.orig).lower():
                raise ValueError("This association already exists")
            raise ValueError("Database integrity error")

    @staticmethod
    def get_association(department_id, user_id):
        """Get a specific department-user association"""
        return DepartmentIncluded.query.filter_by(
            department_id=department_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_departments_for_user(user_id):
        """Get all departments associated with a user"""
        return DepartmentIncluded.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_users_for_department(department_id):
        """Get all users associated with a department"""
        return DepartmentIncluded.query.filter_by(department_id=department_id).all()

    @staticmethod
    def delete_association(department_id, user_id):
        """Delete a department-user association"""
        association = DepartmentIncluded.query.filter_by(
            department_id=department_id,
            user_id=user_id
        ).first()
        
        if not association:
            return False
            
        db.session.delete(association)
        db.session.commit()
        return True