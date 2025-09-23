from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.imerpimec_service import IMERPIMECService
from api.schemas.imerpimec import IMERPIMECSchema
from api.middleware import jwt_required, roles_required
from sqlalchemy.exc import IntegrityError

imerpimec_blueprint = Blueprint('imerpimec', __name__, url_prefix="/imerpimec")

@imerpimec_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('PIMEC', 'Technical Admin')
def create_imerpimec():
    try:
        data = IMERPIMECSchema().load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        imerpimec = IMERPIMECService.create_imerpimec(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'message': f'IMERPIMEC {imerpimec.id} created successfully'}), 201

@imerpimec_blueprint.route('/<int:imerpimec_id>', methods=['GET'])
@jwt_required
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_imerpimec(imerpimec_id):
    imerpimec = IMERPIMECService.get_imerpimec_by_id(imerpimec_id)
    if not imerpimec or imerpimec.is_deleted:
        return jsonify({'error': 'IMERPIMEC not found'}), 404

    imerpimec_schema = IMERPIMECSchema()
    return jsonify(imerpimec_schema.dump(imerpimec)), 200

@imerpimec_blueprint.route('/', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_all_imerpimecs():
    page = request.args.get('page', 1, type=int)
    paginated_imerpimecs = IMERPIMECService.get_all_imerpimecs(page=page)
    
    imerpimec_schema = IMERPIMECSchema(many=True)
    return jsonify({
        'imerpimecs': imerpimec_schema.dump(paginated_imerpimecs.items),
        'total': paginated_imerpimecs.total,
        'pages': paginated_imerpimecs.pages,
        'current_page': paginated_imerpimecs.page,
        'per_page': paginated_imerpimecs.per_page
    }), 200

@imerpimec_blueprint.route('/<int:imerpimec_id>', methods=['PUT'])
@jwt_required
@roles_required('PIMEC', 'Technical Admin')
def update_imerpimec(imerpimec_id):
    imerpimec_schema = IMERPIMECSchema(partial=True)

    try:
        data = imerpimec_schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    imerpimec = IMERPIMECService.update_imerpimec(imerpimec_id, data)
    if not imerpimec or imerpimec.is_deleted:
        return jsonify({'error': 'IMERPIMEC not found'}), 404

    return jsonify({'message': f'IMERPIMEC {imerpimec.id} updated successfully'}), 200

@imerpimec_blueprint.route('/<int:imerpimec_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_imerpimec(imerpimec_id):
    success = IMERPIMECService.soft_delete_imerpimec(imerpimec_id)
    if not success:
        return jsonify({'error': 'IMERPIMEC not found'}), 404

    return jsonify({'message': 'IMERPIMEC deleted successfully'}), 200

@imerpimec_blueprint.route('/<int:imerpimec_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_imerpimec(imerpimec_id):
    success = IMERPIMECService.restore_imerpimec(imerpimec_id)
    if not success:
        return jsonify({'error': 'IMERPIMEC not found or already active'}), 404
    return jsonify({'message': 'IMERPIMEC restored successfully'}), 200