"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# =====================================================
# CLIENT MODELS
# =====================================================

class CostCode(BaseModel):
    """Individual cost code"""
    code: str
    name: str
    subcodes: Optional[List[dict]] = []


class ClientBase(BaseModel):
    """Base client model"""
    name: str
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[EmailStr] = None
    footer_text: Optional[str] = None
    primary_color: str = "#000000"
    secondary_color: str = "#4B5563"
    accent_color: str = "#10B981"
    default_template: str = "jral"


class ClientCreate(ClientBase):
    """Model for creating a client"""
    pass


class ClientUpdate(BaseModel):
    """Model for updating a client (all fields optional)"""
    name: Optional[str] = None
    company_address: Optional[str] = None
    company_phone: Optional[str] = None
    company_email: Optional[EmailStr] = None
    footer_text: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    logo_url: Optional[str] = None
    default_template: Optional[str] = None
    cost_codes: Optional[List[CostCode]] = None


class Client(ClientBase):
    """Complete client model with all fields"""
    id: UUID
    logo_url: Optional[str] = None
    cost_codes: List[CostCode] = []
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# PROJECT MODELS
# =====================================================

class ProjectBase(BaseModel):
    """Base project model"""
    name: str
    description: Optional[str] = None
    template_type: str = "jral"


class ProjectCreate(ProjectBase):
    """Model for creating a project"""
    client_id: UUID


class ProjectUpdate(BaseModel):
    """Model for updating a project"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    template_type: Optional[str] = None


class Project(ProjectBase):
    """Complete project model"""
    id: UUID
    client_id: UUID
    user_id: Optional[UUID] = None
    status: str
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectWithFiles(Project):
    """Project with file count"""
    file_count: int = 0
    video_count: int = 0
    audio_count: int = 0
    photo_count: int = 0
    text_count: int = 0


# =====================================================
# FILE MODELS
# =====================================================

class ProjectFileBase(BaseModel):
    """Base project file model"""
    file_type: str
    file_name: str
    mime_type: Optional[str] = None


class ProjectFileCreate(ProjectFileBase):
    """Model for creating a project file"""
    project_id: UUID
    file_url: str
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[int] = None


class ProjectFile(ProjectFileBase):
    """Complete project file model"""
    id: UUID
    project_id: UUID
    file_url: str
    file_size_mb: Optional[float] = None
    duration_seconds: Optional[int] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# ANALYSIS MODELS
# =====================================================

class ScopeItem(BaseModel):
    """Individual scope item"""
    cost_code: str
    category: str
    sub_code: Optional[str] = None
    sub_category: Optional[str] = None
    description: str
    location: Optional[str] = None
    materials: Optional[str] = None
    quantity: Optional[str] = None
    notes: Optional[str] = None
    photos: Optional[List[str]] = []  # Photo URLs linked to this item
    risk_level: Optional[str] = None  # low, medium, high


class ProjectSummary(BaseModel):
    """Project summary from AI analysis"""
    overview: str
    key_requirements: List[str]
    concerns: List[str]
    decision_points: List[str]
    important_notes: List[str]


class AnalysisBase(BaseModel):
    """Base analysis model"""
    transcript: Optional[str] = None
    project_summary: Optional[ProjectSummary] = None
    scope_items: Optional[List[ScopeItem]] = []
    scope_completeness_score: Optional[int] = None


class AnalysisCreate(AnalysisBase):
    """Model for creating an analysis"""
    project_id: UUID
    processing_time_seconds: Optional[int] = None
    ai_cost_usd: Optional[float] = None
    ai_provider_metadata: Optional[dict] = None


class Analysis(AnalysisBase):
    """Complete analysis model"""
    id: UUID
    project_id: UUID
    processing_time_seconds: Optional[int] = None
    ai_cost_usd: Optional[float] = None
    ai_provider_metadata: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# DOCUMENT MODELS
# =====================================================

class DocumentBase(BaseModel):
    """Base document model"""
    document_type: str  # docx, pdf
    template_used: str  # jral, trade, narrative


class DocumentCreate(DocumentBase):
    """Model for creating a document"""
    analysis_id: UUID
    file_url: str
    file_name: str
    file_size_mb: Optional[float] = None


class Document(DocumentBase):
    """Complete document model"""
    id: UUID
    analysis_id: UUID
    file_url: str
    file_name: str
    file_size_mb: Optional[float] = None
    generated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# PHOTO ANNOTATION MODELS
# =====================================================

class PhotoAnalysis(BaseModel):
    """AI analysis of a photo"""
    materials: List[str] = []
    conditions: List[str] = []
    risks: List[str] = []


class PhotoAnnotationBase(BaseModel):
    """Base photo annotation model"""
    caption: Optional[str] = None
    scope_category: Optional[str] = None
    ai_analysis: Optional[PhotoAnalysis] = None


class PhotoAnnotationCreate(PhotoAnnotationBase):
    """Model for creating a photo annotation"""
    project_file_id: UUID
    analysis_id: UUID


class PhotoAnnotation(PhotoAnnotationBase):
    """Complete photo annotation model"""
    id: UUID
    project_file_id: UUID
    analysis_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# AUTHENTICATION MODELS
# =====================================================

class UserSignup(BaseModel):
    """User signup request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    client_name: str  # Create client during signup


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response after auth"""
    id: UUID
    email: str
    client_id: Optional[UUID] = None
    role: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response"""
    user: UserResponse
    access_token: str
    refresh_token: str


# =====================================================
# API RESPONSE MODELS
# =====================================================

class SuccessResponse(BaseModel):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Generic error response"""
    success: bool = False
    error: str
    details: Optional[dict] = None


class UploadResponse(BaseModel):
    """File upload response"""
    file_id: UUID
    file_url: str
    file_name: str
    file_type: str


class ProcessingStatus(BaseModel):
    """Processing status response"""
    project_id: UUID
    status: str  # draft, processing, completed, failed
    progress: int  # 0-100
    message: str
    error: Optional[str] = None
