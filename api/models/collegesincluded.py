from api.extensions import db

class CollegeIncluded(db.Model):
    __tablename__ = 'collegesincluded'

    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False)
    
    college = db.relationship('College', backref='included_users')
    user = db.relationship('User', backref='included_colleges')

    def __init__(self, college_id, user_id):
        self.college_id = college_id
        self.user_id = user_id

    def __repr__(self):
        return f'<CollegeIncluded college_id={self.college_id}, user_id={self.user_id}>'