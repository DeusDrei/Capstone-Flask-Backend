from api.extensions import db
from api.models.departments import Department

class DepartmentService:
    @staticmethod
    def create_department(data):
        """Create a new department"""
        new_department = Department(
            abbreviation=data['abbreviation'],
            college_id=data['college_id'],
            name=data['name'],
            created_by=data['created_by'],
            updated_by=data['updated_by']
        )
        
        db.session.add(new_department)
        db.session.commit()
        return new_department

    @staticmethod
    def get_all_departments():
        """Get all active departments (no pagination)"""
        return Department.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_departments_by_college_id(college_id):
        """Get all active departments for a given college_id (no pagination)"""
        return Department.query.filter_by(college_id=college_id, is_deleted=False).all()
    
    @staticmethod
    def get_department_by_id(department_id):
        """Get department by ID (including soft-deleted ones)"""
        return db.session.get(Department, department_id)

    @staticmethod
    def update_department(department_id, data):
        """Update department data"""
        department = Department.query.filter_by(id=department_id, is_deleted=False).first()
        if not department:
            return None
        
        try:
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(department, key):  # Only update existing attributes
                    setattr(department, key, value)
            
            # Always update the updated_by field if provided
            if 'updated_by' in data:
                department.updated_by = data['updated_by']
            
            db.session.commit()
            return department
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_department(department_id):
        """Mark department as deleted (soft delete)"""
        department = Department.query.filter_by(id=department_id, is_deleted=False).first()
        if not department:
            return False
        
        department.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def get_deleted_departments(page=1):
        """Get all soft-deleted departments with pagination"""
        per_page = 10
        return Department.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_department(department_id):
        """Restore a soft-deleted department"""
        department = Department.query.filter_by(id=department_id, is_deleted=True).first()
        if not department:
            return False
        
        department.is_deleted = False
        db.session.commit()
        return True