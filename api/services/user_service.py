from api.extensions import db
from api.models.users import User
from api.services.activitylog_service import ActivityLogService
from api.models.collegesincluded import CollegeIncluded
from api.models.colleges import College
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import case, func

class UserService:
    @staticmethod
    def create_user(data):
        """Create a new user with role validation"""
        VALID_ROLES = ['Faculty', 'Technical Admin', 'UTLDO Admin', 'PIMEC']
    
        # Validate role
        if 'role' not in data or data['role'] not in VALID_ROLES:
            raise ValueError(
                f"Invalid role '{data.get('role')}'. Must be one of: {', '.join(VALID_ROLES)}"
            )
        
        new_user = User(
            role=data['role'],
            staff_id=data['staff_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            password=generate_password_hash(data['password']),
            phone_number=data['phone_number'],
            birth_date=data['birth_date'],
            created_by=data['created_by'],
            updated_by=data['updated_by'],
            middle_name=data.get('middle_name')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        if data.get('user_id'):
            ActivityLogService.log_activity(
                user_id=data['user_id'],
                action="CREATE",
                table_name="users",
                description=f"Created user {new_user.id}",
                record_id=new_user.id,
                new_values={"email": new_user.email, "role": new_user.role}
            )
        
        return new_user

    @staticmethod
    def get_all_users(page=1, sort_by=None, sort_dir='asc'):
        """Get all active users with pagination and optional sorting across dataset.

        sort_by: one of allowed columns (id, last_name, first_name, middle_name, role, staff_id, email, phone_number, birth_date, updated_at, colleges)
        sort_dir: 'asc' or 'desc'
        """
        per_page = 10
        direction_desc = (str(sort_dir).lower() == 'desc')

        # Base query (may expand for joins if needed)
        query = User.query.filter_by(is_deleted=False)

        # Mapping of allowed direct columns
        allowed = {
            'id': User.id,
            'last_name': User.last_name,
            'first_name': User.first_name,
            'middle_name': User.middle_name,
            'role': User.role,
            'staff_id': User.staff_id,
            'email': User.email,
            'phone_number': User.phone_number,
            'birth_date': User.birth_date,
            'updated_at': User.updated_at,
        }

        if sort_by == 'role':
            # Custom role ordering numeric mapping via CASE
            role_case = case(
                (User.role == 'Technical Admin', 0),
                (User.role == 'UTLDO Admin', 1),
                (User.role == 'PIMEC', 2),
                (User.role == 'Faculty', 3),
                else_=99
            )
            query = query.order_by(role_case.desc() if direction_desc else role_case.asc(), User.last_name.asc())
        elif sort_by == 'colleges':
            # Order by first (alphabetically) college abbreviation associated with user (case-insensitive)
            first_col = func.min(func.lower(College.abbreviation))
            query = query.outerjoin(CollegeIncluded, CollegeIncluded.user_id == User.id) \
                         .outerjoin(College, College.id == CollegeIncluded.college_id) \
                         .group_by(User.id) \
                         .order_by(first_col.desc() if direction_desc else first_col.asc(), User.last_name.asc())
        elif sort_by in allowed:
            col = allowed[sort_by]
            query = query.order_by(col.desc() if direction_desc else col.asc())
        else:
            # Default order (stable) if no or invalid sort provided
            query = query.order_by(User.id.asc())

        return query.paginate(page=page, per_page=per_page, error_out=False)


    @staticmethod
    def get_all_users_no_pagination(sort_by=None, sort_dir='asc'):
        """Get all active users without pagination. Optional basic sorting.

        sort_by: limited subset of columns for safety
        sort_dir: 'asc' or 'desc'
        """
        direction_desc = (str(sort_dir).lower() == 'desc')

        query = User.query.filter_by(is_deleted=False)

        allowed = {
            'id': User.id,
            'last_name': User.last_name,
            'first_name': User.first_name,
            'role': User.role,
            'staff_id': User.staff_id,
            'email': User.email,
            'updated_at': User.updated_at,
        }

        if sort_by == 'role':
            role_case = case(
                (User.role == 'Technical Admin', 0),
                (User.role == 'UTLDO Admin', 1),
                (User.role == 'PIMEC', 2),
                (User.role == 'Faculty', 3),
                else_=99
            )
            query = query.order_by(role_case.desc() if direction_desc else role_case.asc(), User.last_name.asc())
        elif sort_by in allowed:
            col = allowed[sort_by]
            query = query.order_by(col.desc() if direction_desc else col.asc())
        else:
            query = query.order_by(User.id.asc())

        return query.all()


    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID (including soft-deleted ones)"""
        return db.session.get(User, user_id)

    @staticmethod
    def update_user(user_id, data):
        """Update user data with role validation if provided"""
        VALID_ROLES = ['Faculty', 'Technical Admin', 'UTLDO Admin', 'PIMEC'] 
        
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return None
        
        try:
            # Capture old values before update
            old_values = {
                "email": user.email,
                "role": user.role,
                "first_name": user.first_name,
                "last_name": user.last_name
            }
            
            # Validate role if provided in update
            if 'role' in data:
                if data['role'] not in VALID_ROLES:
                    raise ValueError(
                        f"Invalid role '{data['role']}'. Must be one of: {', '.join(VALID_ROLES)}"
                    )
            
            # Handle password hashing
            if 'password' in data:
                data['password'] = generate_password_hash(data['password'])
            
            # Update only the provided fields
            for key, value in data.items():
                if hasattr(user, key):  # Only update existing attributes
                    setattr(user, key, value)
            
            db.session.commit()
            
            if data.get('user_id'):
                ActivityLogService.log_activity(
                    user_id=data['user_id'],
                    action="UPDATE",
                    table_name="users",
                    description=f"Updated user {user_id}",
                    record_id=user_id,
                    old_values=old_values,
                    new_values={"email": user.email, "role": user.role, "first_name": user.first_name, "last_name": user.last_name}
                )
            
            return user
            
        except ValueError as e:
            db.session.rollback()
            raise ValueError(str(e))  # Re-raise with original message
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_user(user_id):
        """Mark user as deleted (soft delete)"""
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return False
        
        user.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def get_deleted_users(page=1):
        """Get all soft-deleted users with pagination"""
        per_page = 10
        return User.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_user(user_id):
        """Restore a soft-deleted user"""
        user = User.query.filter_by(id=user_id, is_deleted=True).first()
        if not user:
            return False
        
        user.is_deleted = False
        db.session.commit()
        return True