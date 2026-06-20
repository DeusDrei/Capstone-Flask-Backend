from datetime import datetime, UTC
from api.extensions import db

class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, code, name, created_by, updated_by):
        self.code = code
        self.name = name
        self.updated_by = updated_by
        self.created_by = created_by

    def __repr__(self):
        return f'<Subject {self.id}: {self.name} ({self.code})>'