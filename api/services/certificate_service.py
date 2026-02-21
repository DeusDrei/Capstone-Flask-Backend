import os
import json
import subprocess
import shutil
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
    def generate_certificates(im_id, template_path=None):
        """Generate certificates for all authors of an IM.
        
        Args:
            im_id: The instructional material ID.
            template_path: Optional path to a custom DOCX template. If not
                provided the default template is downloaded from S3.
        """
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
        
        # Download template from S3 only if a custom one wasn't supplied
        owns_template = template_path is None
        if owns_template:
            template_path = CertificateService._download_template()
        
        certificates = []
        try:
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
        finally:
            # Cleanup template only if we downloaded it
            if owns_template and os.path.exists(template_path):
                os.remove(template_path)
        
        return certificates
    
    @staticmethod
    def generate_certificate_for_user(im_id, user_id, template_path=None):
        """Generate and send a certificate for a single author only.
        
        Useful for post-publish catch-up when an author was missed.
        """
        im = InstructionalMaterial.query.get(im_id)
        if not im:
            raise ValueError("Instructional Material not found")
        
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        college_name, course_code, course_title, program_name = CertificateService._get_im_details(im)
        semester = im.semester or "N/A"
        academic_year = CertificateService._format_academic_year(im.validity)
        date_issued = date.today().strftime("%B %d, %Y")
        
        owns_template = template_path is None
        if owns_template:
            template_path = CertificateService._download_template()
        
        try:
            cert_data = CertificateService._generate_certificate(
                template_path, user, college_name, course_code, course_title,
                program_name, semester, academic_year, date_issued, im_id
            )
        finally:
            if owns_template and os.path.exists(template_path):
                os.remove(template_path)
        
        return cert_data

    @staticmethod
    def get_certificates_for_user(user_id):
        """Return all certificates issued to a user, enriched with IM details."""
        from api.models.im_certificates import IMCertificate
        from api.models.instructionalmaterials import InstructionalMaterial
        
        certs = IMCertificate.query.filter_by(user_id=user_id).order_by(IMCertificate.date_issued.desc()).all()
        result = []
        for cert in certs:
            im = InstructionalMaterial.query.get(cert.im_id)
            college_name, course_code, course_title, _ = CertificateService._get_im_details(im) if im else ('N/A', 'N/A', 'N/A', 'N/A')
            result.append({
                'id': cert.id,
                'qr_id': cert.qr_id,
                'im_id': cert.im_id,
                'user_id': cert.user_id,
                's3_link': CertificateService._try_presign_pdf(cert.qr_id),
                's3_link_docx': CertificateService._resolve_docx_link(cert.qr_id),
                'date_issued': cert.date_issued.isoformat() if cert.date_issued else None,
                'created_at': cert.created_at.isoformat() if cert.created_at else None,
                'subject_code': course_code,
                'subject_title': course_title,
                'im_version': im.version if im else None,
            })
        return result

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
        
        # Save DOCX to temp file
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
        doc.save(temp_output.name)
        temp_output.close()

        # Convert DOCX → PDF (best-effort; won't crash if unavailable)
        pdf_path = CertificateService._convert_docx_to_pdf(temp_output.name)

        # Upload DOCX to S3
        docx_key = f"generated-certificates/{cert.qr_id}.docx"
        docx_s3_link = CertificateService._upload_to_s3(temp_output.name, docx_key)

        # Upload PDF to S3 if conversion succeeded
        pdf_s3_link = None
        if pdf_path:
            pdf_key = f"generated-certificates/{cert.qr_id}.pdf"
            pdf_s3_link = CertificateService._upload_to_s3(pdf_path, pdf_key)

        # Persist the DOCX key as the stable s3_link (PDF can be re-derived from qr_id)
        cert.s3_link = docx_key
        db.session.commit()

        # Email: one message with DOCX always attached; PDF too if available
        today = date.today()
        try:
            valid_until = today.replace(year=today.year + 5).strftime("%B %d, %Y")
        except ValueError:
            valid_until = date(today.year + 5, 2, 28).strftime("%B %d, %Y")

        email_subject = f"Certificate of Appreciation \u2014 {course_code} ({academic_year})"
        email_body = f"""
<p>Dear {author_name},</p>

<p>On behalf of the institution, we are pleased to present you with a
<strong>Certificate of Appreciation</strong> in recognition of your valuable contribution
in developing an instructional material. The details of your certificate are as follows:</p>

<table style="border-collapse:collapse;font-size:14px;margin:12px 0;">
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Certificate ID</td>
    <td style="padding:5px 0;">{cert.qr_id}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Subject Code</td>
    <td style="padding:5px 0;">{course_code}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Subject Title</td>
    <td style="padding:5px 0;">{course_title}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Program</td>
    <td style="padding:5px 0;">{program_name}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">College</td>
    <td style="padding:5px 0;">{college_name}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Semester</td>
    <td style="padding:5px 0;">{semester}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Academic Year</td>
    <td style="padding:5px 0;">{academic_year}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Date Issued</td>
    <td style="padding:5px 0;">{date_issued}</td>
  </tr>
  <tr>
    <td style="padding:5px 20px 5px 0;font-weight:bold;white-space:nowrap;color:#555;">Valid Until</td>
    <td style="padding:5px 0;">{valid_until}</td>
  </tr>
</table>

<p>Your certificate is attached to this email in DOCX and PDF formats.
Please retain a copy for your personal records. A QR code is embedded in the
certificate for quick verification.</p>

<p>We truly appreciate your dedication and efforts in enhancing the quality of
instruction. Your work reflects a deep commitment to academic excellence and to
the growth of your students.</p>

<p>Congratulations, and thank you.</p>

<p>Sincerely,<br>
<strong>Instructional Materials Management System (IMMS)</strong></p>
"""
        attachments = [(open(temp_output.name, 'rb').read(), f"{cert.qr_id}.docx")]
        if pdf_path and os.path.exists(pdf_path):
            attachments.append((open(pdf_path, 'rb').read(), f"{cert.qr_id}.pdf"))
        EmailService.send_files_to_recipients(
            user.email,
            attachments,
            subject=email_subject,
            html_body=email_body,
        )

        # Cleanup temp files
        os.remove(temp_output.name)
        if pdf_path:
            try:
                shutil.rmtree(os.path.dirname(pdf_path), ignore_errors=True)
            except Exception:
                pass

        return {
            'qr_id': cert.qr_id,
            'user_id': user.id,
            'author_name': author_name,
            's3_link': pdf_s3_link,           # PDF presigned URL, or None if conversion failed
            's3_link_docx': docx_s3_link,     # DOCX presigned URL, always present
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
    def _upload_to_s3(file_path, s3_key):
        """Upload a file to S3 and return a presigned URL valid for 7 days."""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        s3 = boto3.client('s3')
        s3.upload_file(file_path, bucket_name, s3_key)
        presigned_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': s3_key},
            ExpiresIn=604800  # 7 days
        )
        return presigned_url

    @staticmethod
    def _convert_docx_to_pdf(docx_path):
        """Convert a DOCX file to PDF.
        Tries docx2pdf first (uses Word on Windows, LibreOffice on Linux/macOS),
        then falls back to a raw LibreOffice subprocess.
        Returns the path to the generated PDF, or None if both methods fail.
        """
        out_dir = tempfile.mkdtemp()
        base = os.path.splitext(os.path.basename(docx_path))[0]
        pdf_path = os.path.join(out_dir, base + '.pdf')

        # --- Method 1: docx2pdf (cross-platform) ---
        try:
            import pythoncom  # type: ignore
            from docx2pdf import convert as d2p_convert  # type: ignore
            pythoncom.CoInitialize()
            try:
                d2p_convert(docx_path, pdf_path)
            finally:
                pythoncom.CoUninitialize()
            if os.path.exists(pdf_path):
                return pdf_path
        except Exception as e:
            print(f"[cert] docx2pdf failed ({e}), trying LibreOffice…")

        # --- Method 2: LibreOffice headless subprocess ---
        try:
            subprocess.run(
                [
                    'libreoffice', '--headless',
                    '--convert-to', 'pdf',
                    '--outdir', out_dir,
                    docx_path,
                ],
                check=True,
                capture_output=True,
                timeout=120,
            )
            lo_pdf = os.path.join(out_dir, base + '.pdf')
            if os.path.exists(lo_pdf):
                return lo_pdf
        except Exception as e:
            print(f"[cert] LibreOffice fallback also failed ({e})")

        shutil.rmtree(out_dir, ignore_errors=True)
        return None  # caller must handle gracefully

    @staticmethod
    def _key_exists_in_s3(key):
        """Return True if the given S3 key exists in the bucket."""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        try:
            boto3.client('s3').head_object(Bucket=bucket_name, Key=key)
            return True
        except Exception:
            return False

    @staticmethod
    def _try_presign_pdf(qr_id):
        """Return a presigned URL for the PDF of this cert, or None if it doesn't exist yet."""
        key = f"generated-certificates/{qr_id}.pdf"
        if not CertificateService._key_exists_in_s3(key):
            return None
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        return boto3.client('s3').generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': key},
            ExpiresIn=604800
        )

    @staticmethod
    def _resolve_s3_link(raw_link):
        """Ensure raw_link is a usable HTTPS URL.
        - Already a URL → return as-is.
        - Legacy DOCX key → rewrite to .pdf key before presigning.
        - Other S3 key → presign directly.
        """
        if not raw_link:
            return raw_link
        if raw_link.startswith('http://') or raw_link.startswith('https://'):
            return raw_link
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        key = raw_link
        if key.endswith('.docx'):
            key = key[:-5] + '.pdf'
        try:
            s3 = boto3.client('s3')
            return s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=604800
            )
        except Exception:
            return raw_link

    @staticmethod
    def _resolve_docx_link(qr_id):
        """Generate a fresh presigned URL for the DOCX of a given cert (by qr_id)."""
        bucket_name = os.getenv('AWS_BUCKET_NAME')
        key = f"generated-certificates/{qr_id}.docx"
        try:
            s3 = boto3.client('s3')
            return s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': key},
                ExpiresIn=604800
            )
        except Exception:
            return None
