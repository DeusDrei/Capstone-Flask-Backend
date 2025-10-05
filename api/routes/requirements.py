from flask import jsonify, send_file, redirect
from flask_smorest import Blueprint
from api.services.requirements_service import RequirementsService
from api.middleware import jwt_required
import os

requirements_blueprint = Blueprint('requirements', __name__, url_prefix="/requirements")

@requirements_blueprint.route('/recommendation-letter/download', methods=['GET'])
@jwt_required
def download_recommendation_letter():
    """
    Download the recommendation letter PDF from S3
    Returns the PDF file for download
    """
    try:
        file_path = RequirementsService.download_requirements_pdf()
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'Requirements file not found'}), 404
        
        # Send the file and clean up after
        def remove_file(response):
            try:
                os.remove(file_path)
            except:
                pass
            return response
        
        response = send_file(
            file_path,
            as_attachment=True,
            download_name='recommendation-letter.pdf',
            mimetype='application/pdf'
        )
        
        response.call_on_close(lambda: os.remove(file_path) if os.path.exists(file_path) else None)
        
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@requirements_blueprint.route('/recommendation-letter/view', methods=['GET'])
@jwt_required
def view_recommendation_letter():
    """
    Get a presigned URL for viewing the recommendation letter PDF inline
    Returns JSON with the presigned URL
    """
    try:
        url = RequirementsService.generate_requirements_presigned_url(expires_in=3600)
        
        return jsonify({
            'url': url,
            'filename': 'recommendation-letter.pdf',
            'expires_in': 3600
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@requirements_blueprint.route('/recommendation-letter/redirect', methods=['GET'])
@jwt_required  
def redirect_to_recommendation_letter():
    """
    Redirect directly to the recommendation letter PDF
    Uses presigned URL for secure access
    """
    try:
        url = RequirementsService.generate_requirements_presigned_url(expires_in=900)
        return redirect(url, code=302)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@requirements_blueprint.route('/recommendation-letter/check', methods=['GET'])
@jwt_required
def check_recommendation_letter():
    """
    Check if the recommendation letter PDF exists in S3
    Returns status information
    """
    try:
        exists = RequirementsService.check_requirements_file_exists()
        
        return jsonify({
            'exists': exists,
            'filename': 'recommendation-letter.pdf',
            'path': 'requirements/recommendation-letter.pdf'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@requirements_blueprint.route('/recommendation-letter/info', methods=['GET'])
@jwt_required
def get_recommendation_letter_info():
    """
    Get information about available endpoints for the recommendation letter
    """
    return jsonify({
        'endpoints': {
            'download': '/requirements/recommendation-letter/download',
            'view': '/requirements/recommendation-letter/view', 
            'redirect': '/requirements/recommendation-letter/redirect',
            'check': '/requirements/recommendation-letter/check'
        },
        'description': 'Endpoints for accessing the recommendation letter PDF from S3',
        'note': 'All endpoints require JWT authentication'
    }), 200