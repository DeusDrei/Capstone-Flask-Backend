from datetime import datetime, UTC
from api.extensions import db

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    abbreviation = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    college = db.relationship('College', backref='included_departments')

    def __init__(self, college_id, abbreviation, name, created_by, updated_by):
        self.college_id = college_id
        self.abbreviation = abbreviation
        self.name = name
        self.updated_by = updated_by
        self.created_by = created_by

    def __repr__(self):
        return f'<Department {self.id}: {self.name} ({self.abbreviation})>'