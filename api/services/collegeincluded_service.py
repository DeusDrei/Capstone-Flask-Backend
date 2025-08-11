from api.extensions import db
from api.models.collegesincluded import CollegeIncluded
from api.models.colleges import College
from api.models.users import User
from sqlalchemy.exc import IntegrityError

class CollegeIncludedService:
    @staticmethod
    def create_association(college_id, user_id):
        """
        Create a new college-user association
        """
        if not College.query.get(college_id):
            raise ValueError(f"College with ID {college_id} does not exist")

        if not User.query.get(user_id):
            raise ValueError(f"User with ID {user_id} does not exist")
        
        try:
            association = CollegeIncluded(
                college_id=college_id,
                user_id=user_id
            )
            db.session.add(association)
            db.session.commit()
            return association
        except IntegrityError as e:
            db.session.rollback()
            if "college_id" in str(e.orig):
                raise ValueError("College does not exist")
            elif "user_id" in str(e.orig):
                raise ValueError("User does not exist")
            elif "unique constraint" in str(e.orig).lower():
                raise ValueError("This association already exists")
            raise ValueError("Database integrity error")

    @staticmethod
    def get_association(college_id, user_id):
        """
        Get a specific college-user association
        """
        return CollegeIncluded.query.filter_by(
            college_id=college_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_colleges_for_user(user_id):
        """
        Get all colleges associated with a user
        """
        return CollegeIncluded.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_users_for_college(college_id):
        """
        Get all users associated with a college
        """
        return CollegeIncluded.query.filter_by(college_id=college_id).all()

    @staticmethod
    def delete_association(college_id, user_id):
        """
        Delete a college-user association
        """
        association = CollegeIncluded.query.filter_by(
            college_id=college_id,
            user_id=user_id
        ).first()
        
        if not association:
            return False
            
        db.session.delete(association)
        db.session.commit()
        return True