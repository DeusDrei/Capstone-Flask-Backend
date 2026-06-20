from api.extensions import db


class SubjectDepartment(db.Model):
    __tablename__ = 'subject_departments'

    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), primary_key=True, nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), primary_key=True, nullable=False)

    subject = db.relationship('Subject', backref='subject_departments')
    department = db.relationship('Department', backref='subject_departments')

    def __init__(self, subject_id, department_id):
        self.subject_id = subject_id
        self.department_id = department_id

    def __repr__(self):
        return f'<SubjectDepartment subject_id={self.subject_id}, department_id={self.department_id}>'
