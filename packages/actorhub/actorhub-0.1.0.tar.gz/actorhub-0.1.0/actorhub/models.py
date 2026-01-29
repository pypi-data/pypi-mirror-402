"""
Pydantic models for ActorHub SDK.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TrainingStatus(str, Enum):
    """Actor Pack training status."""
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProtectionLevel(str, Enum):
    """Identity protection tier."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseType(str, Enum):
    """License type options."""
    STANDARD = "standard"
    EXTENDED = "extended"
    EXCLUSIVE = "exclusive"


class UsageType(str, Enum):
    """Usage type for licensing."""
    PERSONAL = "personal"
    EDITORIAL = "editorial"
    COMMERCIAL = "commercial"
    EDUCATIONAL = "educational"


class LicenseOption(BaseModel):
    """License option details."""
    type: LicenseType
    price_usd: float
    duration_days: int
    max_impressions: Optional[int] = None


class FaceBBox(BaseModel):
    """Face bounding box coordinates."""
    x: float
    y: float
    width: float
    height: float


class VerifyResult(BaseModel):
    """Individual identity verification result."""
    protected: bool
    identity_id: Optional[str] = None
    similarity_score: Optional[float] = None
    display_name: Optional[str] = None
    license_required: bool = False
    blocked_categories: List[str] = Field(default_factory=list)
    license_options: List[LicenseOption] = Field(default_factory=list)
    face_bbox: Optional[FaceBBox] = None


class VerifyResponse(BaseModel):
    """Response from identity verification."""
    protected: bool
    faces_detected: int
    identities: List[VerifyResult] = Field(default_factory=list)
    response_time_ms: int
    request_id: str


class ConsentDetails(BaseModel):
    """Consent permissions for an identity."""
    commercial_use: bool = False
    ai_training: bool = False
    video_generation: bool = False
    deepfake: bool = False


class ConsentRestrictions(BaseModel):
    """Consent restrictions."""
    blocked_categories: List[str] = Field(default_factory=list)
    blocked_regions: List[str] = Field(default_factory=list)
    blocked_brands: List[str] = Field(default_factory=list)


class ConsentLicenseInfo(BaseModel):
    """License availability info."""
    available: bool = False
    url: Optional[str] = None
    pricing: Optional[Dict[str, float]] = None


class ConsentResult(BaseModel):
    """Individual consent check result."""
    protected: bool
    identity_id: Optional[str] = None
    similarity_score: Optional[float] = None
    consent: ConsentDetails = Field(default_factory=ConsentDetails)
    restrictions: ConsentRestrictions = Field(default_factory=ConsentRestrictions)
    license: ConsentLicenseInfo = Field(default_factory=ConsentLicenseInfo)


class ConsentCheckResponse(BaseModel):
    """Response from consent check."""
    request_id: str
    protected: bool
    faces_detected: int
    faces: List[ConsentResult] = Field(default_factory=list)
    response_time_ms: int
    rate_limit_remaining: Optional[int] = None


class IdentityResponse(BaseModel):
    """Identity details."""
    id: str
    display_name: str
    profile_image_url: Optional[str] = None
    status: str
    protection_level: ProtectionLevel
    protection_mode: str
    total_verifications: int = 0
    total_licenses: int = 0
    total_revenue: float = 0.0
    allow_commercial: bool = False
    allow_ai_training: bool = False
    created_at: Optional[datetime] = None


class MarketplaceListingResponse(BaseModel):
    """Marketplace listing details."""
    id: str
    identity_id: str
    title: str
    description: Optional[str] = None
    category: str
    tags: List[str] = Field(default_factory=list)
    base_price_usd: float
    display_name: str
    profile_image_url: Optional[str] = None
    featured: bool = False
    view_count: int = 0
    license_count: int = 0
    rating: Optional[float] = None
    created_at: Optional[datetime] = None


class LicenseResponse(BaseModel):
    """License details."""
    id: str
    identity_id: str
    identity_name: str
    license_type: LicenseType
    usage_type: UsageType
    status: str
    project_name: str
    project_description: Optional[str] = None
    allowed_platforms: List[str] = Field(default_factory=list)
    max_impressions: Optional[int] = None
    max_outputs: Optional[int] = None
    price_usd: float
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class ActorPackComponents(BaseModel):
    """Actor Pack component availability."""
    face: bool = False
    voice: bool = False
    motion: bool = False


class ActorPackResponse(BaseModel):
    """Actor Pack details."""
    id: str
    identity_id: str
    name: str
    description: Optional[str] = None
    training_status: TrainingStatus
    training_progress: int = 0
    training_images_count: int = 0
    training_audio_seconds: int = 0
    components: ActorPackComponents = Field(default_factory=ActorPackComponents)
    lora_model_url: Optional[str] = None
    total_downloads: int = 0
    is_available: bool = False
    training_error: Optional[str] = None
    created_at: Optional[datetime] = None


class PurchaseResponse(BaseModel):
    """License purchase response."""
    checkout_url: str
    session_id: str
    price_usd: float
    license_details: Dict[str, Any]


class TrainActorPackResponse(BaseModel):
    """Actor Pack training initiation response."""
    id: str
    identity_id: str
    name: str
    training_status: TrainingStatus
    training_progress: int = 0
    message: str = "Training initiated"
