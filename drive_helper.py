import os
import json
import tempfile
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import streamlit as st

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_drive_service():
    """
    Create and return a Google Drive service object using service account credentials.
    
    Returns:
        googleapiclient.discovery.Resource: Google Drive service object
        
    Raises:
        Exception: If authentication fails
    """
    try:
        # Get service account JSON from environment variable
        service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if not service_account_json:
            raise ValueError("Google service account JSON not found. Please set GOOGLE_SERVICE_ACCOUNT_JSON in your .env file.")
        
        # Parse the JSON credentials
        try:
            service_account_info = json.loads(service_account_json)
        except json.JSONDecodeError:
            # If it's a file path instead of JSON content
            if os.path.exists(service_account_json):
                with open(service_account_json, 'r') as f:
                    service_account_info = json.load(f)
            else:
                raise ValueError("Invalid Google service account JSON format")
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            service_account_info, 
            scopes=SCOPES
        )
        
        # Build the service
        service = build('drive', 'v3', credentials=credentials)
        
        return service
        
    except Exception as e:
        raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")

def copy_template(service, template_file_id: str, new_name: str, parent_folder_id: str) -> str:
    """
    Copy a template file to a new location with a new name.
    
    Args:
        service: Google Drive service object
        template_file_id: ID of the template file to copy
        new_name: Name for the new file
        parent_folder_id: ID of the folder where the copy should be placed
        
    Returns:
        str: ID of the newly created file
        
    Raises:
        Exception: If copying fails
    """
    try:
        # Copy the file
        copied_file = {
            'name': new_name,
            'parents': [parent_folder_id]
        }
        
        result = service.files().copy(
            fileId=template_file_id,
            body=copied_file
        ).execute()
        
        return result.get('id')
        
    except Exception as e:
        raise Exception(f"Failed to copy template file: {str(e)}")

def upload_file(service, file_path: str, folder_id: str, filename: str = None) -> str:
    """
    Upload a file to Google Drive.
    
    Args:
        service: Google Drive service object
        file_path: Local path to the file to upload
        folder_id: ID of the Google Drive folder to upload to
        filename: Optional custom filename (defaults to original filename)
        
    Returns:
        str: ID of the uploaded file
        
    Raises:
        Exception: If upload fails
    """
    try:
        if filename is None:
            filename = os.path.basename(file_path)
        
        # Determine MIME type based on file extension
        mime_type = get_mime_type(file_path)
        
        # Create file metadata
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        # Create media upload object
        media = MediaFileUpload(file_path, mimetype=mime_type)
        
        # Upload the file
        result = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        return result.get('id')
        
    except Exception as e:
        raise Exception(f"Failed to upload file to Google Drive: {str(e)}")

def update_file(service, file_id: str, file_path: str) -> str:
    """
    Update an existing file in Google Drive.
    
    Args:
        service: Google Drive service object
        file_id: ID of the file to update
        file_path: Local path to the new file content
        
    Returns:
        str: ID of the updated file
        
    Raises:
        Exception: If update fails
    """
    try:
        # Determine MIME type based on file extension
        mime_type = get_mime_type(file_path)
        
        # Create media upload object
        media = MediaFileUpload(file_path, mimetype=mime_type)
        
        # Update the file
        result = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id'
        ).execute()
        
        return result.get('id')
        
    except Exception as e:
        raise Exception(f"Failed to update file in Google Drive: {str(e)}")

def get_file_info(service, file_id: str) -> dict:
    """
    Get information about a file in Google Drive.
    
    Args:
        service: Google Drive service object
        file_id: ID of the file
        
    Returns:
        dict: File information
        
    Raises:
        Exception: If getting file info fails
    """
    try:
        result = service.files().get(
            fileId=file_id,
            fields='id,name,mimeType,parents,webViewLink'
        ).execute()
        
        return result
        
    except Exception as e:
        raise Exception(f"Failed to get file information: {str(e)}")

def check_folder_access(service, folder_id: str) -> bool:
    """
    Check if the service account has access to a folder.
    
    Args:
        service: Google Drive service object
        folder_id: ID of the folder to check
        
    Returns:
        bool: True if accessible, False otherwise
    """
    try:
        service.files().get(fileId=folder_id, fields='id,name').execute()
        return True
    except Exception:
        return False

def get_mime_type(file_path: str) -> str:
    """
    Get MIME type based on file extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        str: MIME type
    """
    extension = os.path.splitext(file_path)[1].lower()
    
    mime_types = {
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.pdf': 'application/pdf',
        '.txt': 'text/plain',
        '.mp4': 'video/mp4',
        '.mp3': 'audio/mpeg'
    }
    
    return mime_types.get(extension, 'application/octet-stream')

def create_shareable_link(service, file_id: str) -> str:
    """
    Create a shareable link for a file.
    
    Args:
        service: Google Drive service object
        file_id: ID of the file
        
    Returns:
        str: Shareable link URL
        
    Raises:
        Exception: If creating link fails
    """
    try:
        # Make the file readable by anyone with the link
        permission = {
            'type': 'anyone',
            'role': 'reader'
        }
        
        service.permissions().create(
            fileId=file_id,
            body=permission
        ).execute()
        
        # Get the file info with web view link
        file_info = service.files().get(
            fileId=file_id,
            fields='webViewLink'
        ).execute()
        
        return file_info.get('webViewLink', '')
        
    except Exception as e:
        raise Exception(f"Failed to create shareable link: {str(e)}")

def validate_drive_setup(drive_folder_id: str, template_file_id: str) -> tuple[bool, str]:
    """
    Validate that the Google Drive setup is correct.
    
    Args:
        drive_folder_id: ID of the target folder
        template_file_id: ID of the template file
        
    Returns:
        tuple: (is_valid, error_message)
    """
    try:
        service = get_drive_service()
        
        # Check folder access
        if not check_folder_access(service, drive_folder_id):
            return False, f"Cannot access folder with ID: {drive_folder_id}"
        
        # Check template file access
        try:
            template_info = get_file_info(service, template_file_id)
            if 'docx' not in template_info.get('mimeType', ''):
                return False, f"Template file is not a DOCX file: {template_file_id}"
        except Exception:
            return False, f"Cannot access template file with ID: {template_file_id}"
        
        return True, "Google Drive setup is valid"
        
    except Exception as e:
        return False, f"Google Drive validation failed: {str(e)}" 