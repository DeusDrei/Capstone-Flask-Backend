from marshmallow import Schema, fields


class SubjectDepartmentSchema(Schema):
    subject_id = fields.Int(required=True)
    department_id = fields.Int(required=True)
