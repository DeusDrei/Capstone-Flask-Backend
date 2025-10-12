from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.subject_department_service import SubjectDepartmentService
from api.schemas.subject_departments import SubjectDepartmentSchema
from api.middleware import jwt_required, roles_required

subject_department_blueprint = Blueprint('subject_departments', __name__, url_prefix="/subject-departments")
@subject_department_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def create_subject_department():
    schema = SubjectDepartmentSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        assoc = SubjectDepartmentService.create(
            subject_id=data['subject_id'],
            department_id=data['department_id']
        )
        return jsonify({
            'message': 'Subject-Department association created successfully',
            'subject_id': assoc.subject_id,
            'department_id': assoc.department_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@subject_department_blueprint.route('/subject/<int:subject_id>/department/<int:department_id>', methods=['GET'])
@jwt_required

def get_subject_department(subject_id, department_id):
    assoc = SubjectDepartmentService.get(subject_id, department_id)
    if not assoc:
        return jsonify({'error': 'Association not found'}), 404
    schema = SubjectDepartmentSchema()
    return jsonify(schema.dump(assoc)), 200

@subject_department_blueprint.route('/subject/<int:subject_id>', methods=['GET'])
@jwt_required

def get_departments_for_subject(subject_id):
    assocs = SubjectDepartmentService.get_departments_for_subject(subject_id)
    schema = SubjectDepartmentSchema(many=True)
    return jsonify(schema.dump(assocs)), 200

@subject_department_blueprint.route('/department/<int:department_id>', methods=['GET'])
@jwt_required

def get_subjects_for_department(department_id):
    assocs = SubjectDepartmentService.get_subjects_for_department(department_id)
    schema = SubjectDepartmentSchema(many=True)
    return jsonify(schema.dump(assocs)), 200

@subject_department_blueprint.route('/subject/<int:subject_id>/department/<int:department_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_subject_department(subject_id, department_id):
    success = SubjectDepartmentService.delete(subject_id, department_id)
    if not success:
        return jsonify({'error': 'Association not found'}), 404
    return jsonify({'message': 'Association deleted successfully'}), 200
