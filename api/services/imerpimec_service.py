from api.extensions import db
from api.models.imerpimec import IMERPIMEC

class IMERPIMECService:
    @staticmethod
    def create_imerpimec(data):
        """Create a new IMERPIMEC record"""
        new_imerpimec = IMERPIMEC(
            a=data['a'],
            b=data['b'],
            c=data['c'],
            d=data['d'],
            e=data['e'],
            created_by=data['created_by'],
            updated_by=data['updated_by']
        )
        
        db.session.add(new_imerpimec)
        db.session.commit()
        return new_imerpimec

    @staticmethod
    def get_imerpimec_by_id(imerpimec_id):
        """Get IMERPIMEC by ID (including soft-deleted ones)"""
        return db.session.get(IMERPIMEC, imerpimec_id)

    @staticmethod
    def get_all_imerpimecs(page=1):
        """Get all active IMERPIMEC records with pagination"""
        per_page = 10
        return IMERPIMEC.query.filter_by(is_deleted=False).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def update_imerpimec(imerpimec_id, data):
        """Update IMERPIMEC data"""
        imerpimec = IMERPIMEC.query.filter_by(id=imerpimec_id, is_deleted=False).first()
        if not imerpimec:
            return None
        
        try:
            for key, value in data.items():
                if hasattr(imerpimec, key):
                    setattr(imerpimec, key, value)
            
            if 'updated_by' in data:
                imerpimec.updated_by = data['updated_by']
            
            db.session.commit()
            return imerpimec
            
        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_imerpimec(imerpimec_id):
        """Mark IMERPIMEC as deleted (soft delete)"""
        imerpimec = IMERPIMEC.query.filter_by(id=imerpimec_id, is_deleted=False).first()
        if not imerpimec:
            return False
        
        imerpimec.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def restore_imerpimec(imerpimec_id):
        """Restore a soft-deleted IMERPIMEC"""
        imerpimec = IMERPIMEC.query.filter_by(id=imerpimec_id, is_deleted=True).first()
        if not imerpimec:
            return False
        
        imerpimec.is_deleted = False
        db.session.commit()
        return True