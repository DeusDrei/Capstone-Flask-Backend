import os
import json
import qrcode
import tempfile
import boto3
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Inches
from api.extensions import db
from api.models.im_certificates import IMCertificate
from api.models.instructionalmaterials import InstructionalMaterial
from api.models.authors import Author
from api.models.users import User
from api.services.email_service import EmailService

class CertificateService:
    @staticmethod
    def generate_certificates(im_id):
        """Generate certificates for all authors of an IM"""
        im = InstructionalMaterial.query.get(im_id)
        if not im:
            raise ValueError("Instructional Material not found")
        
        # Get all authors
        authors = Author.query.filter_by(im_id=im_id).all()
        if not authors:
            raise ValueError("No authors found for this IM")
        
        # Get IM details
        college_name, course_code, course_title, program_name = CertificateService._get_im_details(im)
        semester = im.semester or "N/A"
        academic_year = CertificateService._format_academic_year(im.validity)
        date_issued = date.today().strftime("%B %d, %Y")
        
        # Download template from S3
        template_path = CertificateService._download_template()
        
        certificates = []
        for author in authors:
            user = User.query.get(author.user_id)
            if not user:
                continue
            
            # Generate certificate
            cert_data = CertificateService._generate_certificate(
                template_path, user, college_name, course_code, course_title,
                program_name, semester, academic_year, date_issued, im_id
            )
            
            certificates.append(cert_data)
        
        # Cleanup template
        if os.path.exists(template_path):
            os.remove(template_path)
        
        return certificates
    
    @staticmethod
    def _get_im_details(im):
        """Extract college, course, and program details from IM"""
        if im.university_im_id and im.university_im:
            uni = im.university_im
            college_name = uni.college.name if uni.college else "N/A"
            course_code = uni.subject.code if uni.subject else "N/A"
            course_title = uni.subject.name if uni.subject else "N/A"
            program_name = uni.department.name if uni.department else "N/A"
        elif im.service_im_id and im.service_im:
            svc = im.service_im
            college_name = svc.college.name if svc.college else "N/A"
            course_code = svc.subject.code if svc.subject else "N/A"
            course_title = svc.subject.name if svc.subject else "N/A"
            program_name = "Service Course"
        else:
            college_name = course_code = course_title = program_name = "N/A"
        
        return college_name, course_code, course_title, program_name
    
    @staticmethod
    def _format_academic_year(validity):
        """Convert validity to academic year format (e.g., 2025 -> 2025-2026)"""
        try:
            year = int(validity)
            return f"{year}-{year + 1}"
        except:
            return validity
    
    @staticmethod
    def _download_template():
        """Download certificate template from S3"""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3_key = 'requirements/cert-of-appreciation.docx'
        
        s3 = boto3.client('s3')
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        temp_file.close()
        
        s3.download_file(bucket_name, s3_key, temp_file.name)
        return temp_file.name
    
    @staticmethod
    def _generate_certificate(template_path, user, college_name, course_code, course_title,
                             program_name, semester, academic_year, date_issued, im_id):
        """Generate a single certificate for a user"""
        # Load template
        doc = Document(template_path)
        
        # Build author name
        author_name = f"{user.first_name}"
        if user.middle_name:
            author_name += f" {user.middle_name}"
        author_name += f" {user.last_name}"
        
        author_rank = user.rank or ""
        
        # Replace placeholders in paragraphs
        replacements = {
            '{{COLLEGE_NAME}}': college_name,
            '{{COURSE_CODE}}': course_code,
            '{{COURSE_TITLE}}': course_title,
            '{{AUTHOR_RANK}}': author_rank,
            '{{AUTHOR_NAME}}': author_name,
            '{{PROGRAM_NAME}}': program_name,
            '{{SEMESTER}}': semester,
            '{{ACADEMIC_YEAR}}': academic_year,
            '{{DATE_ISSUED}}': date_issued
        }
        
        for paragraph in doc.paragraphs:
            CertificateService._replace_text(paragraph, replacements)
        
        # Replace placeholders in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        CertificateService._replace_text(paragraph, replacements)
        
        # Create certificate record to get ID
        cert = IMCertificate(
            qr_id=f"CERT-TEMP",
            im_id=im_id,
            user_id=user.id,
            s3_link="",
            date_issued=date.today()
        )
        db.session.add(cert)
        db.session.flush()
        
        # Update QR ID with actual ID
        cert.qr_id = f"CERT-{cert.id}"
        
        # Generate QR code
        qr_data = {
            "qr_id": cert.qr_id,
            "author_name": author_name,
            "im_id": im_id,
            "date_issued": date_issued
        }
        qr_img = CertificateService._generate_qr_code(json.dumps(qr_data))
        
        # Add QR code to document (bottom right)
        CertificateService._add_qr_to_document(doc, qr_img)
        
        # Save to temp file
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_output.name)
        temp_output.close()
        
        # Upload to S3
        s3_link = CertificateService._upload_to_s3(temp_output.name, cert.qr_id)
        cert.s3_link = s3_link
        db.session.commit()
        
        # Send email
        EmailService.send_file_to_recipients(
            user.email,
            open(temp_output.name, 'rb').read(),
            f"{cert.qr_id}.docx",
            subject=f"Certificate of Submission - {course_code}",
            html_body=f"<p>Dear {author_name},</p><p>Please find attached your Certificate of Submission for {course_code}: {course_title}.</p>"
        )
        
        # Cleanup
        os.remove(temp_output.name)
        
        return {
            'qr_id': cert.qr_id,
            'user_id': user.id,
            'author_name': author_name,
            's3_link': s3_link
        }
    
    @staticmethod
    def _replace_text(paragraph, replacements):
        """Replace text in paragraph"""
        for key, value in replacements.items():
            if key in paragraph.text:
                for run in paragraph.runs:
                    run.text = run.text.replace(key, value)
    
    @staticmethod
    def _generate_qr_code(data):
        """Generate QR code image"""
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_bytes = BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        return img_bytes
    
    @staticmethod
    def _add_qr_to_document(doc, qr_img):
        """Add QR code by replacing [QR CODE SPACE] placeholder"""
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        
        # Search in paragraphs
        for paragraph in doc.paragraphs:
            if '[QR CODE SPACE]' in paragraph.text:
                paragraph.clear()
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = paragraph.add_run()
                run.add_picture(qr_img, width=Inches(1.5))
                return
        
        # Search in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if '[QR CODE SPACE]' in paragraph.text:
                            paragraph.clear()
                            paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                            run = paragraph.add_run()
                            run.add_picture(qr_img, width=Inches(1.5))
                            return
    
    @staticmethod
    def _upload_to_s3(file_path, qr_id):
        """Upload certificate to S3"""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3_key = f"generated-certificates/{qr_id}.docx"
        
        s3 = boto3.client('s3')
        s3.upload_file(file_path, bucket_name, s3_key)
        
        return s3_key
