from marshmallow import Schema, fields

class IMERPIMECSchema(Schema):
    id = fields.Int(dump_only=True)
    a = fields.Int(required=True)
    b = fields.Int(required=True)
    c = fields.Int(required=True)
    d = fields.Int(required=True)
    e = fields.Int(required=True)
    created_by = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)  
    updated_by = fields.Str(required=True)
    updated_at = fields.DateTime(dump_only=True)  
    is_deleted = fields.Boolean(dump_only=True) 
