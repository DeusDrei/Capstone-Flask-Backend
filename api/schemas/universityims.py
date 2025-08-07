from marshmallow import Schema, fields, validate

class UniversityIMSchema(Schema):
    id = fields.Int(dump_only=True)
    college_id = fields.Int(required=True)
    department_id = fields.Int(required=True)
    subject_id = fields.Int(required=True)
    year_level = fields.Int(required=True) 
