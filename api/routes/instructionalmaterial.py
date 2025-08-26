from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.instructionalmaterial_service import InstructionalMaterialService
from api.schemas.instructionalmaterials import InstructionalMaterialSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required
import os

im_blueprint = Blueprint('instructionalmaterials', __name__, url_prefix="/instructionalmaterials")

@im_blueprint.route('/upload', methods=['POST'])
@jwt_required
def upload_pdf():
    """
    Separate endpoint for PDF upload and processing
    Returns S3 link and analysis notes
    """
    try:
        # Check if PDF file is provided
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400
        
        pdf_file = request.files['pdf_file']
        
        # Process the PDF file (upload to S3 and analyze)
        s3_link, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)
        
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify({
            's3_link': s3_link,
            'notes': notes,
            'filename': pdf_file.filename
        }), 200
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/', methods=['POST'])
@jwt_required
def create_instructional_material():
    """
    Create instructional material using pre-uploaded PDF data
    Expects s3_link and notes in the request body
    """
    try:
        # Validate the data
        data = InstructionalMaterialSchema().load(request.json)
        
        # Check if required PDF data is provided
        if 's3_link' not in request.json:
            return jsonify({'error': 's3_link is required'}), 400
        
        s3_link = request.json['s3_link']
        notes = request.json.get('notes', '')
        
        # Create the instructional material
        im = InstructionalMaterialService.create_instructional_material(data, s3_link, notes)
        
        return jsonify({
            'message': f'Instructional Material {im.version} created successfully',
            'id': im.id,
            'data': InstructionalMaterialSchema().dump(im)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['PUT'])
@jwt_required
def update_instructional_material(im_id):
    """
    Update instructional material - can accept new PDF data or just metadata
    """
    try:
        # Check if this is a file upload or JSON update
        if request.files and 'pdf_file' in request.files:
            # Handle PDF file upload and processing
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '' and pdf_file.filename.lower().endswith('.pdf'):
                s3_link, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)
                
                # Get other form data
                form_data = request.form.to_dict()
                validated_data = InstructionalMaterialSchema(partial=True).load(form_data)
                
                # Update with new PDF data
                im = InstructionalMaterialService.update_instructional_material(
                    im_id, validated_data, s3_link, notes
                )
                
                # Clean up temporary file
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            else:
                return jsonify({'error': 'Valid PDF file is required'}), 400
        else:
            # Handle JSON-only update
            data = InstructionalMaterialSchema(partial=True).load(request.json)
            im = InstructionalMaterialService.update_instructional_material(im_id, data)
        
        if not im or im.is_deleted:
            return jsonify({'error': 'Instructional Material not found'}), 404
        
        return jsonify({
            'message': f'Instructional Material {im.version} updated successfully',
            'data': InstructionalMaterialSchema().dump(im)
        }), 200
        
    except Exception as e:
        # Clean up temporary file if it exists
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['GET'])
@jwt_required
def get_instructional_material(im_id):
    im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
    if not im or im.is_deleted:
        return jsonify({'error': 'Instructional Material not found'}), 404

    im_schema = InstructionalMaterialSchema()
    return jsonify(im_schema.dump(im)), 200

@im_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_instructional_materials():
    page = request.args.get('page', 1, type=int)
    paginated_ims = InstructionalMaterialService.get_all_instructional_materials(page=page)
    
    im_schema = InstructionalMaterialSchema(many=True)
    return jsonify({
        'instructional_materials': im_schema.dump(paginated_ims.items),
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_page': paginated_ims.per_page
    }), 200

@im_blueprint.route('/<int:im_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin')
def delete_instructional_material(im_id):
    success = InstructionalMaterialService.soft_delete_instructional_material(im_id)
    if not success:
        return jsonify({'error': 'Instructional Material not found'}), 404

    return jsonify({'message': 'Instructional Material deleted successfully'}), 200

@im_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin')
def get_deleted_instructional_materials():
    page = request.args.get('page', 1, type=int)
    paginated_ims = InstructionalMaterialService.get_deleted_instructional_materials(page=page)
    
    im_schema = InstructionalMaterialSchema(many=True)
    return jsonify({
        'instructional_materials': im_schema.dump(paginated_ims.items),
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_page': paginated_ims.per_page
    }), 200

@im_blueprint.route('/<int:im_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin')
def restore_instructional_material(im_id):
    success = InstructionalMaterialService.restore_instructional_material(im_id)
    if not success:
        return jsonify({'error': 'Instructional Material not found or already active'}), 404
    return jsonify({'message': 'Instructional Material restored successfully'}), 200

@im_blueprint.route('/<int:im_id>/download', methods=['GET'])
@jwt_required
def download_instructional_material(im_id):
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        
        download_dir = request.args.get('download_dir')
        downloaded_path = InstructionalMaterialService.download_pdf(im.s3_link, download_dir)
        
        return jsonify({
            'message': 'PDF downloaded successfully',
            'file_path': downloaded_path,
            'file_name': os.path.basename(downloaded_path)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500