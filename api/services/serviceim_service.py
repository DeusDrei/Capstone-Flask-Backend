from api.extensions import db
from api.models.serviceims import ServiceIM
from api.models.colleges import College
from api.models.subjects import Subject
from sqlalchemy.exc import IntegrityError

class ServiceIMService:
    @staticmethod
    def create_serviceim(data):
        """Create a new Service IM with validation"""
        # Validate college exists
        college = College.query.get(data['college_id'])
        if not college:
            raise ValueError("College not found")

        # Validate subject exists
        subject = Subject.query.get(data['subject_id'])
        if not subject:
            raise ValueError("Subject not found")

        serviceim = ServiceIM(
            college_id=data['college_id'],
            subject_id=data['subject_id']
        )
        
        db.session.add(serviceim)
        db.session.commit()
        return serviceim

    @staticmethod
    def get_all_serviceims(page=1):
        """Get all Service IMs with pagination"""
        per_page = 10
        return ServiceIM.query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_serviceim_by_id(serviceim_id):
        """Get Service IM by ID"""
        return ServiceIM.query.get(serviceim_id)

    @staticmethod
    def update_serviceim(serviceim_id, data):
        """Update Service IM data"""
        serviceim = ServiceIM.query.get(serviceim_id)
        if not serviceim:
            return None

        # Validate college if being updated
        if 'college_id' in data:
            college = College.query.get(data['college_id'])
            if not college:
                raise ValueError("College not found")

        # Validate subject if being updated
        if 'subject_id' in data:
            subject = Subject.query.get(data['subject_id'])
            if not subject:
                raise ValueError("Subject not found")

        try:
            for key, value in data.items():
                setattr(serviceim, key, value)
            db.session.commit()
            return serviceim
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Database integrity error")

    @staticmethod
    def delete_serviceim(serviceim_id):
        """Delete a Service IM"""
        serviceim = ServiceIM.query.get(serviceim_id)
        if not serviceim:
            return False

        db.session.delete(serviceim)
        db.session.commit()
        return True

    @staticmethod
    def get_serviceims_by_college(college_id, page=1):
        """Get Service IMs for a specific college with pagination"""
        per_page = 10
        return ServiceIM.query.filter_by(college_id=college_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_serviceims_by_subject(subject_id, page=1):
        """Get Service IMs for a specific subject with pagination"""
        per_page = 10
        return ServiceIM.query.filter_by(subject_id=subject_id).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )