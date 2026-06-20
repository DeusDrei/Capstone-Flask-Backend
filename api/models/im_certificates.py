from datetime import datetime, UTC
from api.extensions import db

class IMCertificate(db.Model):
    __tablename__ = 'im_certificates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    qr_id = db.Column(db.String(50), unique=True, nullable=False)
    im_id = db.Column(db.Integer, db.ForeignKey('instructionalmaterials.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    s3_link = db.Column(db.String(500), nullable=False)
    date_issued = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))

    instructional_material = db.relationship('InstructionalMaterial', backref='certificates')
    user = db.relationship('User', backref='certificates')

    def __init__(self, qr_id, im_id, user_id, s3_link, date_issued):
        self.qr_id = qr_id
        self.im_id = im_id
        self.user_id = user_id
        self.s3_link = s3_link
        self.date_issued = date_issued

    def __repr__(self):
        return f'<IMCertificate {self.qr_id}>'
