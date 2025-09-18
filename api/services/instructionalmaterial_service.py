import os
import boto3
import pdfplumber
import re
from dotenv import load_dotenv
from api.extensions import db
from api.models.instructionalmaterials import InstructionalMaterial
from api.services.email_service import EmailService
import tempfile
import uuid
import boto3

load_dotenv()

class InstructionalMaterialService:
    @staticmethod
    def _compute_version(published, utldo, evaluator, ai):
        return f"{published}.{utldo}.{evaluator}.{ai}"

    @staticmethod
    def _increment_counters_for_status(im_or_counters, status, is_model=False):
        """
        im_or_counters: either an InstructionalMaterial model instance (is_model=True)
                        or a dict of counters (is_model=False).
        status: new status string
        Behavior:
        - Published: increment published and reset other attempts to 0
        - For UTLDO Evaluation: increment utldo_attempt
        - For Evaluator Evaluation: increment evaluator_attempt
        - For Resubmission: increment ai_attempt
        """
        key_map = {
            'Published': 'published',
            'For UTLDO Evaluation': 'utldo_attempt',
            'For Evaluator Evaluation': 'evaluator_attempt',
            'For Resubmission': 'ai_attempt'
        }

        if is_model:
            # operate on SQLAlchemy model instance
            if status == 'Published':
                # increment published and reset others
                im_or_counters.published = (im_or_counters.published or 0) + 1
                im_or_counters.utldo_attempt = 0
                im_or_counters.evaluator_attempt = 0
                im_or_counters.ai_attempt = 0
            else:
                key = key_map.get(status)
                if key:
                    current = getattr(im_or_counters, key, 0) or 0
                    setattr(im_or_counters, key, current + 1)
        else:
            # operate on a dict of counters
            if status == 'Published':
                im_or_counters['published'] = im_or_counters.get('published', 0) + 1
                im_or_counters['utldo_attempt'] = 0
                im_or_counters['evaluator_attempt'] = 0
                im_or_counters['ai_attempt'] = 0
            else:
                key = key_map.get(status)
                if key:
                    im_or_counters[key] = im_or_counters.get(key, 0) + 1

    @staticmethod
    def upload_pdf_to_s3(file_path, filename):
        """
        Uploads PDF to S3 and returns the object key
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            if not os.path.exists(file_path):
                raise ValueError("File not found")
            
            if not file_path.lower().endswith('.pdf'):
                raise ValueError("File must be a PDF")
            
            unique_folder = str(uuid.uuid4())
            
            s3_key = f"instructional_materials/{unique_folder}/{filename}"
            
            s3 = boto3.client('s3')
            # Set metadata so default behavior is inline viewing
            extra_args = {
                'ContentType': 'application/pdf',
                'ContentDisposition': f'inline; filename="{filename}"'
            }
            s3.upload_file(file_path, bucket_name, s3_key, ExtraArgs=extra_args)
            
            return s3_key
            
        except Exception as e:
            raise Exception(f"S3 upload error: {str(e)}")

    @staticmethod
    def process_pdf_file(pdf_file):
        """
        Process PDF file: save temporarily, analyze, and upload to S3
        Returns: (object_key, notes, temp_file_path)
        """
        try:
            if not pdf_file or pdf_file.filename == '' or not pdf_file.filename.lower().endswith('.pdf'):
                raise ValueError("Valid PDF file is required")
            
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, pdf_file.filename)
            pdf_file.save(file_path)
            
            notes = InstructionalMaterialService.check_missing_sections(file_path)
            
            object_key = InstructionalMaterialService.upload_pdf_to_s3(file_path, pdf_file.filename)
            
            return object_key, notes, file_path
            
        except Exception as e:
            raise Exception(f"PDF processing error: {str(e)}")

    @staticmethod
    def delete_pdf_from_s3(object_key):
        """
        Deletes PDF from S3 using object key
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            s3 = boto3.client('s3')
            s3.delete_object(Bucket=bucket_name, Key=object_key)
            return True
            
        except Exception as e:
            raise Exception(f"S3 delete error: {str(e)}")

    @staticmethod
    def get_s3_url(object_key):
        """Get full S3 URL from object key"""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        if not bucket_name:
            raise ValueError("AWS_BUCKET_NAME not found in environment variables")
        return f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

    @staticmethod
    def check_missing_sections(pdf_path):
        """
        Check an Instructional Materials PDF for missing required sections.
        Uses the local file path directly.
        """
        section_variations = {
            "The VMGOP": ["The VMGOP", "VMGOP"],
            "Preface": ["Preface"], 
            "Table of Contents": ["Table of Contents", "Contents"],
            "The OBE Course Syllabi": ["The OBE Course Syllabi", "OBE Course Syllabi", "Course Syllabus"],
            "References": ["References", "References List", "Reference List"]
        }
        
        try:
            if not os.path.exists(pdf_path):
                return "PDF file not found for analysis"
            
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            text = re.sub(r'\s+', ' ', text).strip()
            
            missing_sections = []
            for section_name, variations in section_variations.items():
                found = False
                for variation in variations:
                    pattern = r'\b' + re.escape(variation) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        found = True
                        break
                
                if not found:
                    missing_sections.append(section_name)
            
            if missing_sections:
                return f"Missing sections: {', '.join(missing_sections)}"
            else:
                return "All required sections are present"
                
        except Exception as e:
            return f"Error processing PDF: {str(e)}"

    @staticmethod
    def create_instructional_material(data, object_key, notes, payload=None):
        """Create a new instructional material with pre-processed PDF data"""
        try:
            # Initialize counters (start at 0)
            counters = {
                'published': 0,
                'utldo_attempt': 0,
                'evaluator_attempt': 0,
                'ai_attempt': 0
            }

            status = data.get('status')
            # Increment according to initial status
            if status in ['Published', 'For UTLDO Evaluation', 'For Evaluator Evaluation', 'For Resubmission', 'For Resubmittion']:
                InstructionalMaterialService._increment_counters_for_status(counters, status, is_model=False)

            version = InstructionalMaterialService._compute_version(
                counters['published'],
                counters['utldo_attempt'],
                counters['evaluator_attempt'],
                counters['ai_attempt']
            )

            print(f"Creating IM with data: {data}")  # Debug
            print(f"Version: {version}")  # Debug

            new_im = InstructionalMaterial(
                im_type=data['im_type'],
                status=status,
                validity=data['validity'],
                version=version,
                s3_link=object_key,
                created_by=data['created_by'],
                updated_by=data['updated_by'],
                notes=notes,
                university_im_id=data.get('university_im_id'),
                service_im_id=data.get('service_im_id'),
                published=counters['published'],
                utldo_attempt=counters['utldo_attempt'],
                evaluator_attempt=counters['evaluator_attempt'],
                ai_attempt=counters['ai_attempt']
            )

            print(f"IM object created: {new_im}")  # Debug
            
            db.session.add(new_im)
            db.session.commit()
            
            print(f"IM committed to database with ID: {new_im.id}")  # Debug
            
            # Send email notification after successful creation
            try:
                # Extract filename from object_key
                filename = os.path.basename(object_key)
                
                # Get user email from payload or data
                user_email = payload.get('email') if payload else data.get('email')
                
                if user_email:
                    EmailService.send_instructional_material_notification(
                        receiver_email=user_email,
                        filename=filename,
                        status=data['status'],
                        notes=notes,
                        action="created"
                    )
            except Exception as e:
                print(f"Email notification failed: {str(e)}")
            
            return new_im

        except Exception as e:
            print(f"Error creating instructional material: {str(e)}")  # Debug
            db.session.rollback()
            raise Exception(f"Create failed: {str(e)}")

    @staticmethod
    def get_all_instructional_materials(page=1):
        """Get all active instructional materials with pagination"""
        per_page = 10
        return InstructionalMaterial.query.filter_by(is_deleted=False).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_instructional_material_by_id(im_id):
        """Get instructional material by ID (including soft-deleted ones)"""
        return db.session.get(InstructionalMaterial, im_id)

    @staticmethod
    def update_instructional_material(im_id, data):
        """Update instructional material data with optional PDF replacement"""
        im = InstructionalMaterial.query.filter_by(id=im_id, is_deleted=False).first()
        object_key = data.get('s3_link')
        notes = data.get('notes')
        if not im:
            return None

        try:
            # Normalize incoming status and define accepted canonical statuses
            incoming_status_raw = data.get('status')
            status_map = {
                'published': 'Published',
                'for utldo evaluation': 'For UTLDO Evaluation',
                'for evaluator evaluation': 'For Evaluator Evaluation',
                'for resubmission': 'For Resubmission',
                'for resubmittion': 'For Resubmission'  # accept common misspelling
            }
            incoming_status = None
            if incoming_status_raw and isinstance(incoming_status_raw, str):
                key = incoming_status_raw.strip().lower()
                incoming_status = status_map.get(key, incoming_status_raw.strip())

            status_changed = False
            incremented = False
            # If status is provided and different -> increment according to the new status
            if incoming_status and incoming_status != im.status:
                InstructionalMaterialService._increment_counters_for_status(im, incoming_status, is_model=True)
                im.status = incoming_status
                status_changed = True
                incremented = True

            # If a new PDF is uploaded and status wasn't changed in this update,
            # but the current status is one of the tracked statuses, increment for that status (only if not already incremented)
            tracked_statuses = set(status_map.values())
            if object_key and (not status_changed):
                # new file uploaded (replacement)
                if im.s3_link and im.s3_link != object_key:
                    # increment based on current status if it's a tracked one
                    if im.status in tracked_statuses and not incremented:
                        InstructionalMaterialService._increment_counters_for_status(im, im.status, is_model=True)
                        incremented = True
                    InstructionalMaterialService.delete_pdf_from_s3(im.s3_link)
                im.s3_link = object_key

            # Only increment when incoming_status equals current status and status wasn't just changed above, and not already incremented
            if incoming_status and incoming_status == im.status and not status_changed and not incremented:
                InstructionalMaterialService._increment_counters_for_status(im, incoming_status, is_model=True)
                incremented = True

            if notes is not None:
                im.notes = notes

            for key, value in data.items():
                if hasattr(im, key) and key not in ['s3_link', 'notes', 'published', 'utldo_attempt', 'evaluator_attempt', 'ai_attempt', 'version']:
                    setattr(im, key, value)

            # Recompute version from counters before commit
            im.version = InstructionalMaterialService._compute_version(
                im.published or 0,
                im.utldo_attempt or 0,
                im.evaluator_attempt or 0,
                im.ai_attempt or 0
            )

            db.session.commit()

            # Send email notification after successful update
            try:
                # Extract filename from object_key (use existing if no new one provided)
                object_key = data.get('s3_link', im.s3_link)
                filename = os.path.basename(object_key)
                
                # Get user email
                user_email = data.get('email')
                
                EmailService.send_instructional_material_notification(
                    receiver_email=user_email,
                    filename=filename,
                    status=im.status,  # Use the updated status
                    notes=data.get('notes', im.notes),
                    action="updated"
                )
            except Exception as e:
                print(f"Email notification failed: {str(e)}")
                # Don't raise the error as we don't want to fail the main operation
            return im

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Update failed: {str(e)}")

    @staticmethod
    def soft_delete_instructional_material(im_id):
        """Mark instructional material as deleted (soft delete)"""
        im = InstructionalMaterial.query.filter_by(id=im_id, is_deleted=False).first()
        if not im:
            return False
        
        im.is_deleted = True
        db.session.commit()
        return True

    @staticmethod
    def get_deleted_instructional_materials(page=1):
        """Get all deleted instructional materials with pagination"""
        per_page = 10
        return InstructionalMaterial.query.filter_by(is_deleted=True).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def restore_instructional_material(im_id):
        """Restore a soft-deleted instructional material"""
        im = InstructionalMaterial.query.filter_by(id=im_id, is_deleted=True).first()
        if not im:
            return False
        
        im.is_deleted = False
        db.session.commit()
        return True

    @staticmethod
    def download_pdf(object_key, download_path=None):
        """
        Download PDF from S3 using object key
        """
        try:       
            if not object_key:
                raise ValueError("Object key is required")
            
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            filename = os.path.basename(object_key)
            
            if not download_path:
                download_path = os.path.join(os.path.expanduser('~'), 'Downloads', filename)
            else:
                if os.path.isdir(download_path):
                    download_path = os.path.join(download_path, filename)
            
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            s3 = boto3.client('s3')
            s3.download_file(bucket_name, object_key, download_path)
            
            return download_path
            
        except Exception as e:
            raise Exception(f"PDF download error: {str(e)}")

    @staticmethod
    def generate_presigned_url(object_key, expires_in=900):
        """Generate a presigned GET URL for the PDF (default 15 minutes) forcing inline render."""
        try:
            if not object_key:
                raise ValueError("Object key required")
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            s3 = boto3.client('s3')
            params = {
                'Bucket': bucket_name,
                'Key': object_key,
                'ResponseContentType': 'application/pdf',
                'ResponseContentDisposition': f'inline; filename="{os.path.basename(object_key)}"'
            }
            url = s3.generate_presigned_url('get_object', Params=params, ExpiresIn=expires_in)
            return url
        except Exception as e:
            raise Exception(f"Presign error: {str(e)}")
        
    @staticmethod
    def get_instructional_materials_for_evaluator(page=1):
        """
        Get instructional materials with status 'For Evaluator Evaluation'
        """
        per_page = 10
        return InstructionalMaterial.query.filter_by(
            status='For Evaluator Evaluation', 
            is_deleted=False
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_instructional_materials_for_utldo(page=1):
        """
        Get instructional materials with status 'For UTLDO Evaluation'
        """
        per_page = 10
        return InstructionalMaterial.query.filter_by(
            status='For UTLDO Evaluation', 
            is_deleted=False
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )

    @staticmethod
    def get_instructional_materials_for_certification(page=1):
        """
        Get instructional materials with status 'For Certification'
        """
        per_page = 10
        return InstructionalMaterial.query.filter_by(
            status='For Certification',
            is_deleted=False
        ).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )