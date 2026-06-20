from marshmallow import Schema, fields

class AuthorSchema(Schema):
    im_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
