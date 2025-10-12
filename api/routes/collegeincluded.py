from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.collegeincluded_service import CollegeIncludedService
from api.schemas.collegesincluded import CollegeIncludedSchema
from api.middleware import jwt_required, roles_required
from sqlalchemy.exc import IntegrityError

collegeincluded_blueprint = Blueprint('college_included', __name__, url_prefix="/college-included")

@collegeincluded_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def create_association():
    schema = CollegeIncludedSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        association = CollegeIncludedService.create_association(
            college_id=data['college_id'],
            user_id=data['user_id']
        )
        return jsonify({
            'message': 'Association created successfully',
            'college_id': association.college_id,
            'user_id': association.user_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@collegeincluded_blueprint.route('/college/<int:college_id>/user/<int:user_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_association(college_id, user_id):
    association = CollegeIncludedService.get_association(college_id, user_id)
    if not association:
        return jsonify({'error': 'Association not found'}), 404

    schema = CollegeIncludedSchema()
    return jsonify(schema.dump(association)), 200

@collegeincluded_blueprint.route('/user/<int:user_id>', methods=['GET'])
@jwt_required
def get_colleges_for_user(user_id):
    associations = CollegeIncludedService.get_colleges_for_user(user_id)
    schema = CollegeIncludedSchema(many=True)
    return jsonify(schema.dump(associations)), 200

@collegeincluded_blueprint.route('/college/<int:college_id>', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'PIMEC', 'UTLDO Admin')
def get_users_for_college(college_id):
    """Get users associated with a college - needed for author selection"""
    associations = CollegeIncludedService.get_users_for_college(college_id)
    schema = CollegeIncludedSchema(many=True)
    return jsonify(schema.dump(associations)), 200

@collegeincluded_blueprint.route('/college/<int:college_id>/user/<int:user_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_association(college_id, user_id):
    success = CollegeIncludedService.delete_association(college_id, user_id)
    if not success:
        return jsonify({'error': 'Association not found'}), 404
    return jsonify({'message': 'Association deleted successfully'}), 200