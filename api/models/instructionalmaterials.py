from datetime import datetime, UTC
from api.extensions import db

class InstructionalMaterial(db.Model):
    __tablename__ = 'instructionalmaterials'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    im_type = db.Column(db.String(50), nullable=False)
    university_im_id = db.Column(db.Integer, db.ForeignKey('universityims.id'), nullable=True)
    service_im_id = db.Column(db.Integer, db.ForeignKey('serviceims.id'), nullable=True)
    imerpimec_id = db.Column(db.Integer, db.ForeignKey('imerpimec.id'), nullable=True)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), nullable=False)
    validity = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    s3_link = db.Column(db.String(500), nullable=True)  # Made nullable for assignment workflow
    notes = db.Column(db.Text, nullable=True)
    published = db.Column(db.Integer, default=0, nullable=False)
    utldo_attempt = db.Column(db.Integer, default=0, nullable=False)
    pimec_attempt = db.Column(db.Integer, default=0, nullable=False)
    ai_attempt = db.Column(db.Integer, default=0, nullable=False)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    university_im = db.relationship('UniversityIM', backref='instructional_materials')
    service_im = db.relationship('ServiceIM', backref='instructional_materials')
    imerpimec = db.relationship('IMERPIMEC', backref='instructional_materials')
    assigned_by_user = db.relationship('User', foreign_keys=[assigned_by], backref='assigned_materials')

    def __init__(self, im_type, status, validity, version, s3_link, created_by, updated_by, university_im_id=None, service_im_id=None, imerpimec_id=None, assigned_by=None, notes=None, published=0, utldo_attempt=0, pimec_attempt=0, ai_attempt=0):
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
        self.imerpimec_id = imerpimec_id
        self.assigned_by = assigned_by
        self.published = published
        self.utldo_attempt = utldo_attempt
        self.pimec_attempt = pimec_attempt
        self.ai_attempt = ai_attempt

    def __repr__(self):
        return f'<InstructionalMaterial {self.id}: {self.im_type} ({self.version})>'