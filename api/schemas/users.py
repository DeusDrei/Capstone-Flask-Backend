from marshmallow import Schema, fields, validate

class UserSchema(Schema):
    id = fields.Int(dump_only=True)
    role = fields.Str(required=True)
    staff_id = fields.Str(required=True, validate=validate.Length(min=1))
    first_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    middle_name = fields.Str(validate=validate.Length(max=50), allow_none=True)
    last_name = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    email = fields.Str(required=True, validate=validate.Email())
    password = fields.Str(required=True, load_only=True)  # Don't return in responses
    phone_number = fields.Str(required=True)
    birth_date = fields.Date(required=True)
    created_by = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)  
    updated_by = fields.Str(required=True)
    updated_at = fields.DateTime(dump_only=True)  
    is_deleted = fields.Boolean(dump_only=True) 

class UserLoginSchema(Schema):
    email = fields.Str(required=True, validate=validate.Email())
    password = fields.Str(required=True, validate=validate.Length(min=6))