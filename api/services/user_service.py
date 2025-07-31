from api.extensions import db
from api.models.users import User
from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    @staticmethod
    def create_user(data):
        """Create a new user with role validation"""
        VALID_ROLES = ['Faculty', 'Technical Admin', 'UTLDO Admin', 'Evaluator']
    
        # Validate role
        if 'role' not in data or data['role'] not in VALID_ROLES:
            raise ValueError(
                f"Invalid role '{data.get('role')}'. Must be one of: {', '.join(VALID_ROLES)}"
            )
        
        new_user = User(
            role=data['role'],
            faculty_id=data['faculty_id'],
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
        return new_user

    @staticmethod
    def get_all_users():
        """Get all active users"""
        return User.query.filter_by(is_deleted=False).all()

    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID (including soft-deleted ones)"""
        return db.session.get(User, user_id)

    @staticmethod
    def get_active_user(user_id):
        """Get only active user by ID"""
        return User.query.filter_by(id=user_id, is_deleted=False).first()

    @staticmethod
    def update_user(user_id, data):
        """Update user data with role validation if provided"""
        VALID_ROLES = ['Faculty', 'Technical Admin', 'UTLDO Admin', 'Evaluator'] 
        
        user = User.query.filter_by(id=user_id, is_deleted=False).first()
        if not user:
            return None
        
        try:
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
    def get_deleted_users():
        """Get all soft-deleted users"""
        return User.query.filter_by(is_deleted=True).all()

    @staticmethod
    def restore_user(user_id):
        """Restore a soft-deleted user"""
        user = User.query.filter_by(id=user_id, is_deleted=True).first()
        if not user:
            return False
        
        user.is_deleted = False
        db.session.commit()
        return True