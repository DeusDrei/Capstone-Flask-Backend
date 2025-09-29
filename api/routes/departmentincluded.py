from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.departmentincluded_service import DepartmentIncludedService
from api.schemas.departmentsincluded import DepartmentIncludedSchema
from api.middleware import jwt_required, roles_required
from sqlalchemy.exc import IntegrityError

departmentincluded_blueprint = Blueprint('department_included', __name__, url_prefix="/department-included")

@departmentincluded_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def create_association():
    schema = DepartmentIncludedSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        association = DepartmentIncludedService.create_association(
            department_id=data['department_id'],
            user_id=data['user_id']
        )
        return jsonify({
            'message': 'Association created successfully',
            'department_id': association.department_id,
            'user_id': association.user_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@departmentincluded_blueprint.route('/department/<int:department_id>/user/<int:user_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_association(department_id, user_id):
    association = DepartmentIncludedService.get_association(department_id, user_id)
    if not association:
        return jsonify({'error': 'Association not found'}), 404

    schema = DepartmentIncludedSchema()
    return jsonify(schema.dump(association)), 200

@departmentincluded_blueprint.route('/user/<int:user_id>', methods=['GET'])
@jwt_required
def get_departments_for_user(user_id):
    associations = DepartmentIncludedService.get_departments_for_user(user_id)
    schema = DepartmentIncludedSchema(many=True)
    return jsonify(schema.dump(associations)), 200

@departmentincluded_blueprint.route('/department/<int:department_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_users_for_department(department_id):
    associations = DepartmentIncludedService.get_users_for_department(department_id)
    schema = DepartmentIncludedSchema(many=True)
    return jsonify(schema.dump(associations)), 200

@departmentincluded_blueprint.route('/department/<int:department_id>/user/<int:user_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_association(department_id, user_id):
    success = DepartmentIncludedService.delete_association(department_id, user_id)
    if not success:
        return jsonify({'error': 'Association not found'}), 404
    return jsonify({'message': 'Association deleted successfully'}), 200