"""
Application settings and environment variables
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str  # anon/public key for client-side
    SUPABASE_SERVICE_KEY: str  # service role key for admin operations

    # AI Services
    ANTHROPIC_API_KEY: str
    ASSEMBLYAI_API_KEY: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Application
    APP_NAME: str = "GC Video Scope Analyzer"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # File Upload
    MAX_FILE_SIZE_MB: int = 500
    ALLOWED_VIDEO_TYPES: list[str] = ["video/mp4", "video/quicktime", "video/webm", "video/x-msvideo"]
    ALLOWED_AUDIO_TYPES: list[str] = ["audio/mpeg", "audio/mp4", "audio/wav", "audio/x-wav", "audio/flac", "audio/ogg"]
    ALLOWED_IMAGE_TYPES: list[str] = ["image/jpeg", "image/png", "image/heic", "image/heif"]
    ALLOWED_TEXT_TYPES: list[str] = ["text/plain", "application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]

    # AI Configuration
    CLAUDE_MODEL: str = "claude-3-5-sonnet-20241022"
    CLAUDE_MAX_TOKENS: int = 4096
    CLAUDE_TEMPERATURE: float = 0.3

    # Processing
    ASSEMBLYAI_WEBHOOK_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
