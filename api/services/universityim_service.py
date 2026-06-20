from api.extensions import db
from api.models.universityims import UniversityIM
from api.services.activitylog_service import ActivityLogService
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
        
        if data.get('user_id'):
            ActivityLogService.log_activity(
                user_id=data['user_id'],
                action="CREATE",
                table_name="universityims",
                description=f"Created university IM {new_universityim.id}",
                record_id=new_universityim.id,
                new_values={"subject_id": new_universityim.subject_id, "year_level": new_universityim.year_level}
            )
            
        return new_universityim

    @staticmethod
    def get_all_universityims(page=1):
        """Get all University IM entries with pagination"""
        per_page = 10 
        return UniversityIM.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

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
            # Capture old values before update
            old_values = {
                "college_id": universityim.college_id,
                "department_id": universityim.department_id,
                "subject_id": universityim.subject_id,
                "year_level": universityim.year_level
            }
            
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(universityim, key):
                    setattr(universityim, key, value)
            
            db.session.commit()
            
            if data.get('user_id'):
                ActivityLogService.log_activity(
                    user_id=data['user_id'],
                    action="UPDATE",
                    table_name="universityims",
                    description=f"Updated university IM {universityim_id}",
                    record_id=universityim_id,
                    old_values=old_values,
                    new_values={"college_id": universityim.college_id, "department_id": universityim.department_id, "subject_id": universityim.subject_id, "year_level": universityim.year_level}
                )
            
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
    def get_universityims_by_college(college_id, page=1):
        """Get all University IMs for a specific college with pagination"""
        per_page = 10
        return UniversityIM.query.filter_by(college_id=college_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_universityims_by_department(department_id, page=1):
        """Get all University IMs for a specific department with pagination"""
        per_page = 10
        return UniversityIM.query.filter_by(department_id=department_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_universityims_by_subject(subject_id, page=1):
        """Get all University IMs for a specific subject with pagination"""
        per_page = 10
        return UniversityIM.query.filter_by(subject_id=subject_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )