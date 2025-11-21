from marshmallow import Schema, fields

class IMSubmissionSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    im_id = fields.Int(required=True)
    due_date = fields.Date(required=False)
    date_submitted = fields.DateTime(dump_only=True)
