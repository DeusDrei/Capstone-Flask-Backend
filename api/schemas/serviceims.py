from marshmallow import Schema, fields, validate

class ServiceIMSchema(Schema):
    id = fields.Int(dump_only=True)
    college_id = fields.Int(required=True)
    subject_id = fields.Int(required=True)

    user_id = fields.Int(load_only=True)