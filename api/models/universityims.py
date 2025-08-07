from api.extensions import db

class UniversityIM(db.Model):
    __tablename__ = 'universityims'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    year_level = db.Column(db.Integer, nullable=False)
    
    college = db.relationship('College', backref='university_ims')
    department = db.relationship('Department', backref='university_ims')
    subject = db.relationship('Subject', backref='university_ims')

    def __init__(self, college_id, department_id, subject_id, year_level):
        self.college_id = college_id
        self.department_id = department_id
        self.subject_id = subject_id
        self.year_level = year_level

    def __repr__(self):
        return f'<UniversityIM {self.id}>'