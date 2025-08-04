from datetime import datetime, UTC
from api.extensions import db

class College(db.Model):
    __tablename__ = 'colleges'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    abbreviation = db.Column(db.String, nullable=False, unique=True)
    name = db.Column(db.String, nullable=False, unique=True)
    created_by = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, abbreviation, name, created_by, updated_by):
        self.abbreviation = abbreviation
        self.name = name
        self.updated_by = updated_by
        self.created_by = created_by

    def __repr__(self):
        return f'<College {self.id}: {self.name} ({self.abbreviation})>'