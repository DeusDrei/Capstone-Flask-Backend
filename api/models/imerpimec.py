from datetime import datetime, UTC
from api.extensions import db

class IMERPIMEC(db.Model):
    __tablename__ = 'imerpimec'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # A section
    a1 = db.Column(db.Integer, nullable=False)
    a2 = db.Column(db.Integer, nullable=False)
    a3 = db.Column(db.Integer, nullable=False)
    a_comment = db.Column(db.Text, nullable=True)
    a_subtotal = db.Column(db.Integer, nullable=False)
    
    # B section
    b1 = db.Column(db.Integer, nullable=False)
    b2 = db.Column(db.Integer, nullable=False)
    b3 = db.Column(db.Integer, nullable=False)
    b_comment = db.Column(db.Text, nullable=True)
    b_subtotal = db.Column(db.Integer, nullable=False)
    
    # C section
    c1 = db.Column(db.Integer, nullable=False)
    c2 = db.Column(db.Integer, nullable=False)
    c3 = db.Column(db.Integer, nullable=False)
    c4 = db.Column(db.Integer, nullable=False)
    c5 = db.Column(db.Integer, nullable=False)
    c6 = db.Column(db.Integer, nullable=False)
    c7 = db.Column(db.Integer, nullable=False)
    c8 = db.Column(db.Integer, nullable=False)
    c9 = db.Column(db.Integer, nullable=False)
    c10 = db.Column(db.Integer, nullable=False)
    c_comment = db.Column(db.Text, nullable=True)
    c_subtotal = db.Column(db.Integer, nullable=False)
    
    # D section
    d1 = db.Column(db.Integer, nullable=False)
    d2 = db.Column(db.Integer, nullable=False)
    d3 = db.Column(db.Integer, nullable=False)
    d_comment = db.Column(db.Text, nullable=True)
    d_subtotal = db.Column(db.Integer, nullable=False)
    
    # E section
    e1 = db.Column(db.Integer, nullable=False)
    e2 = db.Column(db.Integer, nullable=False)
    e3 = db.Column(db.Integer, nullable=False)
    e_comment = db.Column(db.Text, nullable=True)
    e_subtotal = db.Column(db.Integer, nullable=False)
    
    # Totals
    total = db.Column(db.Integer, nullable=False)
    overall_comment = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(UTC))
    updated_by = db.Column(db.String(255), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(UTC), onupdate=datetime.now(UTC))
    is_deleted = db.Column(db.Boolean, default=False)

    def __init__(self, a1, a2, a3, a_comment, a_subtotal, b1, b2, b3, b_comment, b_subtotal,
                 c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c_comment, c_subtotal,
                 d1, d2, d3, d_comment, d_subtotal, e1, e2, e3, e_comment, e_subtotal,
                 total, overall_comment, created_by, updated_by):
        self.a1 = a1
        self.a2 = a2
        self.a3 = a3
        self.a_comment = a_comment
        self.a_subtotal = a_subtotal
        self.b1 = b1
        self.b2 = b2
        self.b3 = b3
        self.b_comment = b_comment
        self.b_subtotal = b_subtotal
        self.c1 = c1
        self.c2 = c2
        self.c3 = c3
        self.c4 = c4
        self.c5 = c5
        self.c6 = c6
        self.c7 = c7
        self.c8 = c8
        self.c9 = c9
        self.c10 = c10
        self.c_comment = c_comment
        self.c_subtotal = c_subtotal
        self.d1 = d1
        self.d2 = d2
        self.d3 = d3
        self.d_comment = d_comment
        self.d_subtotal = d_subtotal
        self.e1 = e1
        self.e2 = e2
        self.e3 = e3
        self.e_comment = e_comment
        self.e_subtotal = e_subtotal
        self.total = total
        self.overall_comment = overall_comment
        self.created_by = created_by
        self.updated_by = updated_by

    def __repr__(self):
        return f'<IMERPIMEC {self.id}>'