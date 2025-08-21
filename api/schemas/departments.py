from marshmallow import Schema, fields, validate

class DepartmentSchema(Schema):
    id = fields.Int(dump_only=True)
    college_id = fields.Int(required=True)
    abbreviation = fields.Str(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=10))
    created_by = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)  
    updated_by = fields.Str(required=True)
    updated_at = fields.DateTime(dump_only=True)  
    is_deleted = fields.Boolean(dump_only=True) 
