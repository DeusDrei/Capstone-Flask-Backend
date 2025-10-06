from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.activitylog_service import ActivityLogService
from api.schemas.activitylog import ActivityLogSchema
from api.middleware import jwt_required, roles_required

activitylog_blueprint = Blueprint('activity_log', __name__, url_prefix="/activity-logs")

@activitylog_blueprint.route('/', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_all_logs():
    page = request.args.get('page', 1, type=int)
    paginated_logs = ActivityLogService.get_all_logs(page=page)
    
    log_schema = ActivityLogSchema(many=True)
    return jsonify({
        'logs': log_schema.dump(paginated_logs.items),
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'per_page': paginated_logs.per_page
    }), 200

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
    paginated_logs = ActivityLogService.get_logs_by_user(user_id, page=page)
    
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
    paginated_logs = ActivityLogService.get_logs_by_table(table_name, page=page)
    
    log_schema = ActivityLogSchema(many=True)
    return jsonify({
        'logs': log_schema.dump(paginated_logs.items),
        'total': paginated_logs.total,
        'pages': paginated_logs.pages,
        'current_page': paginated_logs.page,
        'per_page': paginated_logs.per_page
    }), 200