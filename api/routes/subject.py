from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.subject_service import SubjectService
from api.schemas.subjects import SubjectSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required

subject_blueprint = Blueprint('subjects', __name__, url_prefix="/subjects")

@subject_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
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
    page = request.args.get('page', 1, type=int)
    paginated_subjects = SubjectService.get_all_subjects(page=page)
    
    subject_schema = SubjectSchema(many=True)
    return jsonify({
        'subjects': subject_schema.dump(paginated_subjects.items),
        'total': paginated_subjects.total,
        'pages': paginated_subjects.pages,
        'current_page': paginated_subjects.page,
        'per_page': paginated_subjects.per_page
    }), 200

@subject_blueprint.route('/all', methods=['GET'])
@jwt_required
def get_all_subjects_no_pagination():
    try:
        subjects = SubjectService.get_all_subjects_no_pagination()
        subject_schema = SubjectSchema(many=True)
        return jsonify(subject_schema.dump(subjects)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@subject_blueprint.route('/<int:subject_id>', methods=['PUT'])
@jwt_required
@roles_required('Technical Admin')
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
@roles_required('Technical Admin')
def delete_subject(subject_id):
    success = SubjectService.soft_delete_subject(subject_id)
    if not success:
        return jsonify({'error': 'Subject not found'}), 404

    return jsonify({'message': 'Subject deleted successfully'}), 200

@subject_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_deleted_subjects():
    page = request.args.get('page', 1, type=int)
    paginated_subjects = SubjectService.get_deleted_subjects(page=page)
    
    subject_schema = SubjectSchema(many=True)
    return jsonify({
        'subjects': subject_schema.dump(paginated_subjects.items),
        'total': paginated_subjects.total,
        'pages': paginated_subjects.pages,
        'current_page': paginated_subjects.page,
        'per_page': paginated_subjects.per_page
    }), 200

@subject_blueprint.route('/<int:subject_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_subject(subject_id):
    success = SubjectService.restore_subject(subject_id)
    if not success:
        return jsonify({'error': 'Subject not found or already active'}), 404
    return jsonify({'message': 'Subject restored successfully'}), 200


@subject_blueprint.route('/college/<int:college_id>', methods=['GET'])
@jwt_required
def get_subjects_by_college(college_id):
    try:
        subjects = SubjectService.get_subjects_by_college_id(college_id)
        subject_schema = SubjectSchema(many=True)
        return jsonify(subject_schema.dump(subjects)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@subject_blueprint.route('/instructionalmaterial/<int:im_id>', methods=['GET'])
@jwt_required
def get_subject_by_im(im_id):
    """Return the subject linked to an Instructional Material id.

    Resolution path:
    - IM -> university_im.subject_id OR service_im.subject_id
    - Returns 404 if IM or subject not found / subject soft-deleted.
    """
    try:
        subj = SubjectService.get_subject_by_im_id(im_id)
        if not subj:
            return jsonify({'error': 'Subject not found for IM'}), 404
        subject_schema = SubjectSchema()
        return jsonify(subject_schema.dump(subj)), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    