from api.extensions import db

class ServiceIM(db.Model):
    __tablename__ = 'serviceims'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    
    college = db.relationship('College', backref='service_ims')
    subject = db.relationship('Subject', backref='service_ims')

    def __init__(self, college_id, subject_id):
        self.college_id = college_id
        self.subject_id = subject_id

    def __repr__(self):
        return f'<ServiceIM {self.id}>'