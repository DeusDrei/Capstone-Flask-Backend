import os
import boto3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from botocore.exceptions import ClientError
from dotenv import load_dotenv

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
                    <tr><td><strong>Filename:</strong></td><td>{filename}</td></tr>
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
            
            response = ses_client.send_email(
                Destination={'ToAddresses': [receiver_email]},
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
            return EmailService._send_via_gmail(receiver_email, filename, status, notes, action)
        except Exception as e:
            print(f"SES email sending failed: {str(e)}. Trying Gmail SMTP fallback...")
            return EmailService._send_via_gmail(receiver_email, filename, status, notes, action)
    
    @staticmethod
    def _send_via_gmail(receiver_email, filename, status, notes, action):
        """Fallback to Gmail SMTP when SES fails"""
        print(f"Gmail fallback called for {receiver_email}")
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
            msg['To'] = receiver_email
            
            msg.attach(MIMEText(html, 'html'))
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            
            print("Email sent successfully via Gmail SMTP")
            return True
            
        except Exception as e:
            print(f"Gmail SMTP fallback also failed: {str(e)}")
            return False