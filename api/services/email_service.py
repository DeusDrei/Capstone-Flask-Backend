import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    @staticmethod
    def send_instructional_material_notification(receiver_email, filename, status, notes, action="created"):
        """
        Send email notification for instructional material actions
        
        Args:
            receiver_email: Email address of the recipient
            filename: Name of the instructional material file
            status: Current status of the material
            notes: Additional notes/comments
            action: Either "created" or "updated"
        """
        try:
            # Email configuration
            sender_email = os.getenv('EMAIL_SENDER', 'merit.pup@gmail.com')
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', 587))
            smtp_username = os.getenv('SMTP_USERNAME', 'merit.pup@gmail.com')
            smtp_password = os.getenv('SMTP_PASSWORD')
            
            if not smtp_password:
                raise ValueError("SMTP password not configured")
            
            # Create message
            subject = f"Instructional Material {action.capitalize()}: {filename}"
            
            # HTML email content
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
            
            # Plain text version
            text = f"""
            Instructional Material Notification
            
            Your instructional material has been {action} successfully.
            
            Filename: {filename}
            Status: {status}
            Notes: {notes or 'No additional notes'}
            
            Thank you for using our instructional materials system.
            """
            
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = receiver_email
            
            # Attach parts
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(sender_email, receiver_email, msg.as_string())
            
            return True
            
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False