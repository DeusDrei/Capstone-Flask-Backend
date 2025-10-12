from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.universityim_service import UniversityIMService
from api.schemas.universityims import UniversityIMSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required

universityim_blueprint = Blueprint('universityims', __name__, url_prefix="/universityims")

@universityim_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
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
@roles_required('Faculty', 'PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_universityim(universityim_id):
    universityim = UniversityIMService.get_universityim_by_id(universityim_id)
    if not universityim:
        return jsonify({'error': 'University IM not found'}), 404

    universityim_schema = UniversityIMSchema()
    return jsonify(universityim_schema.dump(universityim)), 200

@universityim_blueprint.route('/', methods=['GET'])
@jwt_required
@roles_required('Faculty', 'PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_all_universityims():
    page = request.args.get('page', 1, type=int)
    paginated_universityims = UniversityIMService.get_all_universityims(page=page)
    
    universityim_schema = UniversityIMSchema(many=True)
    return jsonify({
        'universityims': universityim_schema.dump(paginated_universityims.items),
        'total': paginated_universityims.total,
        'pages': paginated_universityims.pages,
        'current_page': paginated_universityims.page,
        'per_page': paginated_universityims.per_page
    }), 200

@universityim_blueprint.route('/<int:universityim_id>', methods=['PUT'])
@jwt_required
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
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
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
def delete_universityim(universityim_id):
    success = UniversityIMService.delete_universityim(universityim_id)
    if not success:
        return jsonify({'error': 'University IM not found'}), 404

    return jsonify({'message': 'University IM deleted successfully'}), 200

@universityim_blueprint.route('/college/<int:college_id>', methods=['GET'])
@jwt_required
@roles_required('Faculty', 'PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_universityims_by_college(college_id):
    page = request.args.get('page', 1, type=int)
    paginated_universityims = UniversityIMService.get_universityims_by_college(college_id, page=page)
    
    universityim_schema = UniversityIMSchema(many=True)
    return jsonify({
        'universityims': universityim_schema.dump(paginated_universityims.items),
        'total': paginated_universityims.total,
        'pages': paginated_universityims.pages,
        'current_page': paginated_universityims.page,
        'per_page': paginated_universityims.per_page
    }), 200

@universityim_blueprint.route('/department/<int:department_id>', methods=['GET'])
@jwt_required
@roles_required('Faculty', 'PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_universityims_by_department(department_id):
    page = request.args.get('page', 1, type=int)
    paginated_universityims = UniversityIMService.get_universityims_by_department(department_id, page=page)
    
    universityim_schema = UniversityIMSchema(many=True)
    return jsonify({
        'universityims': universityim_schema.dump(paginated_universityims.items),
        'total': paginated_universityims.total,
        'pages': paginated_universityims.pages,
        'current_page': paginated_universityims.page,
        'per_page': paginated_universityims.per_page
    }), 200

@universityim_blueprint.route('/subject/<int:subject_id>', methods=['GET'])
@jwt_required
@roles_required('Faculty', 'PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_universityims_by_subject(subject_id):
    page = request.args.get('page', 1, type=int)
    paginated_universityims = UniversityIMService.get_universityims_by_subject(subject_id, page=page)
    
    universityim_schema = UniversityIMSchema(many=True)
    return jsonify({
        'universityims': universityim_schema.dump(paginated_universityims.items),
        'total': paginated_universityims.total,
        'pages': paginated_universityims.pages,
        'current_page': paginated_universityims.page,
        'per_page': paginated_universityims.per_page
    }), 200