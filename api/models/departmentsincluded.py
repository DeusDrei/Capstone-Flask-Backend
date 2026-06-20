from api.extensions import db

class DepartmentIncluded(db.Model):
    __tablename__ = 'departmentsincluded'

    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False)
    
    department = db.relationship('Department', backref='included_users')
    user = db.relationship('User', backref='included_departments')

    def __init__(self, department_id, user_id):
        self.department_id = department_id
        self.user_id = user_id

    def __repr__(self):
        return f'<DepartmentIncluded department_id={self.department_id}, user_id={self.user_id}>'