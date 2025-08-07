from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.universityim_service import UniversityIMService
from api.schemas.universityims import UniversityIMSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required

universityim_blueprint = Blueprint('universityims', __name__, url_prefix="/universityims")

@universityim_blueprint.route('/', methods=['POST'])
@jwt_required
def create_universityim():
    try:
        data = UniversityIMSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        universityim = UniversityIMService.create_universityim(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IntegrityError as e:
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'University IM created successfully', 'id': universityim.id}), 201

@universityim_blueprint.route('/<int:universityim_id>', methods=['GET'])
@jwt_required
def get_universityim(universityim_id):
    universityim = UniversityIMService.get_universityim_by_id(universityim_id)
    if not universityim:
        return jsonify({'error': 'University IM not found'}), 404

    universityim_schema = UniversityIMSchema()
    return jsonify(universityim_schema.dump(universityim)), 200

@universityim_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_universityims():
    universityims = UniversityIMService.get_all_universityims()
    universityim_schema = UniversityIMSchema(many=True)
    return jsonify(universityim_schema.dump(universityims)), 200

@universityim_blueprint.route('/<int:universityim_id>', methods=['PUT'])
@jwt_required
def update_universityim(universityim_id):
    universityim_schema = UniversityIMSchema(partial=True)

    try:
        data = universityim_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    universityim = UniversityIMService.update_universityim(universityim_id, data)
    if not universityim:
        return jsonify({'error': 'University IM not found'}), 404

    return jsonify({'message': 'University IM updated successfully'}), 200

@universityim_blueprint.route('/<int:universityim_id>', methods=['DELETE'])
@jwt_required
def delete_universityim(universityim_id):
    success = UniversityIMService.delete_universityim(universityim_id)
    if not success:
        return jsonify({'error': 'University IM not found'}), 404

    return jsonify({'message': 'University IM deleted successfully'}), 200