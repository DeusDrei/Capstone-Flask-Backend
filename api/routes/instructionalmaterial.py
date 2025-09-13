from flask import request, jsonify
from flask import send_file, redirect
from flask_smorest import Blueprint
from api.services.instructionalmaterial_service import InstructionalMaterialService
from api.schemas.instructionalmaterials import InstructionalMaterialSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required
import tempfile, os

im_blueprint = Blueprint('instructionalmaterials', __name__, url_prefix="/instructionalmaterials")

@im_blueprint.route('/upload', methods=['POST'])
@jwt_required
def upload_pdf():
    """
    Separate endpoint for PDF upload and processing
    Returns object key and analysis notes
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400
        
        pdf_file = request.files['pdf_file']
        
        object_key, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)
        
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        return jsonify({
            's3_link': object_key,
            'notes': notes,
            'filename': pdf_file.filename
        }), 200
        
    except Exception as e:
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/', methods=['POST'])
@jwt_required
def create_instructional_material():
    """
    Create instructional material using pre-uploaded PDF data
    Expects object_key and notes in the request body
    """
    try:
        data = InstructionalMaterialSchema().load(request.json)
        
        if 's3_link' not in request.json:
            return jsonify({'error': 's3_link is required'}), 400

        s3_link = request.json['s3_link']
        notes = request.json.get('notes', '')

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
                object_key, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)
                
                # Get other form data
                form_data = request.form.to_dict()
                validated_data = InstructionalMaterialSchema(partial=True).load(form_data)
                
                validated_data['s3_link'] = object_key
                if notes:
                    validated_data['notes'] = notes
                
                im = InstructionalMaterialService.update_instructional_material(im_id, validated_data)
                
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            else:
                return jsonify({'error': 'Valid PDF file is required'}), 400
        else:
            data = InstructionalMaterialSchema(partial=True).load(request.json)
            im = InstructionalMaterialService.update_instructional_material(im_id, data)
        
        if not im or im.is_deleted:
            return jsonify({'error': 'Instructional Material not found'}), 404
        
        return jsonify({
            'message': f'Instructional Material {im.version} updated successfully',
            'data': InstructionalMaterialSchema().dump(im)
        }), 200
        
    except Exception as e:
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['GET'])
@jwt_required
def get_instructional_material(im_id):
    im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
    if not im or im.is_deleted:
        return jsonify({'error': 'Instructional Material not found'}), 404

    im_data = InstructionalMaterialSchema().dump(im)
    return jsonify(im_data), 200

@im_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_instructional_materials():
    page = request.args.get('page', 1, type=int)
    paginated_ims = InstructionalMaterialService.get_all_instructional_materials(page=page)
    
    ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
    
    return jsonify({
        'instructional_materials': ims_data,
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_page': paginated_ims.per_page
    }), 200

@im_blueprint.route('/delete-pdf', methods=['POST'])
@jwt_required
def delete_pdf_from_s3():
    """
    Delete a PDF from S3 using the object key provided in the request body.
    """
    try:
        data = request.json
        s3_link = data.get('s3_link')
        if not s3_link:
            return jsonify({'error': 's3_link is required'}), 400
        result = InstructionalMaterialService.delete_pdf_from_s3(s3_link)
        return jsonify({'success': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
        
@im_blueprint.route('/check-missing-sections', methods=['POST'])
@jwt_required
def check_missing_sections():
    """
    Check a PDF for missing required sections using a file upload.
    Accepts multipart/form-data with 'pdf_file'.
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400
        pdf_file = request.files['pdf_file']
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(file_path)
        try:
            result = InstructionalMaterialService.check_missing_sections(file_path)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
        return jsonify({'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

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
    
    ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
    
    return jsonify({
        'instructional_materials': ims_data,
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_per_page': paginated_ims.per_page
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

@im_blueprint.route('/<int:im_id>/pdf', methods=['GET'])
@jwt_required
def stream_instructional_material_pdf(im_id):
    """Return a direct S3 URL redirect or (future) a streamed file for embedding in iframe."""
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        # Build direct S3 https URL
        try:
            url = InstructionalMaterialService.get_s3_url(im.s3_link)
            # Use redirect (302) so the browser loads the PDF directly
            return redirect(url, code=302)
        except Exception as e:
            return jsonify({'error': f'URL build failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@im_blueprint.route('/<int:im_id>/presigned', methods=['GET'])
@jwt_required
def get_presigned_pdf_url(im_id):
    """Return JSON with a presigned URL for the PDF so frontend can embed without auth headers."""
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        url = InstructionalMaterialService.generate_presigned_url(im.s3_link, expires_in=900)
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@im_blueprint.route('/get-for-evaluator', methods=['GET'])
@jwt_required
@roles_required('Evaluator', 'UTLDO Admin', 'Technical Admin')
def get_instructional_material_for_evaluator():
    """
    Get instructional materials with status 'For Evaluator Evaluation'
    """
    try:
        page = request.args.get('page', 1, type=int)
        paginated_ims = InstructionalMaterialService.get_instructional_materials_for_evaluator(page=page)
        
        ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
        
        return jsonify({
            'instructional_materials': ims_data,
            'total': paginated_ims.total,
            'pages': paginated_ims.pages,
            'current_page': paginated_ims.page,
            'per_page': paginated_ims.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/get-for-utldo', methods=['GET'])
@jwt_required
@roles_required('UTLDO Admin', 'Technical Admin')
def get_instructional_material_for_utldo():
    """
    Get instructional materials with status 'For UTLDO Evaluation'
    """
    try:
        page = request.args.get('page', 1, type=int)
        paginated_ims = InstructionalMaterialService.get_instructional_materials_for_utldo(page=page)
        
        ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
        
        return jsonify({
            'instructional_materials': ims_data,
            'total': paginated_ims.total,
            'pages': paginated_ims.pages,
            'current_page': paginated_ims.page,
            'per_page': paginated_ims.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400