from api.extensions import db
from datetime import datetime, UTC

class ActivityLog(db.Model):
    __tablename__ = 'activitylog'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    table_name = db.Column(db.String(100), nullable=False)
    record_id = db.Column(db.Integer, nullable=True)
    old_values = db.Column(db.Text, nullable=True)
    new_values = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC), nullable=False)
    
    user = db.relationship('User', backref='activity_logs')

    def __init__(self, user_id, action, table_name, description, record_id=None, old_values=None, new_values=None):
        self.user_id = user_id
        self.action = action
        self.table_name = table_name
        self.record_id = record_id
        self.old_values = old_values
        self.new_values = new_values
        self.description = description

    def __repr__(self):
        return f'<ActivityLog id={self.id}, user_id={self.user_id}, action={self.action}>'