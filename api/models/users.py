from datetime import datetime, UTC
from api.extensions import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    role = db.Column(db.String, nullable=False)
    faculty_id = db.Column(db.String, unique=True, nullable=False)
    first_name = db.Column(db.String, nullable=False)
    middle_name = db.Column(db.String)
    last_name = db.Column(db.String, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, role, faculty_id, first_name, last_name, email, password, phone_number, birth_date,
                 created_by, updated_by, middle_name=None):
        self.role = role
        self.faculty_id = faculty_id
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