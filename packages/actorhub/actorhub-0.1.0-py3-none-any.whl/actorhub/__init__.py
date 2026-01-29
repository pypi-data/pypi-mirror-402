"""
ActorHub.ai Python SDK

Official Python client for the ActorHub.ai API.
Verify AI-generated content against protected identities.
"""

from .client import ActorHub, AsyncActorHub
from .models import (
    VerifyResponse,
    VerifyResult,
    IdentityResponse,
    ConsentCheckResponse,
    ConsentResult,
    MarketplaceListingResponse,
    LicenseResponse,
    ActorPackResponse,
    TrainingStatus,
    ProtectionLevel,
    LicenseType,
    UsageType,
)
from .exceptions import (
    ActorHubError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
    ServerError,
)

__version__ = "0.1.0"
__all__ = [
    # Clients
    "ActorHub",
    "AsyncActorHub",
    # Models
    "VerifyResponse",
    "VerifyResult",
    "IdentityResponse",
    "ConsentCheckResponse",
    "ConsentResult",
    "MarketplaceListingResponse",
    "LicenseResponse",
    "ActorPackResponse",
    "TrainingStatus",
    "ProtectionLevel",
    "LicenseType",
    "UsageType",
    # Exceptions
    "ActorHubError",
    "AuthenticationError",
    "RateLimitError",
    "ValidationError",
    "NotFoundError",
    "ServerError",
]
