from datetime import datetime, UTC
from api.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.String(50), nullable=False)
    staff_id = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    middle_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, role, staff_id, first_name, last_name, email, password, phone_number, birth_date,
                 created_by, updated_by, middle_name=None):
        self.role = role
        self.staff_id = staff_id
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.phone_number = phone_number
        self.birth_date = birth_date
        self.updated_by = updated_by
        self.created_by = created_by
        self.middle_name = middle_name

    def __repr__(self):
        return f'<User {self.id}: {self.first_name} {self.last_name}>'