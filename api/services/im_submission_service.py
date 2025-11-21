from api.extensions import db
from api.models.im_submissions import IMSubmission

class IMSubmissionService:
    @staticmethod
    def create_submission(user_id, im_id, due_date=None):
        """Create a new IM submission record"""
        submission = IMSubmission(
            user_id=user_id,
            im_id=im_id,
            due_date=due_date
        )
        db.session.add(submission)
        db.session.commit()
        return submission

    @staticmethod
    def get_submissions_by_im(im_id, page=1):
        """Get all submissions for a specific IM"""
        per_page = 10
        return IMSubmission.query.filter_by(im_id=im_id).paginate(
            page=page, per_page=per_page, error_out=False
        )

    @staticmethod
    def get_submissions_by_user(user_id, page=1):
        """Get all submissions by a specific user"""
        per_page = 10
        return IMSubmission.query.filter_by(user_id=user_id).paginate(
            page=page, per_page=per_page, error_out=False
        )
