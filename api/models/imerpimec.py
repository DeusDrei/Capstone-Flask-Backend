from datetime import datetime, UTC
from api.extensions import db

class IMERPIMEC(db.Model):
    __tablename__ = 'imerpimec'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    a = db.Column(db.Integer, default=0, nullable=False)
    b = db.Column(db.Integer, default=0, nullable=False)
    c = db.Column(db.Integer, default=0, nullable=False)
    d = db.Column(db.Integer, default=0, nullable=False)
    e = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, a, b, c, d, e, created_by, updated_by):
        self.a = a
        self.b = b
        self.c = c
        self.d = d
        self.e = e
        self.updated_by = updated_by
        self.created_by = created_by

    def __repr__(self):
        return f'<IMERPIMEC {self.id}>'