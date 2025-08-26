from marshmallow import Schema, fields, validate

class InstructionalMaterialSchema(Schema):
    id = fields.Int(dump_only=True)
    im_type = fields.Str(required=True)
    university_im_id = fields.Int(required=False)
    service_im_id = fields.Int(required=False)
    status = fields.Str(required=True)
    validity = fields.Str(required=True)
    version = fields.Str(required=True)
    s3_link = fields.Str(required=True)
    notes = fields.Str(required=False)
    created_by = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)  
    updated_by = fields.Str(required=True)
    updated_at = fields.DateTime(dump_only=True)  
    is_deleted = fields.Boolean(dump_only=True) 
