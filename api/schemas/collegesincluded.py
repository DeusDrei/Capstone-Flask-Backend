from marshmallow import Schema, fields, validate

class CollegeIncludedSchema(Schema):
    college_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
