from flask import request, jsonify
from flask import send_file, redirect
from flask_smorest import Blueprint
from api.services.instructionalmaterial_service import InstructionalMaterialService
from api.services.email_service import EmailService
import boto3
from api.schemas.instructionalmaterials import InstructionalMaterialSchema
from sqlalchemy.exc import IntegrityError
from api.middleware import jwt_required, roles_required
import tempfile, os

im_blueprint = Blueprint('instructionalmaterials', __name__, url_prefix="/instructionalmaterials")

@im_blueprint.route('/upload', methods=['POST'])
@jwt_required
def upload_pdf():
    """
    Separate endpoint for PDF upload and processing
    Returns object key and analysis notes
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400
        
        pdf_file = request.files['pdf_file']
        
        object_key, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)

        # If caller provided an im_id in the multipart form, persist the s3_link
        # and notes into the Instructional Material record so uploads update assigned IMs.
        try:
            im_id = request.form.get('im_id') or request.args.get('im_id')
            if im_id:
                try:
                    validated = {
                        's3_link': object_key,
                        'notes': notes,
                        # preserve existing status/other fields by using partial update
                    }
                    InstructionalMaterialService.update_instructional_material(int(im_id), validated)
                except Exception as e:
                    # Log but don't fail the upload — return the s3_link regardless
                    print(f"Failed to persist s3_link for im_id={im_id}: {e}")
        except Exception:
            # ignore any errors reading im_id
            pass

        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

        return jsonify({
            's3_link': object_key,
            'notes': notes,
            'filename': pdf_file.filename
        }), 200
        
    except Exception as e:
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/', methods=['POST'])
@jwt_required
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
def create_instructional_material():
    """
    Create instructional material - supports both assignment (no file) and creation with file
    For assignment workflow: PIMEC assigns IM without uploading, status set to 'Assigned to Faculty'
    For upload workflow: includes s3_link and file data
    """
    try:
        # Read raw JSON and extract helper fields before schema validation to
        # avoid Marshmallow 'Unknown field' errors (author_ids is not part of schema)
        raw = dict(request.json or {})
        author_ids = raw.pop('author_ids', [])
        s3_link = raw.get('s3_link', None)
        notes = raw.get('notes', '')

        # Validate remaining payload against the schema
        data = InstructionalMaterialSchema().load(raw)
        
        # If no s3_link provided, this is an assignment workflow - set status accordingly
        is_assignment = not s3_link
        if is_assignment:
            data['status'] = 'Assigned to Faculty'
            data['s3_link'] = None
        
        im = InstructionalMaterialService.create_instructional_material(data, s3_link, notes)

        # If this is an assignment, send email notification to all authors
        if is_assignment and author_ids:
            try:
                # Fetch author emails
                from api.models.users import User
                author_emails = []
                for author_id in author_ids:
                    user = User.query.get(author_id)
                    if user and user.email:
                        author_emails.append(user.email)
                
                # Send notification to all authors
                if author_emails:
                    subject_name = "an instructional material"  # You can enhance this with actual subject name
                    for email in author_emails:
                        EmailService.send_instructional_material_notification(
                            receiver_email=email,
                            filename=f"IM-{im.id}",
                            status="Assigned to Faculty",
                            notes="You have been assigned to create an instructional material. Please upload the PDF file.",
                            action="assigned"
                        )
            except Exception as email_error:
                # Log email error but don't fail the request
                print(f"Failed to send email notification: {email_error}")

        return jsonify({
            'message': f'Instructional Material {im.version} {"assigned" if is_assignment else "created"} successfully',
            'id': im.id,
            'data': InstructionalMaterialSchema().dump(im)
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['PUT'])
@jwt_required
def update_instructional_material(im_id):
    """
    Update instructional material - can accept new PDF data or just metadata
    """
    try:
        # Check if this is a file upload or JSON update
        if request.files and 'pdf_file' in request.files:
            # Handle PDF file upload and processing
            pdf_file = request.files['pdf_file']
            if pdf_file.filename != '' and pdf_file.filename.lower().endswith('.pdf'):
                object_key, notes, temp_file_path = InstructionalMaterialService.process_pdf_file(pdf_file)
                
                # Get other form data
                form_data = request.form.to_dict()
                validated_data = InstructionalMaterialSchema(partial=True).load(form_data)
                
                validated_data['s3_link'] = object_key
                if notes:
                    validated_data['notes'] = notes
                
                im = InstructionalMaterialService.update_instructional_material(im_id, validated_data)
                
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            else:
                return jsonify({'error': 'Valid PDF file is required'}), 400
        else:
            data = InstructionalMaterialSchema(partial=True).load(request.json)
            im = InstructionalMaterialService.update_instructional_material(im_id, data)
        
        if not im or im.is_deleted:
            return jsonify({'error': 'Instructional Material not found'}), 404
        
        return jsonify({
            'message': f'Instructional Material {im.version} updated successfully',
            'data': InstructionalMaterialSchema().dump(im)
        }), 200
        
    except Exception as e:
        if 'temp_file_path' in locals() and temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['GET'])
@jwt_required
def get_instructional_material(im_id):
    im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
    if not im or im.is_deleted:
        return jsonify({'error': 'Instructional Material not found'}), 404

    im_data = InstructionalMaterialSchema().dump(im)
    return jsonify(im_data), 200

@im_blueprint.route('/', methods=['GET'])
@jwt_required
def get_all_instructional_materials():
    page = request.args.get('page', 1, type=int)
    paginated_ims = InstructionalMaterialService.get_all_instructional_materials(page=page)
    
    ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
    
    return jsonify({
        'instructional_materials': ims_data,
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_page': paginated_ims.per_page
    }), 200

@im_blueprint.route('/delete-pdf', methods=['POST'])
@jwt_required
def delete_pdf_from_s3():
    """
    Delete a PDF from S3 using the object key provided in the request body.
    """
    try:
        data = request.json
        s3_link = data.get('s3_link')
        if not s3_link:
            return jsonify({'error': 's3_link is required'}), 400
        result = InstructionalMaterialService.delete_pdf_from_s3(s3_link)
        return jsonify({'success': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400
        
@im_blueprint.route('/check-missing-sections', methods=['POST'])
@jwt_required
def check_missing_sections():
    """
    Check a PDF for missing required sections using a file upload.
    Accepts multipart/form-data with 'pdf_file'.
    """
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400
        pdf_file = request.files['pdf_file']
        
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, pdf_file.filename)
        pdf_file.save(file_path)
        try:
            result = InstructionalMaterialService.check_missing_sections(file_path)
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
        return jsonify({'result': result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/<int:im_id>', methods=['DELETE'])
@jwt_required
@roles_required('Technical Admin', 'PIMEC', 'UTLDO Admin')
def delete_instructional_material(im_id):
    success = InstructionalMaterialService.soft_delete_instructional_material(im_id)
    if not success:
        return jsonify({'error': 'Instructional Material not found'}), 404

    return jsonify({'message': 'Instructional Material deleted successfully'}), 200

@im_blueprint.route('/deleted', methods=['GET'])
@jwt_required
@roles_required('Technical Admin', 'PIMEC', 'UTLDO Admin')
def get_deleted_instructional_materials():
    page = request.args.get('page', 1, type=int)
    paginated_ims = InstructionalMaterialService.get_deleted_instructional_materials(page=page)
    
    ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
    
    return jsonify({
        'instructional_materials': ims_data,
        'total': paginated_ims.total,
        'pages': paginated_ims.pages,
        'current_page': paginated_ims.page,
        'per_per_page': paginated_ims.per_page
    }), 200

@im_blueprint.route('/<int:im_id>/restore', methods=['POST'])
@jwt_required
@roles_required('Technical Admin', 'PIMEC', 'UTLDO Admin')
def restore_instructional_material(im_id):
    success = InstructionalMaterialService.restore_instructional_material(im_id)
    if not success:
        return jsonify({'error': 'Instructional Material not found or already active'}), 404
    return jsonify({'message': 'Instructional Material restored successfully'}), 200

@im_blueprint.route('/<int:im_id>/download', methods=['GET'])
@jwt_required
def download_instructional_material(im_id):
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        
        download_dir = request.args.get('download_dir')
        downloaded_path = InstructionalMaterialService.download_pdf(im.s3_link, download_dir)
        
        return jsonify({
            'message': 'PDF downloaded successfully',
            'file_path': downloaded_path,
            'file_name': os.path.basename(downloaded_path)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@im_blueprint.route('/<int:im_id>/pdf', methods=['GET'])
@jwt_required
def stream_instructional_material_pdf(im_id):
    """Return a direct S3 URL redirect or (future) a streamed file for embedding in iframe."""
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        # Build direct S3 https URL
        try:
            url = InstructionalMaterialService.get_s3_url(im.s3_link)
            # Use redirect (302) so the browser loads the PDF directly
            return redirect(url, code=302)
        except Exception as e:
            return jsonify({'error': f'URL build failed: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@im_blueprint.route('/<int:im_id>/presigned', methods=['GET'])
@jwt_required
def get_presigned_pdf_url(im_id):
    """Return JSON with a presigned URL for the PDF so frontend can embed without auth headers."""
    try:
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im or im.is_deleted or not im.s3_link:
            return jsonify({'error': 'Instructional Material not found or no PDF available'}), 404
        url = InstructionalMaterialService.generate_presigned_url(im.s3_link, expires_in=900)
        return jsonify({'url': url})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@im_blueprint.route('/cert-of-appreciation', methods=['GET'])
@jwt_required
def get_cert_of_appreciation():
    """Download the certificate DOCX template from S3.
    This endpoint downloads the template file stored at 
    'requirements/cert-of-appreciation.docx' in the configured S3 bucket
    and returns it as a file download.
    """
    try:
        object_key = 'requirements/cert-of-appreciation.docx'
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        
        if not bucket_name:
            return jsonify({'error': 'AWS_BUCKET_NAME not configured'}), 500
        
        # Download file from S3 to a temporary location
        s3 = boto3.client('s3')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file_path = temp_file.name
        temp_file.close()
        
        try:
            s3.download_file(bucket_name, object_key, temp_file_path)
            
            # Send the file to the client
            response = send_file(
                temp_file_path,
                as_attachment=True,
                download_name='cert-of-appreciation.docx',
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
            
            # Schedule file deletion after sending
            @response.call_on_close
            def cleanup():
                try:
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                except:
                    pass
            
            return response
            
        except Exception as download_error:
            # Clean up temp file on error
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            raise download_error
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@im_blueprint.route('/send-certs-of-appreciation/<int:im_id>', methods=['POST'])
@jwt_required
def send_certs_of_appreciation(im_id):
    """Accept a file upload and recipients, then email the attachment to multiple recipients.
    Expects multipart/form-data with fields:
      - file: the uploaded file
      - recipients: comma-separated emails OR multiple recipients fields
      - subject (optional)
      - text_body / html_body (optional)
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'file is required'}), 400
        uploaded = request.files['file']
        if uploaded.filename == '':
            return jsonify({'error': 'file is required'}), 400

        # get optional fields
        subject = request.form.get('subject')
        text_body = request.form.get('text_body')
        html_body = request.form.get('html_body')

        # read bytes
        file_bytes = uploaded.read()
        filename = uploaded.filename

        # fetch IM and derive recipients from its authors
        recipients = []
        im = InstructionalMaterialService.get_instructional_material_by_id(im_id)
        if not im:
            return jsonify({'error': f'Instructional Material with id {im_id} not found'}), 404

        # im.authors is a relationship of Author objects -> .user -> .email
        for author_rel in getattr(im, 'authors', []) or []:
            user = getattr(author_rel, 'user', None)
            if user and getattr(user, 'email', None):
                recipients.append(user.email)

        if not recipients:
            return jsonify({'error': 'No author emails found for the specified instructional material'}), 400

        # Prepare a formal email body if none provided, using author names
        # build author display names
        author_names = []
        for author_rel in getattr(im, 'authors', []) or []:
            user = getattr(author_rel, 'user', None)
            if not user:
                continue
            parts = [getattr(user, 'first_name', '') or '']
            middle = getattr(user, 'middle_name', None)
            if middle:
                parts.append(middle)
            parts.append(getattr(user, 'last_name', '') or '')
            full_name = ' '.join([p for p in parts if p and p.strip()])
            author_names.append(full_name)

        # default subject
        if not subject:
            subject = f"Certificate of Appreciation — Instructional Materials"

        # If the client didn't supply html_body/text_body, construct polite/formal templates
        if not html_body:
            authors_html = '<br>'.join([f"<strong>{name}</strong>" for name in author_names]) if author_names else ''
            html_body = f"""
            <html>
            <body style=\"font-family: Arial, sans-serif; color: #222; line-height:1.4;\">
              <h2 style=\"color:#0b3255;\">Certificate of Appreciation</h2>
              <p>Congratulations.</p>
              <p>This certificate is presented in recognition of the exemplary services and significant contributions made
                 in the preparation and development of instructional materials.</p>
              <p><strong>Awarded to:</strong><br>
              {authors_html}
              </p>
              <p>We sincerely thank the above individuals for their dedication and commitment to quality teaching and learning.
                 Their efforts have been instrumental in ensuring high standards in our instructional resources.</p>
              <br>
              <p>With appreciation,<br>
                 The Instructional Materials Committee</p>
            </body>
            </html>
            """

        if not text_body:
            authors_text = ', '.join(author_names) if author_names else ''
            text_body = (
                f"Certificate of Appreciation\n\n"
                f"Congratulations.\n\n"
                f"This certificate is presented in recognition of the contributions made in the preparation and development of instructional materials.\n\n"
                f"Awarded to:\n{authors_text}\n\n"
                f"We sincerely thank the above individuals for their dedication and commitment to quality teaching and learning.\n\n"
                f"With appreciation,\nThe Instructional Materials Committee"
            )

        # call EmailService helper directly
        from api.services.email_service import EmailService
        sent = EmailService.send_file_to_recipients(recipients, file_bytes, filename, subject=subject, html_body=html_body, text_body=text_body)

        if sent:
            return jsonify({'success': True, 'recipients': recipients}), 200
        else:
            return jsonify({'error': 'Failed to send email to recipients'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@im_blueprint.route('/get-for-pimec', methods=['GET'])
@jwt_required
@roles_required('PIMEC', 'UTLDO Admin', 'Technical Admin')
def get_instructional_material_for_pimec():
    """
    Get instructional materials with status 'For PIMECm Evaluation'
    """
    try:
        page = request.args.get('page', 1, type=int)
        paginated_ims = InstructionalMaterialService.get_instructional_materials_for_pimec(page=page)

        ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
        
        return jsonify({
            'instructional_materials': ims_data,
            'total': paginated_ims.total,
            'pages': paginated_ims.pages,
            'current_page': paginated_ims.page,
            'per_page': paginated_ims.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@im_blueprint.route('/get-for-utldo', methods=['GET'])
@jwt_required
@roles_required('UTLDO Admin', 'Technical Admin', 'PIMEC')
def get_instructional_material_for_utldo():
    """
    Get instructional materials with status 'For UTLDO Evaluation'
    """
    try:
        page = request.args.get('page', 1, type=int)
        paginated_ims = InstructionalMaterialService.get_instructional_materials_for_utldo(page=page)
        
        ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
        
        return jsonify({
            'instructional_materials': ims_data,
            'total': paginated_ims.total,
            'pages': paginated_ims.pages,
            'current_page': paginated_ims.page,
            'per_page': paginated_ims.per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@im_blueprint.route('/get-for-certification', methods=['GET'])
@jwt_required
@roles_required('UTLDO Admin', 'Technical Admin', 'PIMEC')
def get_instructional_materials_for_certification():
    """
    Get instructional materials with status 'For Certification'
    """
    try:
        page = request.args.get('page', 1, type=int)
        paginated_ims = InstructionalMaterialService.get_instructional_materials_for_certification(page=page)
        ims_data = InstructionalMaterialSchema(many=True).dump(paginated_ims.items)
        return jsonify({
            'instructional_materials': ims_data,
            'total': paginated_ims.total,
            'pages': paginated_ims.pages,
            'current_page': paginated_ims.page,
            'per_page': paginated_ims.per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

