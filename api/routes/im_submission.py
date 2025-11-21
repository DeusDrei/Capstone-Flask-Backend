from flask import request, jsonify
from flask_smorest import Blueprint
from api.services.im_submission_service import IMSubmissionService
from api.schemas.im_submissions import IMSubmissionSchema
from api.middleware import jwt_required

im_submission_blueprint = Blueprint('im_submissions', __name__, url_prefix="/im-submissions")

@im_submission_blueprint.route('/im/<int:im_id>', methods=['GET'])
@jwt_required
def get_submissions_by_im(im_id):
    """Get all submissions for a specific IM"""
    page = request.args.get('page', 1, type=int)
    paginated = IMSubmissionService.get_submissions_by_im(im_id, page=page)
    schema = IMSubmissionSchema(many=True)
    return jsonify({
        'submissions': schema.dump(paginated.items),
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'per_page': paginated.per_page
    }), 200

@im_submission_blueprint.route('/user/<int:user_id>', methods=['GET'])
@jwt_required
def get_submissions_by_user(user_id):
    """Get all submissions by a specific user"""
    page = request.args.get('page', 1, type=int)
    paginated = IMSubmissionService.get_submissions_by_user(user_id, page=page)
    schema = IMSubmissionSchema(many=True)
    return jsonify({
        'submissions': schema.dump(paginated.items),
        'total': paginated.total,
        'pages': paginated.pages,
        'current_page': paginated.page,
        'per_page': paginated.per_page
    }), 200
