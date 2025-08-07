from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.serviceim_service import ServiceIMService
from api.schemas.serviceims import ServiceIMSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required

serviceim_blueprint = Blueprint('serviceims', __name__, url_prefix="/serviceims")

@serviceim_blueprint.route('/', methods=['POST'])
@jwt_required
def create_serviceim():
    try:
        data = ServiceIMSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        serviceim = ServiceIMService.create_serviceim(data)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except IntegrityError as e:
        return jsonify({'error': 'Database integrity error'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({
        'message': 'Service IM created successfully',
        'id': serviceim.id
    }), 201

@serviceim_blueprint.route('/<int:serviceim_id>', methods=['GET'])
@jwt_required
def get_serviceim(serviceim_id):
    serviceim = ServiceIMService.get_serviceim_by_id(serviceim_id)
    if not serviceim:
        return jsonify({'error': 'Service IM not found'}), 404

    serviceim_schema = ServiceIMSchema()
    return jsonify(serviceim_schema.dump(serviceim)), 200

@serviceim_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_serviceims():
    serviceims = ServiceIMService.get_all_serviceims()
    serviceim_schema = ServiceIMSchema(many=True)
    return jsonify(serviceim_schema.dump(serviceims)), 200

@serviceim_blueprint.route('/<int:serviceim_id>', methods=['PUT'])
@jwt_required
def update_serviceim(serviceim_id):
    serviceim_schema = ServiceIMSchema(partial=True)

    try:
        data = serviceim_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        serviceim = ServiceIMService.update_serviceim(serviceim_id, data)
        if not serviceim:
            return jsonify({'error': 'Service IM not found'}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Service IM updated successfully'}), 200

@serviceim_blueprint.route('/<int:serviceim_id>', methods=['DELETE'])
@jwt_required
def delete_serviceim(serviceim_id):
    try:
        success = ServiceIMService.delete_serviceim(serviceim_id)
        if not success:
            return jsonify({'error': 'Service IM not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': 'Service IM deleted successfully'}), 200