import os
import boto3
import smtplib
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
        Send email notification for instructional material actions using AWS SES
        
        Args:
            receiver_email: Email address of the recipient
            filename: Name of the instructional material file
            status: Current status of the material
            notes: Additional notes/comments
            action: Either "created" or "updated"
        """
        try:
            sender_email = os.getenv('EMAIL_SENDER')
            aws_region = os.getenv('AWS_REGION')

            # normalize recipients: accept single string, comma-separated string, or list/tuple
            if isinstance(receiver_email, str):
                recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
            elif isinstance(receiver_email, (list, tuple)):
                recipients = [e.strip() for e in receiver_email if e and e.strip()]
            else:
                raise ValueError("receiver_email must be a string or list/tuple of emails")
            if not recipients:
                raise ValueError("no valid recipient emails provided")

            if not sender_email or not aws_region:
                raise ValueError("EMAIL_SENDER or AWS_REGION not configured")

            subject = f"Instructional Material {action.capitalize()}: {filename}"
            
            # HTML email content
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
            
            # Plain text version
            text_body = f"""
            Instructional Material Notification
            
            Your instructional material has been {action} successfully.
            
            Filename: {filename}
            Status: {status}
            Notes: {notes or 'No additional notes'}
            
            Thank you for using our instructional materials system.
            """
            
            # Send email using SES
            ses_client = boto3.client('ses', region_name=aws_region)

            # SES accepts a list of addresses
            response = ses_client.send_email(
                Destination={'ToAddresses': recipients},
                Message={
                    'Body': {
                        'Html': {'Charset': 'UTF-8', 'Data': html_body},
                        'Text': {'Charset': 'UTF-8', 'Data': text_body}
                    },
                    'Subject': {'Charset': 'UTF-8', 'Data': subject}
                },
                Source=sender_email
            )
            
            return True
            
        except ClientError as e:
            print(f"SES email sending failed: {e.response['Error']['Message']}. Trying Gmail SMTP fallback...")
            return EmailService._send_via_gmail(recipients, filename, status, notes, action)
        except Exception as e:
            print(f"SES email sending failed: {str(e)}. Trying Gmail SMTP fallback...")
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
    def send_file_to_recipients(receiver_email, file_bytes, filename, subject=None, html_body=None, text_body=None):
        """Send a file attachment to multiple recipients. Tries SES Raw first, falls back to SMTP.

        receiver_email: string CSV or list/tuple of addresses
        file_bytes: bytes of the file to attach
        filename: filename for attachment
        subject: email subject (optional)
        html_body / text_body: optional bodies
        """
        # normalize recipients same as other methods
        if isinstance(receiver_email, str):
            recipients = [e.strip() for e in receiver_email.split(",") if e.strip()]
        elif isinstance(receiver_email, (list, tuple)):
            recipients = [e.strip() for e in receiver_email if e and e.strip()]
        else:
            raise ValueError("receiver_email must be a string or list/tuple of emails")
        if not recipients:
            raise ValueError("no valid recipient emails provided")

        sender_email = os.getenv('EMAIL_SENDER')
        aws_region = os.getenv('AWS_REGION')
        if not sender_email:
            raise ValueError("EMAIL_SENDER not configured")

        subj = subject or f"File from Instructional Materials: {filename}"

        # build MIME message with attachment
        msg = MIMEMultipart('mixed')
        msg['Subject'] = subj
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)

        # alternative (text/html)
        alt = MIMEMultipart('alternative')
        if text_body:
            alt.attach(MIMEText(text_body, 'plain'))
        if html_body:
            alt.attach(MIMEText(html_body, 'html'))
        if text_body or html_body:
            msg.attach(alt)

        # attach file
        part = MIMEApplication(file_bytes)
        part.add_header('Content-Disposition', 'attachment', filename=filename)
        msg.attach(part)

        # Try SES Raw
        try:
            if aws_region:
                ses = boto3.client('ses', region_name=aws_region)
                # send_raw_email supports RawMessage and Destinations
                ses.send_raw_email(Source=sender_email, Destinations=recipients, RawMessage={'Data': msg.as_string()})
                return True
        except ClientError as e:
            print(f"SES raw send failed: {e.response.get('Error', {}).get('Message')}. Falling back to SMTP.")
        except Exception as e:
            print(f"SES raw send error: {str(e)}. Falling back to SMTP.")

        # SMTP fallback
        try:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME')
            smtp_password = os.getenv('SMTP_PASSWORD')
            if not all([smtp_server, smtp_username, smtp_password]):
                print("SMTP not configured for attachment fallback")
                return False

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, recipients, msg.as_string())
            return True
        except Exception as e:
            print(f"SMTP send for attachment failed: {str(e)}")
            return False