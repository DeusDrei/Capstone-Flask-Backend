from api.extensions import db
from api.models.universityims import UniversityIM
from api.models.colleges import College
from api.models.departments import Department
from api.models.subjects import Subject
from sqlalchemy.exc import IntegrityError

class UniversityIMService:
    @staticmethod
    def create_universityim(data):
        """Create a new University IM entry with foreign key validation"""
        # Validate foreign keys exist
        college = College.query.filter_by(id=data['college_id'], is_deleted=False).first()
        if not college:
            raise ValueError("College not found or is deleted")
            
        department = Department.query.filter_by(id=data['department_id'], is_deleted=False).first()
        if not department:
            raise ValueError("Department not found or is deleted")
            
        subject = Subject.query.filter_by(id=data['subject_id'], is_deleted=False).first()
        if not subject:
            raise ValueError("Subject not found or is deleted")

        new_universityim = UniversityIM(
            college_id=data['college_id'],
            department_id=data['department_id'],
            subject_id=data['subject_id'],
            year_level=data['year_level']
        )
        
        db.session.add(new_universityim)
        try:
            db.session.commit()
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError("Database integrity error") from e
            
        return new_universityim

    @staticmethod
    def get_all_universityims():
        """Get all University IM entries"""
        return UniversityIM.query.all()

    @staticmethod
    def get_universityim_by_id(universityim_id):
        """Get University IM by ID"""
        return db.session.get(UniversityIM, universityim_id)

    @staticmethod
    def update_universityim(universityim_id, data):
        """Update University IM data"""
        universityim = UniversityIM.query.get(universityim_id)
        if not universityim:
            return None
        
        try:
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(universityim, key):
                    setattr(universityim, key, value)
            
            db.session.commit()
            return universityim
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def delete_universityim(universityim_id):
        """Delete a University IM entry"""
        universityim = UniversityIM.query.get(universityim_id)
        if not universityim:
            return False
        
        db.session.delete(universityim)
        db.session.commit()
        return True

    @staticmethod
    def get_universityims_by_college(college_id):
        """Get all University IMs for a specific college"""
        return UniversityIM.query.filter_by(college_id=college_id).all()

    @staticmethod
    def get_universityims_by_department(department_id):
        """Get all University IMs for a specific department"""
        return UniversityIM.query.filter_by(department_id=department_id).all()

    @staticmethod
    def get_universityims_by_subject(subject_id):
        """Get all University IMs for a specific subject"""
        return UniversityIM.query.filter_by(subject_id=subject_id).all()