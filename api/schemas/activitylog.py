from marshmallow import Schema, fields

class ActivityLogSchema(Schema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    action = fields.Str(required=True)
    table_name = fields.Str(required=True)
    record_id = fields.Int(required=False)
    old_values = fields.Str(required=False)
    new_values = fields.Str(required=False)
    description = fields.Str(required=True)
    created_at = fields.DateTime(dump_only=True)