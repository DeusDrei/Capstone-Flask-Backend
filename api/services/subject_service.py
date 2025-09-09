from api.extensions import db
from api.models.subjects import Subject
from api.models.subject_departments import SubjectDepartment
from api.models.departments import Department

class SubjectService:
    @staticmethod
    def create_subject(data):
        """Create a new subject"""
        new_subject = Subject(
            code=data['code'],
            name=data['name'],
            created_by=data['created_by'],
            updated_by=data['updated_by']
        )
        
        db.session.add(new_subject)
        db.session.commit()
        return new_subject

    @staticmethod
    def get_all_subjects(page=1):
        """Get all active subjects with pagination"""
        per_page = 10 
        return Subject.query.filter_by(is_deleted=False).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_subject_by_id(subject_id):
        """Get subject by ID (including soft-deleted ones)"""
        return db.session.get(Subject, subject_id)

    @staticmethod
    def update_subject(subject_id, data):
        """Update subject data"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=False).first()
        if not subject:
            return None
        
        try:
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(subject, key):
                    setattr(subject, key, value)
            
            if 'updated_by' in data:
                subject.updated_by = data['updated_by']
            
            db.session.commit()
            return subject
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_subject(subject_id):
        """Mark subject as deleted (soft delete)"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=False).first()
        if not subject:
            return False
        
        subject.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def get_deleted_subjects(page=1):
        """Get all soft-deleted subjects with pagination"""
        per_page = 10 
        return Subject.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_subject(subject_id):
        """Restore a soft-deleted subject"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=True).first()
        if not subject:
            return False
        
        subject.is_deleted = False
        db.session.commit()
        return True

    @staticmethod
    def get_subjects_by_college_id(college_id: int):
        """Return distinct active subjects linked to a college via SubjectDepartment -> Department."""
        q = (
            db.session.query(Subject)
            .join(SubjectDepartment, SubjectDepartment.subject_id == Subject.id)
            .join(Department, Department.id == SubjectDepartment.department_id)
            .filter(Subject.is_deleted == False, Department.college_id == college_id)
            .distinct()
        )
        return q.all()