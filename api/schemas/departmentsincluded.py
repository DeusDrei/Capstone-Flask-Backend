from marshmallow import Schema, fields

class DepartmentIncludedSchema(Schema):
    department_id = fields.Int(required=True)
    user_id = fields.Int(required=True)