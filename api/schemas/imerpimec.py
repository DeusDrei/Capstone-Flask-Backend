from marshmallow import Schema, fields

class IMERPIMECSchema(Schema):
    id = fields.Int(dump_only=True)
    
    # A section
    a1 = fields.Int(required=True)
    a2 = fields.Int(required=True)
    a3 = fields.Int(required=True)
    a_comment = fields.Str(required=False)
    a_subtotal = fields.Int(dump_only=True)
    
    # B section
    b1 = fields.Int(required=True)
    b2 = fields.Int(required=True)
    b3 = fields.Int(required=True)
    b_comment = fields.Str(required=False)
    b_subtotal = fields.Int(dump_only=True)
    
    # C section
    c1 = fields.Int(required=True)
    c2 = fields.Int(required=True)
    c3 = fields.Int(required=True)
    c4 = fields.Int(required=True)
    c5 = fields.Int(required=True)
    c6 = fields.Int(required=True)
    c7 = fields.Int(required=True)
    c8 = fields.Int(required=True)
    c9 = fields.Int(required=True)
    c10 = fields.Int(required=True)
    c_comment = fields.Str(required=False)
    c_subtotal = fields.Int(dump_only=True)
    
    # D section
    d1 = fields.Int(required=True)
    d2 = fields.Int(required=True)
    d3 = fields.Int(required=True)
    d_comment = fields.Str(required=False)
    d_subtotal = fields.Int(dump_only=True)
    
    # E section
    e1 = fields.Int(required=True)
    e2 = fields.Int(required=True)
    e3 = fields.Int(required=True)
    e_comment = fields.Str(required=False)
    e_subtotal = fields.Int(dump_only=True)
    
    # Totals
    total = fields.Int(dump_only=True)
    overall_comment = fields.Str(required=False)
    created_by = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)  
    updated_by = fields.Str(required=True)
    updated_at = fields.DateTime(dump_only=True)  
    is_deleted = fields.Boolean(dump_only=True)
    user_id = fields.Int(load_only=True) 
