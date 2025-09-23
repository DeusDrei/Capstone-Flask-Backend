from api.extensions import db
from api.models.users import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, decode_token
from datetime import datetime, UTC

class AuthService:
    @staticmethod
    def register_user(data):
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
        return new_user

    @staticmethod
    def authenticate_user(email, password):
        user = User.query.filter_by(email=email, is_deleted=False).first()
        
        if user and check_password_hash(user.password, password):
            return user
        return None

    @staticmethod
    def create_access_token(identity):
        """
        Create a JWT token using Flask-JWT-Extended.
        """
        return create_access_token(
            identity=str(identity.id),
            additional_claims={
                "role": identity.role,
                "email": identity.email,
                "staff_id": identity.staff_id,
                "first_name": identity.first_name,
                "last_name": identity.last_name
            }            
        )
    
    @staticmethod
    def decode_access_token(token):
        """
        Decode a JWT token using Flask-JWT-Extended.
        """
        try:
            payload = decode_token(token)
            return payload
        except Exception as e:
            return e