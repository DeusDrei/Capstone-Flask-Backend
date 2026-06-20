from marshmallow import Schema, fields


class IMCertificateSchema(Schema):
    id = fields.Int(dump_only=True)
    qr_id = fields.Str(dump_only=True)
    im_id = fields.Int(required=True)
    user_id = fields.Int(required=True)
    s3_link = fields.Str(dump_only=True)
    date_issued = fields.Date(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    # Enriched fields from joined queries
    author_name = fields.Str(dump_only=True)
    subject_code = fields.Str(dump_only=True)
    subject_title = fields.Str(dump_only=True)
    im_version = fields.Str(dump_only=True)
