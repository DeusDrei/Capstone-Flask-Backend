from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.subject_service import SubjectService
from api.schemas.subjects import SubjectSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required

subject_blueprint = Blueprint('subjects', __name__, url_prefix="/subjects")

@subject_blueprint.route('/', methods=['POST'])
@jwt_required
def create_subject():
    try:
        data = SubjectSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        subject = SubjectService.create_subject(data)
    except IntegrityError as e:
        if "subjects.code" in str(e.orig):
            return jsonify({"message": "Subject with this code already exists"}), 409
        if "subjects.name" in str(e.orig):
            return jsonify({"message": "Subject with this name already exists"}), 409
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': f'Subject {subject.name} created successfully'}), 201

@subject_blueprint.route('/<int:subject_id>', methods=['GET'])
@jwt_required
def get_subject(subject_id):
    subject = SubjectService.get_subject_by_id(subject_id)
    if not subject or subject.is_deleted:
        return jsonify({'error': 'Subject not found'}), 404

    subject_schema = SubjectSchema()
    return jsonify(subject_schema.dump(subject)), 200

@subject_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_subjects():
    subjects = SubjectService.get_all_subjects()
    subject_schema = SubjectSchema(many=True)
    return jsonify(subject_schema.dump(subjects)), 200

@subject_blueprint.route('/<int:subject_id>', methods=['PUT'])
@jwt_required
def update_subject(subject_id):
    subject_schema = SubjectSchema(partial=True)

    try:
        data = subject_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    subject = SubjectService.update_subject(subject_id, data)
    if not subject or subject.is_deleted:
        return jsonify({'error': 'Subject not found'}), 404

    return jsonify({'message': f'Subject {subject.name} updated successfully'}), 200

@subject_blueprint.route('/<int:subject_id>', methods=['DELETE'])
@jwt_required
def delete_subject(subject_id):
    success = SubjectService.soft_delete_subject(subject_id)
    if not success:
        return jsonify({'error': 'Subject not found'}), 404

    return jsonify({'message': 'Subject deleted successfully'}), 200

@subject_blueprint.route('/deleted', methods=['GET'])
@jwt_required
def get_deleted_subjects():
    subjects = SubjectService.get_deleted_subjects()
    subject_schema = SubjectSchema(many=True)
    return jsonify(subject_schema.dump(subjects)), 200

@subject_blueprint.route('/<int:subject_id>/restore', methods=['POST'])
@jwt_required
def restore_subject(subject_id):
    success = SubjectService.restore_subject(subject_id)
    if not success:
        return jsonify({'error': 'Subject not found or already active'}), 404
    return jsonify({'message': 'Subject restored successfully'}), 200