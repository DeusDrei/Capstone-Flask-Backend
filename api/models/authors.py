from api.extensions import db

class Author(db.Model):
    __tablename__ = 'authors'

    im_id = db.Column(db.Integer, db.ForeignKey('instructionalmaterials.id'), primary_key=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True, nullable=False)

    instructional_material = db.relationship('InstructionalMaterial', backref='authors')
    user = db.relationship('User', backref='authored_materials')

    def __init__(self, im_id, user_id):
        self.im_id = im_id
        self.user_id = user_id

    def __repr__(self):
        return f'<Author im_id={self.im_id}, user_id={self.user_id}>'