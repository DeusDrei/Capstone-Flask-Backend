from datetime import datetime, UTC
from api.extensions import db

class InstructionalMaterial(db.Model):
    __tablename__ = 'instructionalmaterials'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    im_type = db.Column(db.String, nullable=False)
    university_im_id = db.Column(db.Integer, db.ForeignKey('universityims.id'), nullable=True)
    service_im_id = db.Column(db.Integer, db.ForeignKey('serviceims.id'), nullable=True)
    status = db.Column(db.String, nullable=False)
    validity = db.Column(db.String, nullable=False)
    version = db.Column(db.String, nullable=False)
    s3_link = db.Column(db.String, nullable=False)
    notes = db.Column(db.String, nullable=True)
    created_by = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    university_im = db.relationship('UniversityIM', backref='instructional_materials')
    service_im = db.relationship('ServiceIM', backref='instructional_materials')

    def __init__(self, im_type, status, validity, version, s3_link, created_by, updated_by, university_im_id=None, service_im_id=None, notes=None):
        self.im_type = im_type
        self.status = status
        self.validity = validity
        self.version = version
        self.s3_link = s3_link
        self.created_by = created_by
        self.updated_by = updated_by
        self.notes = notes
        self.university_im_id = university_im_id
        self.service_im_id = service_im_id

    def __repr__(self):
        return f'<InstructionalMaterial {self.id}: {self.im_type} ({self.version})>'