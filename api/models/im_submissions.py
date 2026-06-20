from datetime import datetime, UTC
from api.extensions import db

class IMSubmission(db.Model):
    __tablename__ = 'im_submissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    im_id = db.Column(db.Integer, db.ForeignKey('instructionalmaterials.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    date_submitted = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)

    user = db.relationship('User', backref='im_submissions')
    instructional_material = db.relationship('InstructionalMaterial', backref='submissions')

    def __init__(self, user_id, im_id, due_date=None):
        self.user_id = user_id
        self.im_id = im_id
        self.due_date = due_date

    def __repr__(self):
        return f'<IMSubmission id={self.id}, user_id={self.user_id}, im_id={self.im_id}>'
