import json
from datetime import date, datetime, time
from sqlalchemy import or_, cast, String
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
    def get_filter_metadata():
        """Return distinct filter option values used by activity logs."""
        actions = [
            row[0]
            for row in db.session.query(ActivityLog.action)
            .distinct()
            .order_by(ActivityLog.action.asc())
            .all()
            if row[0]
        ]
        table_names = [
            row[0]
            for row in db.session.query(ActivityLog.table_name)
            .distinct()
            .order_by(ActivityLog.table_name.asc())
            .all()
            if row[0]
        ]

        return {
            'actions': actions,
            'table_names': table_names,
        }

    @staticmethod
    def _build_filtered_query(
        user_id=None,
        table_name=None,
        action=None,
        search=None,
        start_date=None,
        end_date=None,
    ):
        """Build the base activity-log query with optional filters."""
        query = ActivityLog.query

        if user_id is not None:
            query = query.filter(ActivityLog.user_id == user_id)

        if table_name:
            table_pattern = f"%{table_name.strip()}%"
            query = query.filter(ActivityLog.table_name.ilike(table_pattern))

        if action:
            action_pattern = f"%{action.strip()}%"
            query = query.filter(ActivityLog.action.ilike(action_pattern))

        if search:
            q = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    ActivityLog.description.ilike(q),
                    ActivityLog.table_name.ilike(q),
                    ActivityLog.action.ilike(q),
                    cast(ActivityLog.user_id, String).ilike(q),
                    cast(ActivityLog.record_id, String).ilike(q),
                )
            )

        if isinstance(start_date, date):
            start_dt = datetime.combine(start_date, time.min)
            query = query.filter(ActivityLog.created_at >= start_dt)

        if isinstance(end_date, date):
            end_dt = datetime.combine(end_date, time.max)
            query = query.filter(ActivityLog.created_at <= end_dt)

        return query

    @staticmethod
    def get_all_logs(
        page=1,
        per_page=10,
        user_id=None,
        table_name=None,
        action=None,
        search=None,
        start_date=None,
        end_date=None,
    ):
        """Get activity logs with pagination and optional filters."""
        per_page_safe = max(1, min(int(per_page or 10), 100))
        query = ActivityLogService._build_filtered_query(
            user_id=user_id,
            table_name=table_name,
            action=action,
            search=search,
            start_date=start_date,
            end_date=end_date,
        )
        return query.order_by(ActivityLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page_safe,
            error_out=False,
        )

    @staticmethod
    def get_log_by_id(log_id):
        """Get activity log by ID"""
        return db.session.get(ActivityLog, log_id)

    @staticmethod
    def get_logs_by_user(user_id, page=1, per_page=10):
        """Get activity logs for specific user"""
        per_page_safe = max(1, min(int(per_page or 10), 100))
        return ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page_safe,
            error_out=False
        )

    @staticmethod
    def get_logs_by_table(table_name, page=1, per_page=10):
        """Get activity logs for specific table"""
        per_page_safe = max(1, min(int(per_page or 10), 100))
        return ActivityLog.query.filter_by(table_name=table_name).order_by(ActivityLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page_safe,
            error_out=False
        )