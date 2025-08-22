from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.department_service import DepartmentService
from api.schemas.departments import DepartmentSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required

department_blueprint = Blueprint('departments', __name__, url_prefix="/departments")

@department_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def create_department():
    try:
        data = DepartmentSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        department = DepartmentService.create_department(data)
    except IntegrityError as e:
        if "departments.abbreviation" in str(e.orig):
            return jsonify({"message": "Department with this abbreviation already exists"}), 409
        if "departments.name" in str(e.orig):
            return jsonify({"message": "Department with this name already exists"}), 409
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': f'Department {department.name} created successfully'}), 201

@department_blueprint.route('/<int:department_id>', methods=['GET'])
@jwt_required
def get_department(department_id):
    department = DepartmentService.get_department_by_id(department_id)
    if not department or department.is_deleted:
        return jsonify({'error': 'Department not found'}), 404

    department_schema = DepartmentSchema()
    return jsonify(department_schema.dump(department)), 200

@department_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_departments():
    try:
        departments = DepartmentService.get_all_departments()
        department_schema = DepartmentSchema(many=True)
        return jsonify(department_schema.dump(departments)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@department_blueprint.route('/college/<int:college_id>', methods=['GET'])
@jwt_required
def get_departments_by_college_id(college_id):
    try:
        departments = DepartmentService.get_departments_by_college_id(college_id)
        department_schema = DepartmentSchema(many=True)
        return jsonify(department_schema.dump(departments)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@department_blueprint.route('/<int:department_id>', methods=['PUT'])
@jwt_required
@roles_required('Technical Admin')
def update_department(department_id):
    department_schema = DepartmentSchema(partial=True)

    try:
        data = department_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    department = DepartmentService.update_department(department_id, data)
    if not department or department.is_deleted:
        return jsonify({'error': 'Department not found'}), 404

    return jsonify({'message': f'Department {department.name} updated successfully'}), 200

@department_blueprint.route('/<int:department_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_department(department_id):
    success = DepartmentService.soft_delete_department(department_id)
    if not success:
        return jsonify({'error': 'Department not found'}), 404

    return jsonify({'message': 'Department deleted successfully'}), 200

@department_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_deleted_departments():
    page = request.args.get('page', 1, type=int)
    paginated_departments = DepartmentService.get_deleted_departments(page=page)
    department_schema = DepartmentSchema(many=True)
    return jsonify({
        'departments': department_schema.dump(paginated_departments.items),
        'total': paginated_departments.total,
        'pages': paginated_departments.pages,
        'current_page': paginated_departments.page,
        'per_page': paginated_departments.per_page
    }), 200

@department_blueprint.route('/<int:department_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_department(department_id):
    success = DepartmentService.restore_department(department_id)
    if not success:
        return jsonify({'error': 'Department not found or already active'}), 404
    return jsonify({'message': 'Department restored successfully'}), 200