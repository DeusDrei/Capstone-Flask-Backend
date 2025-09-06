import os
import boto3
import pdfplumber
import re
from dotenv import load_dotenv
from api.extensions import db
from api.models.instructionalmaterials import InstructionalMaterial
import tempfile
import uuid

load_dotenv()

class InstructionalMaterialService:
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
            s3.upload_file(file_path, bucket_name, s3_key)
            
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
    def create_instructional_material(data, object_key, notes):
        """Create a new instructional material with pre-processed PDF data"""
        new_im = InstructionalMaterial(
            im_type=data['im_type'],
            status=data['status'],
            validity=data['validity'],
            version=data['version'],
            s3_link=object_key,
            created_by=data['created_by'],
            updated_by=data['updated_by'],
            notes=notes,
            university_im_id=data.get('university_im_id'),
            service_im_id=data.get('service_im_id')
        )
        
        db.session.add(new_im)
        db.session.commit()
        return new_im

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
            if object_key:
                if im.s3_link and im.s3_link != object_key:
                    InstructionalMaterialService.delete_pdf_from_s3(im.s3_link)

                im.s3_link = object_key

            if notes is not None:
                im.notes = notes

            for key, value in data.items():
                if hasattr(im, key) and key not in ['s3_link', 'notes']:
                    setattr(im, key, value)
            
            db.session.commit()
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