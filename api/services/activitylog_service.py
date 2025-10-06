import json
from api.extensions import db
from api.models.activitylog import ActivityLog

class ActivityLogService:
    @staticmethod
    def log_activity(user_id, action, table_name, description, record_id=None, old_values=None, new_values=None):
        """Log an activity to the database"""
        try:
            # Convert dict values to JSON strings if provided
            old_json = json.dumps(old_values) if old_values else None
            new_json = json.dumps(new_values) if new_values else None
            
            log = ActivityLog(
                user_id=user_id,
                action=action,
                table_name=table_name,
                description=description,
                record_id=record_id,
                old_values=old_json,
                new_values=new_json
            )
            
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            print(f"Failed to log activity: {str(e)}")
            return None

    @staticmethod
    def get_all_logs(page=1):
        """Get all activity logs with pagination"""
        per_page = 10
        return ActivityLog.query.order_by(ActivityLog.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_log_by_id(log_id):
        """Get activity log by ID"""
        return db.session.get(ActivityLog, log_id)

    @staticmethod
    def get_logs_by_user(user_id, page=1):
        """Get activity logs for specific user"""
        per_page = 10
        return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_logs_by_table(table_name, page=1):
        """Get activity logs for specific table"""
        per_page = 10
        return ActivityLog.query.filter_by(table_name=table_name).order_by(ActivityLog.created_at.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )