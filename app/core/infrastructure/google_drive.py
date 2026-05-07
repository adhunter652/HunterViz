import logging
from typing import Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.auth

logger = logging.getLogger(__name__)

def get_drive_service():
    """Initialize Drive API service using Application Default Credentials."""
    credentials, project = google.auth.default(
        scopes=['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']
    )
    return build('drive', 'v3', credentials=credentials)

def share_report(file_id: str, email: str, role: str = 'viewer') -> tuple[bool, str]:
    """
    Share a Google Drive file (Looker Studio report) with an email address.
    Returns (success, message).
    """
    try:
        service = get_drive_service()
        
        # Check if already shared or just try to create permission
        # Using sendNotificationEmail=False to avoid spamming if not needed, 
        # but the user might want notifications. Let's keep it True by default.
        
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email.strip().lower()
        }
        
        service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id',
            sendNotificationEmail=True
        ).execute()
        
        return True, f"Successfully shared with {email}"
        
    except HttpError as error:
        detail = error.reason
        # Common error: "The email address is not associated with a Google Account."
        if error.resp.status == 400 and "not associated with a Google Account" in str(error):
            return False, f"The email {email} is not a valid Google account."
        
        logger.error(f"Error sharing file {file_id} with {email}: {error}")
        return False, f"Failed to share: {detail}"
    except Exception as e:
        logger.error(f"Unexpected error sharing file: {e}")
        return False, f"An unexpected error occurred: {str(e)}"

def extract_file_id(url: str) -> Optional[str]:
    """Extract Google Drive / Looker Studio file ID from URL."""
    if not url:
        return None
    # Looker Studio URLs usually look like:
    # https://lookerstudio.google.com/reporting/FILE_ID/page/PAGE_ID
    # or https://lookerstudio.google.com/u/0/reporting/FILE_ID/...
    
    import re
    # Match 28+ chars of ID-like string
    match = re.search(r'reporting/([a-zA-Z0-9_-]{28,})', url)
    if match:
        return match.group(1)
    
    # Fallback for generic drive links
    match = re.search(r'/d/([a-zA-Z0-9_-]{28,})', url)
    if match:
        return match.group(1)
        
    return None
