from api.extensions import db
from api.models.authors import Author
from api.models.instructionalmaterials import InstructionalMaterial
from api.models.users import User
from sqlalchemy.exc import IntegrityError

class AuthorService:
    @staticmethod
    def create_author(im_id, user_id):
        """
        Create a new author association between instructional material and user
        """
        if not InstructionalMaterial.query.get(im_id):
            raise ValueError(f"Instructional material with ID {im_id} does not exist")

        if not User.query.get(user_id):
            raise ValueError(f"User with ID {user_id} does not exist")
        
        try:
            author = Author(
                im_id=im_id,
                user_id=user_id
            )
            db.session.add(author)
            db.session.commit()
            return author
        except IntegrityError as e:
            db.session.rollback()
            if "im_id" in str(e.orig):
                raise ValueError("Instructional material does not exist")
            elif "user_id" in str(e.orig):
                raise ValueError("User does not exist")
            elif "unique constraint" in str(e.orig).lower():
                raise ValueError("This author association already exists")
            raise ValueError("Database integrity error")

    @staticmethod
    def get_author(im_id, user_id):
        """
        Get a specific author association
        """
        return Author.query.filter_by(
            im_id=im_id,
            user_id=user_id
        ).first()

    @staticmethod
    def get_instructional_materials_for_user(user_id):
        """
        Get all instructional materials associated with a user as author
        """
        return Author.query.filter_by(user_id=user_id).all()

    @staticmethod
    def get_authors_for_instructional_material(im_id):
        """
        Get all authors associated with an instructional material
        """
        return Author.query.filter_by(im_id=im_id).all()

    @staticmethod
    def delete_author(im_id, user_id):
        """
        Delete an author association
        """
        author = Author.query.filter_by(
            im_id=im_id,
            user_id=user_id
        ).first()
        
        if not author:
            return False
            
        db.session.delete(author)
        db.session.commit()
        return True