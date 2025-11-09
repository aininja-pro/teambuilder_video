"""
Supabase client configuration and helpers
"""
from supabase import create_client, Client
from config.settings import settings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase client wrapper with helper methods"""

    def __init__(self, use_service_key: bool = False):
        """
        Initialize Supabase client

        Args:
            use_service_key: If True, use service role key (bypasses RLS).
                           If False, use anon key (respects RLS)
        """
        key = settings.SUPABASE_SERVICE_KEY if use_service_key else settings.SUPABASE_KEY
        self.client: Client = create_client(settings.SUPABASE_URL, key)
        self.use_service_key = use_service_key

    def get_client(self) -> Client:
        """Get the underlying Supabase client"""
        return self.client

    async def upload_file(
        self,
        bucket: str,
        file_path: str,
        file_data: bytes,
        content_type: Optional[str] = None
    ) -> dict:
        """
        Upload a file to Supabase Storage

        Args:
            bucket: Storage bucket name (e.g., 'uploads', 'documents', 'logos')
            file_path: Path within bucket (e.g., 'client_id/project_id/file.mp4')
            file_data: File content as bytes
            content_type: MIME type of the file

        Returns:
            dict with 'path' and 'url' of uploaded file
        """
        try:
            # Upload file
            response = self.client.storage.from_(bucket).upload(
                file_path,
                file_data,
                file_options={"content-type": content_type} if content_type else None
            )

            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(file_path)

            logger.info(f"File uploaded successfully: {bucket}/{file_path}")

            return {
                "path": file_path,
                "url": public_url
            }

        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {e}")
            raise

    async def download_file(self, bucket: str, file_path: str) -> bytes:
        """
        Download a file from Supabase Storage

        Args:
            bucket: Storage bucket name
            file_path: Path within bucket

        Returns:
            File content as bytes
        """
        try:
            response = self.client.storage.from_(bucket).download(file_path)
            logger.info(f"File downloaded successfully: {bucket}/{file_path}")
            return response

        except Exception as e:
            logger.error(f"Error downloading file from Supabase Storage: {e}")
            raise

    async def delete_file(self, bucket: str, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage

        Args:
            bucket: Storage bucket name
            file_path: Path within bucket

        Returns:
            True if successful
        """
        try:
            self.client.storage.from_(bucket).remove([file_path])
            logger.info(f"File deleted successfully: {bucket}/{file_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {e}")
            raise


# Global instances
# Use anon key for client-side operations (respects RLS)
supabase_client = SupabaseClient(use_service_key=False)

# Use service key for admin operations (bypasses RLS)
supabase_admin = SupabaseClient(use_service_key=True)


def get_supabase() -> Client:
    """Get Supabase client (respects RLS)"""
    return supabase_client.get_client()


def get_supabase_admin() -> Client:
    """Get Supabase admin client (bypasses RLS)"""
    return supabase_admin.get_client()
