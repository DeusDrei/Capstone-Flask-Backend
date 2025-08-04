from api.extensions import db
from api.models.subjects import Subject

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
    def get_all_subjects():
        """Get all active subjects"""
        return Subject.query.filter_by(is_deleted=False).all()

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
    def get_deleted_subjects():
        """Get all soft-deleted subjects"""
        return Subject.query.filter_by(is_deleted=True).all()

    @staticmethod
    def restore_subject(subject_id):
        """Restore a soft-deleted subject"""
        subject = Subject.query.filter_by(id=subject_id, is_deleted=True).first()
        if not subject:
            return False
        
        subject.is_deleted = False
        db.session.commit()
        return True