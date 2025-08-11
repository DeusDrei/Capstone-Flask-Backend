from api.extensions import db
from api.models.colleges import College

class CollegeService:
    @staticmethod
    def create_college(data):
        """Create a new college"""
        new_college = College(
            abbreviation=data['abbreviation'],
            name=data['name'],
            created_by=data['created_by'],
            updated_by=data['updated_by']
        )
        
        db.session.add(new_college)
        db.session.commit()
        return new_college

    @staticmethod
    def get_all_colleges(page=1):
        """Get all active colleges with pagination"""
        per_page = 10
        return College.query.filter_by(is_deleted=False).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )


    @staticmethod
    def get_college_by_id(college_id):
        """Get college by ID (including soft-deleted ones)"""
        return db.session.get(College, college_id)

    @staticmethod
    def update_college(college_id, data):
        """Update college data"""
        college = College.query.filter_by(id=college_id, is_deleted=False).first()
        if not college:
            return None
        
        try:
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(college, key):  # Only update existing attributes
                    setattr(college, key, value)
            
            # Always update the updated_by field if provided
            if 'updated_by' in data:
                college.updated_by = data['updated_by']
            
            db.session.commit()
            return college
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_college(college_id):
        """Mark college as deleted (soft delete)"""
        college = College.query.filter_by(id=college_id, is_deleted=False).first()
        if not college:
            return False
        
        college.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def get_deleted_colleges(page=1):
        """Get all deleted colleges with pagination"""
        per_page = 10
        return College.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_college(college_id):
        """Restore a soft-deleted college"""
        college = College.query.filter_by(id=college_id, is_deleted=True).first()
        if not college:
            return False
        
        college.is_deleted = False
        db.session.commit()
        return True