import os
import boto3
import tempfile
from dotenv import load_dotenv

load_dotenv()

class RequirementsService:
    """Service for downloading static requirement documents from S3"""
    
    @staticmethod
    def download_requirements_pdf():
        """
        Download the requirements PDF from S3 (recommendation-letter.pdf)
        Returns the file content or raises an exception
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            # The specific S3 key for the requirements PDF
            s3_key = "requirements/recommendation-letter.pdf"
            
            # Create S3 client
            s3 = boto3.client('s3')
            
            # Create a temporary file to download to
            temp_dir = tempfile.gettempdir()
            temp_file_path = os.path.join(temp_dir, "recommendation-letter.pdf")
            
            # Download the file from S3
            s3.download_file(bucket_name, s3_key, temp_file_path)
            
            return temp_file_path
            
        except Exception as e:
            raise Exception(f"Requirements PDF download error: {str(e)}")
    
    @staticmethod
    def generate_requirements_presigned_url(expires_in=3600):
        """
        Generate a presigned URL for the requirements PDF (default 1 hour)
        Returns the presigned URL for direct access
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            s3_key = "requirements/recommendation-letter.pdf"
            
            s3 = boto3.client('s3')
            
            # Generate presigned URL with content disposition for inline viewing
            params = {
                'Bucket': bucket_name,
                'Key': s3_key,
                'ResponseContentType': 'application/pdf',
                'ResponseContentDisposition': 'inline; filename="recommendation-letter.pdf"'
            }
            
            url = s3.generate_presigned_url('get_object', Params=params, ExpiresIn=expires_in)
            return url
            
        except Exception as e:
            raise Exception(f"Presigned URL generation error: {str(e)}")
    
    @staticmethod
    def get_requirements_direct_url():
        """
        Get the direct S3 URL for the requirements PDF
        Note: This will only work if the bucket/object has public read access
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                raise ValueError("AWS_BUCKET_NAME not found in environment variables")
            
            s3_key = "requirements/recommendation-letter.pdf"
            
            # Build direct S3 URL
            return f"https://{bucket_name}.s3.amazonaws.com/{s3_key}"
            
        except Exception as e:
            raise Exception(f"Direct URL generation error: {str(e)}")
    
    @staticmethod
    def check_requirements_file_exists():
        """
        Check if the requirements PDF exists in S3
        Returns True if exists, False otherwise
        """
        try:
            bucket_name = os.getenv('AWS_BUCKET_NAME')
            if not bucket_name:
                return False
            
            s3_key = "requirements/recommendation-letter.pdf"
            s3 = boto3.client('s3')
            
            # Try to get object metadata
            s3.head_object(Bucket=bucket_name, Key=s3_key)
            return True
            
        except Exception:
            return False