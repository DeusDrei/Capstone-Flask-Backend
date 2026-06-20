from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.activitylog_service import ActivityLogService
from api.schemas.activitylog import ActivityLogSchema
from api.middleware import jwt_required, roles_required
from datetime import datetime

activitylog_blueprint = Blueprint('activity_log', __name__, url_prefix="/activity-logs")


def _parse_date(date_str, field_name):
    if not date_str:
        return None, None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date(), None
    except ValueError:
        return None, f"{field_name} must be in YYYY-MM-DD format"

@activitylog_blueprint.route('/', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_all_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    user_id = request.args.get('user_id', type=int)
    table_name = request.args.get('table_name', type=str)
    action = request.args.get('action', type=str)
    search = request.args.get('q', type=str)

    start_date, start_error = _parse_date(request.args.get('start_date'), 'start_date')
    if start_error:
        return jsonify({'error': start_error}), 400

    end_date, end_error = _parse_date(request.args.get('end_date'), 'end_date')
    if end_error:
        return jsonify({'error': end_error}), 400

    paginated_logs = ActivityLogService.get_all_logs(
        page=page,
        per_page=per_page,
        user_id=user_id,
        table_name=table_name,
        action=action,
        search=search,
        start_date=start_date,
        end_date=end_date,
    )
    log_schema = ActivityLogSchema(many=True)
    return jsonify({
        'logs': log_schema.dump(paginated_logs.items),
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'per_page': paginated_logs.per_page
    }), 200


@activitylog_blueprint.route('/meta', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_log_filter_metadata():
    metadata = ActivityLogService.get_filter_metadata()
    return jsonify(metadata), 200

@activitylog_blueprint.route('/<int:log_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_log(log_id):
    log = ActivityLogService.get_log_by_id(log_id)
    if not log:
        return jsonify({'error': 'Activity log not found'}), 404

    log_schema = ActivityLogSchema()
    return jsonify(log_schema.dump(log)), 200

@activitylog_blueprint.route('/user/<int:user_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_logs_by_user(user_id):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    paginated_logs = ActivityLogService.get_logs_by_user(user_id, page=page, per_page=per_page)
    
    log_schema = ActivityLogSchema(many=True)
    return jsonify({
        'logs': log_schema.dump(paginated_logs.items),
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'per_page': paginated_logs.per_page
    }), 200

@activitylog_blueprint.route('/table/<string:table_name>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_logs_by_table(table_name):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    paginated_logs = ActivityLogService.get_logs_by_table(table_name, page=page, per_page=per_page)
    
    log_schema = ActivityLogSchema(many=True)
    return jsonify({
        'logs': log_schema.dump(paginated_logs.items),
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'per_page': paginated_logs.per_page
    }), 200