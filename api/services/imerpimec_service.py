from api.extensions import db
from api.models.imerpimec import IMERPIMEC

class IMERPIMECService:
    @staticmethod
    def create_imerpimec(data):
        """Create a new IMERPIMEC record"""
        # Calculate subtotals
        a_subtotal = data['a1'] + data['a2'] + data['a3']
        b_subtotal = data['b1'] + data['b2'] + data['b3']
        c_subtotal = data['c1'] + data['c2'] + data['c3'] + data['c4'] + data['c5'] + data['c6'] + data['c7'] + data['c8'] + data['c9'] + data['c10']
        d_subtotal = data['d1'] + data['d2'] + data['d3']
        e_subtotal = data['e1'] + data['e2'] + data['e3']
        total = a_subtotal + b_subtotal + c_subtotal + d_subtotal + e_subtotal
        
        new_imerpimec = IMERPIMEC(
            a1=data['a1'], a2=data['a2'], a3=data['a3'],
            a_comment=data.get('a_comment'), a_subtotal=a_subtotal,
            b1=data['b1'], b2=data['b2'], b3=data['b3'],
            b_comment=data.get('b_comment'), b_subtotal=b_subtotal,
            c1=data['c1'], c2=data['c2'], c3=data['c3'], c4=data['c4'], c5=data['c5'],
            c6=data['c6'], c7=data['c7'], c8=data['c8'], c9=data['c9'], c10=data['c10'],
            c_comment=data.get('c_comment'), c_subtotal=c_subtotal,
            d1=data['d1'], d2=data['d2'], d3=data['d3'],
            d_comment=data.get('d_comment'), d_subtotal=d_subtotal,
            e1=data['e1'], e2=data['e2'], e3=data['e3'],
            e_comment=data.get('e_comment'), e_subtotal=e_subtotal,
            total=total, overall_comment=data.get('overall_comment'),
            created_by=data['created_by'], updated_by=data['updated_by']
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
            # Update individual fields
            for key, value in data.items():
                if hasattr(imerpimec, key) and key not in ['a_subtotal', 'b_subtotal', 'c_subtotal', 'd_subtotal', 'e_subtotal', 'total']:
                    setattr(imerpimec, key, value)
            
            # Recalculate subtotals and total
            imerpimec.a_subtotal = imerpimec.a1 + imerpimec.a2 + imerpimec.a3
            imerpimec.b_subtotal = imerpimec.b1 + imerpimec.b2 + imerpimec.b3
            imerpimec.c_subtotal = imerpimec.c1 + imerpimec.c2 + imerpimec.c3 + imerpimec.c4 + imerpimec.c5 + imerpimec.c6 + imerpimec.c7 + imerpimec.c8 + imerpimec.c9 + imerpimec.c10
            imerpimec.d_subtotal = imerpimec.d1 + imerpimec.d2 + imerpimec.d3
            imerpimec.e_subtotal = imerpimec.e1 + imerpimec.e2 + imerpimec.e3
            imerpimec.total = imerpimec.a_subtotal + imerpimec.b_subtotal + imerpimec.c_subtotal + imerpimec.d_subtotal + imerpimec.e_subtotal
            
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