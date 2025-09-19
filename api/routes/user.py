from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.user_service import UserService
from api.schemas.users import UserSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required

user_blueprint = Blueprint('users', __name__, url_prefix="/users")

@user_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def create_user():
    try:
        data = UserSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        user = UserService.create_user(data)
    except IntegrityError as e:
        if "users.email" in str(e.orig):
            return jsonify({"message": "User with this email already exists"}), 409
        if "users.staff_id" in str(e.orig):
            return jsonify({"message": "User with this faculty ID already exists"}), 409
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': f'User {user.first_name} {user.last_name} created successfully',
        'id': user.id,
    }), 201

@user_blueprint.route('/<int:user_id>', methods=['GET'])
@jwt_required
def get_user(user_id):
    user = UserService.get_user_by_id(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404

    user_schema = UserSchema()
    return jsonify(user_schema.dump(user)), 200

@user_blueprint.route('/', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_all_users():
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort_by', type=str)
    sort_dir = request.args.get('sort_dir', 'asc', type=str)
    paginated_users = UserService.get_all_users(page=page, sort_by=sort_by, sort_dir=sort_dir)

    user_schema = UserSchema(many=True)
    return jsonify({
        'users': user_schema.dump(paginated_users.items),
        'total': paginated_users.total,
        'pages': paginated_users.pages,
        'current_page': paginated_users.page,
    'per_page': paginated_users.per_page,
    'has_next': paginated_users.has_next,
    'has_prev': paginated_users.has_prev,
        'sort_by': sort_by,
        'sort_dir': sort_dir
    }), 200

@user_blueprint.route('/all', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_all_users_no_pagination():
    sort_by = request.args.get('sort_by', type=str)
    sort_dir = request.args.get('sort_dir', 'asc', type=str)
    users = UserService.get_all_users_no_pagination(sort_by=sort_by, sort_dir=sort_dir)
    user_schema = UserSchema(many=True)
    return jsonify(user_schema.dump(users)), 200

@user_blueprint.route('/<int:user_id>', methods=['PUT'])
@jwt_required
def update_user(user_id):
    user_schema = UserSchema(partial=True)

    try:
        data = user_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    user = UserService.update_user(user_id, data)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'message': f'User {user.first_name} {user.last_name} updated successfully'}), 200

@user_blueprint.route('/<int:user_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_user(user_id):
    success = UserService.soft_delete_user(user_id)
    if not success:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({'message': 'User deleted successfully'}), 200

@user_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_deleted_users():
    page = request.args.get('page', 1, type=int)
    paginated_users = UserService.get_deleted_users(page=page)
    
    user_schema = UserSchema(many=True)
    return jsonify({
        'users': user_schema.dump(paginated_users.items),
        'total': paginated_users.total,
        'pages': paginated_users.pages,
        'current_page': paginated_users.page,
        'per_page': paginated_users.per_page
    }), 200

@user_blueprint.route('/<int:user_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_user(user_id):
    success = UserService.restore_user(user_id)
    if not success:
        return jsonify({'error': 'User not found or already active'}), 404
    return jsonify({'message': 'User restored successfully'}), 200