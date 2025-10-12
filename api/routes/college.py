from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.college_service import CollegeService
from api.schemas.colleges import CollegeSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required

college_blueprint = Blueprint('colleges', __name__, url_prefix="/colleges")

@college_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin', 'PIMEC', 'UTLDO Admin')
def create_college():
    try:
        data = CollegeSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        college = CollegeService.create_college(data)
    except IntegrityError as e:
        if "colleges.abbreviation" in str(e.orig):
            return jsonify({"message": "College with this abbreviation already exists"}), 409
        if "colleges.name" in str(e.orig):
            return jsonify({"message": "College with this name already exists"}), 409
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': f'College {college.name} created successfully'}), 201

@college_blueprint.route('/<int:college_id>', methods=['GET'])
@jwt_required
def get_college(college_id):
    college = CollegeService.get_college_by_id(college_id)
    if not college or college.is_deleted:
        return jsonify({'error': 'College not found'}), 404

    college_schema = CollegeSchema()
    return jsonify(college_schema.dump(college)), 200

@college_blueprint.route('/all', methods=['GET'])
@jwt_required
def get_all_colleges():
    colleges = CollegeService.get_all_colleges()
    college_schema = CollegeSchema(many=True)
    return jsonify({'colleges': college_schema.dump(colleges)}), 200

@college_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_colleges_paginated():
    page = request.args.get('page', 1, type=int)
    paginated_colleges = CollegeService.get_all_colleges_paginated(page=page)
    college_schema = CollegeSchema(many=True)
    return jsonify({
        'colleges': college_schema.dump(paginated_colleges.items),
        'total': paginated_colleges.total,
        'pages': paginated_colleges.pages,
        'current_page': paginated_colleges.page,
        'per_page': paginated_colleges.per_page
    }), 200

@college_blueprint.route('/<int:college_id>', methods=['PUT'])
@jwt_required
@roles_required('Technical Admin')
def update_college(college_id):
    college_schema = CollegeSchema(partial=True)

    try:
        data = college_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    college = CollegeService.update_college(college_id, data)
    if not college or college.is_deleted:
        return jsonify({'error': 'College not found'}), 404

    return jsonify({'message': f'College {college.name} updated successfully'}), 200

@college_blueprint.route('/<int:college_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_college(college_id):
    success = CollegeService.soft_delete_college(college_id)
    if not success:
        return jsonify({'error': 'College not found'}), 404

    return jsonify({'message': 'College deleted successfully'}), 200

@college_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_deleted_colleges():
    page = request.args.get('page', 1, type=int)
    paginated_colleges = CollegeService.get_deleted_colleges(page=page)
    
    college_schema = CollegeSchema(many=True)
    return jsonify({
        'colleges': college_schema.dump(paginated_colleges.items),
        'total': paginated_colleges.total,
        'pages': paginated_colleges.pages,
        'current_page': paginated_colleges.page,
        'per_page': paginated_colleges.per_page
    }), 200

@college_blueprint.route('/<int:college_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_college(college_id):
    success = CollegeService.restore_college(college_id)
    if not success:
        return jsonify({'error': 'College not found or already active'}), 404
    return jsonify({'message': 'College restored successfully'}), 200