from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.author_service import AuthorService
from api.schemas.authors import AuthorSchema
from api.middleware import jwt_required, roles_required
from sqlalchemy.exc import IntegrityError

author_blueprint = Blueprint('authors', __name__, url_prefix="/authors")

@author_blueprint.route('/', methods=['POST'])
@jwt_required
def create_author():
    schema = AuthorSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    try:
        author = AuthorService.create_author(
            im_id=data['im_id'],
            user_id=data['user_id']
        )
        return jsonify({
            'message': 'Author association created successfully',
            'im_id': author.im_id,
            'user_id': author.user_id
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@author_blueprint.route('/im/<int:im_id>/user/<int:user_id>', methods=['GET'])
@jwt_required
def get_author(im_id, user_id):
    author = AuthorService.get_author(im_id, user_id)
    if not author:
        return jsonify({'error': 'Author association not found'}), 404

    schema = AuthorSchema()
    return jsonify(schema.dump(author)), 200

@author_blueprint.route('/user/<int:user_id>', methods=['GET'])
@jwt_required
def get_instructional_materials_for_user(user_id):
    authors = AuthorService.get_instructional_materials_for_user(user_id)
    schema = AuthorSchema(many=True)
    return jsonify(schema.dump(authors)), 200

@author_blueprint.route('/im/<int:im_id>', methods=['GET'])
@jwt_required
def get_authors_for_instructional_material(im_id):
    authors = AuthorService.get_authors_for_instructional_material(im_id)
    schema = AuthorSchema(many=True)
    return jsonify(schema.dump(authors)), 200

@author_blueprint.route('/im/<int:im_id>/user/<int:user_id>', methods=['DELETE'])
@jwt_required
def delete_author(im_id, user_id):
    success = AuthorService.delete_author(im_id, user_id)
    if not success:
        return jsonify({'error': 'Author association not found'}), 404
    return jsonify({'message': 'Author association deleted successfully'}), 200