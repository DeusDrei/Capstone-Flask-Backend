import os
import base64
import boto3
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from email.mime.application import MIMEApplication

load_dotenv()

class EmailService:
    @staticmethod
    def send_instructional_material_notification(receiver_email, filename, status, notes, action="created"):
        """
        Send email notification for instructional material actions using Brevo API
        
        Args:
            receiver_email: Email address of the recipient
            filename: Name of the instructional material file
            status: Current status of the material
            notes: Additional notes/comments
            action: Either "created" or "updated"
        """
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            brevo_api_key = os.getenv('BREVO_API_KEY')

            # normalize recipients
            if isinstance(receiver_email, str):
                recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
            elif isinstance(receiver_email, (list, tuple)):
                recipients = [e.strip() for e in receiver_email if e and e.strip()]
            else:
                raise ValueError("receiver_email must be a string or list/tuple of emails")
            if not recipients:
                raise ValueError("no valid recipient emails provided")

            if not sender_email or not brevo_api_key:
                raise ValueError("EMAIL_SENDER or BREVO_API_KEY not configured")

            subject = f"Instructional Material {action.capitalize()}: {filename}"
            
            html_body = f"""
            <html>
            <body>
                <h2>Instructional Material Notification</h2>
                <p>Your instructional material has been {action} successfully.</p>
                <table border="0" cellpadding="5">
                    <tr><td><strong>Instructional Material ID:</strong></td><td>{filename}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{status}</td></tr>
                    <tr><td><strong>Notes:</strong></td><td>{notes or 'No additional notes'}</td></tr>
                </table>
                <br>
                <p>Thank you for using our instructional materials system.</p>
            </body>
            </html>
            """
            
            # Send email using Brevo
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': brevo_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'sender': {'email': sender_email},
                    'to': [{'email': email} for email in recipients],
                    'subject': subject,
                    'htmlContent': html_body
                }
            )
            
            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Brevo API error: {response.text}")
            
        except Exception as e:
            print(f"Brevo email sending failed: {str(e)}. Trying Gmail SMTP fallback...")
            if 'recipients' not in locals():
                if isinstance(receiver_email, str):
                    recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
                elif isinstance(receiver_email, (list, tuple)):
                    recipients = [e.strip() for e in receiver_email if e and e.strip()]
                else:
                    return False
            return EmailService._send_via_gmail(recipients, filename, status, notes, action)
    
    @staticmethod
    def _send_via_gmail(recipients, filename, status, notes, action):
        """Fallback to Gmail SMTP when SES fails. `recipients` is a list of addresses."""
        print(f"Gmail fallback called for {recipients}")
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                print("Gmail SMTP not configured")
                return False
            
            subject = f"Instructional Material {action.capitalize()}: {filename}"
            
            html = f"""
            <html>
            <body>
                <h2>Instructional Material Notification</h2>
                <p>Your instructional material has been {action} successfully.</p>
                <table border="0" cellpadding="5">
                    <tr><td><strong>Filename:</strong></td><td>{filename}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{status}</td></tr>
                    <tr><td><strong>Notes:</strong></td><td>{notes or 'No additional notes'}</td></tr>
                </table>
                <br>
                <p>Thank you for using our instructional materials system.</p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            to_header = ", ".join(recipients)
            msg['To'] = to_header
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                # sendmail accepts a list of recipients
                server.sendmail(sender_email, recipients, msg.as_string())
            
            print("Email sent successfully via Gmail SMTP")
            return True
            
        except Exception as e:
            print(f"Gmail SMTP fallback also failed: {str(e)}")
            return False

    @staticmethod
    def send_deadline_notification(receiver_email, im_id, days_remaining, due_date, subject_name=None):
        """
        Send deadline notification email for instructional materials
        
        Args:
            receiver_email: Email address of the recipient
            im_id: Instructional material ID
            days_remaining: Number of days until deadline
            due_date: The due date
            subject_name: Optional subject name
        """
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            brevo_api_key = os.getenv('BREVO_API_KEY')

            # normalize recipients
            if isinstance(receiver_email, str):
                recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
            elif isinstance(receiver_email, (list, tuple)):
                recipients = [e.strip() for e in receiver_email if e and e.strip()]
            else:
                raise ValueError("receiver_email must be a string or list/tuple of emails")
            if not recipients:
                raise ValueError("no valid recipient emails provided")

            if not sender_email or not brevo_api_key:
                raise ValueError("EMAIL_SENDER or BREVO_API_KEY not configured")

            subject = f"Deadline Reminder: Instructional Material Due in {days_remaining} Day(s)"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h3 style="color:#d32f2f;">Deadline Reminder</h3>
                <p><strong>IM-{im_id}</strong> {f'({subject_name})' if subject_name else ''} is due in <strong>{days_remaining} day(s)</strong></p>
                <p>Due Date: {due_date}</p>
                <p>Submit before deadline to avoid delays.</p>
            </body>
            </html>
            """
            
            # Send email using Brevo
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': brevo_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'sender': {'email': sender_email},
                    'to': [{'email': email} for email in recipients],
                    'subject': subject,
                    'htmlContent': html_body
                }
            )
            
            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Brevo API error: {response.text}")
            
        except Exception as e:
            print(f"Brevo deadline email failed: {str(e)}. Trying Gmail SMTP fallback...")
            if 'recipients' not in locals():
                if isinstance(receiver_email, str):
                    recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
                elif isinstance(receiver_email, (list, tuple)):
                    recipients = [e.strip() for e in receiver_email if e and e.strip()]
                else:
                    return False
            return EmailService._send_deadline_via_gmail(recipients, im_id, days_remaining, due_date, subject_name)
    
    @staticmethod
    def _send_deadline_via_gmail(recipients, im_id, days_remaining, due_date, subject_name):
        """Fallback to Gmail SMTP for deadline notifications"""
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                print("Gmail SMTP not configured")
                return False
            
            subject = f"Deadline Reminder: Instructional Material Due in {days_remaining} Day(s)"
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #222; line-height:1.4;">
                <h2 style="color:#d32f2f;">⚠️ Deadline Reminder</h2>
                <p>This is a friendly reminder that your instructional material is due soon.</p>
                <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Instructional Material ID:</strong> IM-{im_id}</p>
                    {f'<p><strong>Subject:</strong> {subject_name}</p>' if subject_name else ''}
                    <p><strong>Due Date:</strong> {due_date}</p>
                    <p><strong>Days Remaining:</strong> <span style="color: #d32f2f; font-weight: bold;">{days_remaining} day(s)</span></p>
                </div>
                <p>Please ensure you submit your instructional material before the deadline.</p>
                <p>Best regards,<br>Instructional Materials Management System</p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Gmail SMTP deadline notification failed: {str(e)}")
            return False

    @staticmethod
    def send_file_to_recipients(receiver_email, file_bytes, filename, subject=None, html_body=None, text_body=None):
        """Send a file attachment to multiple recipients. Tries Brevo first, falls back to SMTP.

        receiver_email: string CSV or list/tuple of addresses
        file_bytes: bytes of the file to attach
        filename: filename for attachment
        subject: email subject (optional)
        html_body / text_body: optional bodies
        """
        # normalize recipients
        if isinstance(receiver_email, str):
            recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
        elif isinstance(receiver_email, (list, tuple)):
            recipients = [e.strip() for e in receiver_email if e and e.strip()]
        else:
            raise ValueError("receiver_email must be a string or list/tuple of emails")
        if not recipients:
            raise ValueError("no valid recipient emails provided")

        sender_email = os.getenv('EMAIL_SENDER')
        brevo_api_key = os.getenv('BREVO_API_KEY')
        if not sender_email:
            raise ValueError("EMAIL_SENDER not configured")

        subj = subject or f"File from Instructional Materials: {filename}"
        html_content = html_body or "<p>Please find the attached file.</p>"

        # Try Brevo with attachment
        if brevo_api_key:
            try:
                # Encode file as base64
                file_base64 = base64.b64encode(file_bytes).decode('utf-8')
                
                response = requests.post(
                    'https://api.brevo.com/v3/smtp/email',
                    headers={
                        'api-key': brevo_api_key,
                        'Content-Type': 'application/json'
                    },
                    json={
                        'sender': {'email': sender_email},
                        'to': [{'email': email} for email in recipients],
                        'subject': subj,
                        'htmlContent': html_content,
                        'attachment': [{
                            'content': file_base64,
                            'name': filename
                        }]
                    }
                )
                
                if response.status_code == 201:
                    return True
                else:
                    print(f"Brevo attachment send failed: {response.text}. Falling back to SMTP.")
            except Exception as e:
                print(f"Brevo attachment error: {str(e)}. Falling back to SMTP.")

        # SMTP fallback
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            if not all([smtp_server, smtp_username, smtp_password]):
                print("SMTP not configured for attachment fallback")
                return False

            msg = MIMEMultipart('mixed')
            msg['Subject'] = subj
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)

            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            elif text_body:
                msg.attach(MIMEText(text_body, 'plain'))

            part = MIMEApplication(file_bytes)
            part.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(part)

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            return True
        except Exception as e:
            print(f"SMTP send for attachment failed: {str(e)}")
            return False

    @staticmethod
    def send_past_due_notification(receiver_email, im_id, due_date, subject_name=None):
        """
        Send past due notification email for instructional materials
        
        Args:
            receiver_email: Email address of the recipient
            im_id: Instructional material ID
            due_date: The original due date
            subject_name: Optional subject name
        """
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            brevo_api_key = os.getenv('BREVO_API_KEY')

            # normalize recipients
            if isinstance(receiver_email, str):
                recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
            elif isinstance(receiver_email, (list, tuple)):
                recipients = [e.strip() for e in receiver_email if e and e.strip()]
            else:
                raise ValueError("receiver_email must be a string or list/tuple of emails")
            if not recipients:
                raise ValueError("no valid recipient emails provided")

            if not sender_email or not brevo_api_key:
                raise ValueError("EMAIL_SENDER or BREVO_API_KEY not configured")

            subject = f"PAST DUE: Instructional Material Overdue"
            
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h3 style="color:#d32f2f;">⚠️ PAST DUE NOTICE</h3>
                <p><strong>IM-{im_id}</strong> {f'({subject_name})' if subject_name else ''} is <strong style="color:#d32f2f;">PAST DUE</strong></p>
                <p>Original Due Date: {due_date}</p>
                <p>Please submit immediately to avoid further delays.</p>
            </body>
            </html>
            """
            
            # Send email using Brevo
            response = requests.post(
                'https://api.brevo.com/v3/smtp/email',
                headers={
                    'api-key': brevo_api_key,
                    'Content-Type': 'application/json'
                },
                json={
                    'sender': {'email': sender_email},
                    'to': [{'email': email} for email in recipients],
                    'subject': subject,
                    'htmlContent': html_body
                }
            )
            
            if response.status_code == 201:
                return True
            else:
                raise Exception(f"Brevo API error: {response.text}")
            
        except Exception as e:
            print(f"Brevo past due email failed: {str(e)}. Trying Gmail SMTP fallback...")
            if 'recipients' not in locals():
                if isinstance(receiver_email, str):
                    recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
                elif isinstance(receiver_email, (list, tuple)):
                    recipients = [e.strip() for e in receiver_email if e and e.strip()]
                else:
                    return False
            return EmailService._send_past_due_via_gmail(recipients, im_id, due_date, subject_name)
    
    @staticmethod
    def _send_past_due_via_gmail(recipients, im_id, due_date, subject_name):
        """Fallback to Gmail SMTP for past due notifications"""
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not all([smtp_server, smtp_username, smtp_password]):
                print("Gmail SMTP not configured")
                return False
            
            subject = f"PAST DUE: Instructional Material Overdue"
            
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #222; line-height:1.4;">
                <h2 style="color:#d32f2f;">🚨 PAST DUE NOTICE</h2>
                <p>This is an urgent notice that your instructional material is overdue.</p>
                <div style="background-color: #ffebee; border: 1px solid #f44336; padding: 15px; border-radius: 5px; margin: 15px 0;">
                    <p><strong>Instructional Material ID:</strong> IM-{im_id}</p>
                    {f'<p><strong>Subject:</strong> {subject_name}</p>' if subject_name else ''}
                    <p><strong>Original Due Date:</strong> {due_date}</p>
                    <p><strong>Status:</strong> <span style="color: #d32f2f; font-weight: bold;">PAST DUE</span></p>
                </div>
                <p>Please submit your instructional material immediately to avoid further delays.</p>
                <p>Best regards,<br>Instructional Materials Management System</p>
            </body>
            </html>
            """
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = ", ".join(recipients)
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Gmail SMTP past due notification failed: {str(e)}")
            return False