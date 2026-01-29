"""
ActorHub API Client.

Provides sync and async clients for interacting with ActorHub.ai API.
"""

import base64
from pathlib import Path
from typing import Optional, List, Union, Dict, Any, BinaryIO

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from .models import (
    VerifyResponse,
    IdentityResponse,
    ConsentCheckResponse,
    MarketplaceListingResponse,
    LicenseResponse,
    ActorPackResponse,
    PurchaseResponse,
    TrainActorPackResponse,
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

DEFAULT_BASE_URL = "https://api.actorhub.ai"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


def _should_retry(exception: BaseException) -> bool:
    """Determine if request should be retried."""
    if isinstance(exception, RateLimitError):
        return True
    if isinstance(exception, ServerError):
        return True
    if isinstance(exception, httpx.TransportError):
        return True
    return False


class ActorHub:
    """
    Synchronous client for ActorHub.ai API.

    Usage:
        client = ActorHub(api_key="your-api-key")
        result = client.verify(image_url="https://example.com/image.jpg")
        if result.protected:
            print("Protected identity detected!")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize ActorHub client.

        Args:
            api_key: Your ActorHub API key
            base_url: API base URL (default: https://api.actorhub.ai)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> Dict[str, str]:
        """Get default request headers."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "actorhub-python/0.1.0",
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process API response and raise appropriate exceptions."""
        request_id = response.headers.get("X-Request-ID")

        if response.status_code == 401:
            raise AuthenticationError(
                message="Invalid or missing API key",
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code == 404:
            raise NotFoundError(
                message="Resource not found",
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code == 422:
            data = response.json() if response.content else {}
            raise ValidationError(
                message=data.get("detail", "Validation error"),
                errors=data.get("errors", {}),
                response_data=data,
                request_id=request_id,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code >= 500:
            raise ServerError(
                message=f"Server error: {response.status_code}",
                status_code=response.status_code,
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code >= 400:
            data = response.json() if response.content else {}
            raise ActorHubError(
                message=data.get("detail", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_data=data,
                request_id=request_id,
            )

        return response.json() if response.content else {}

    @retry(
        stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((RateLimitError, ServerError, httpx.TransportError)),
        reraise=True,
    )
    def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        response = self._client.request(method, path, **kwargs)
        return self._handle_response(response)

    def verify(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_file: Optional[Union[str, Path, BinaryIO]] = None,
        include_license_options: bool = False,
    ) -> VerifyResponse:
        """
        Verify if an image contains protected identities.

        Args:
            image_url: URL of the image to verify
            image_base64: Base64-encoded image data
            image_file: Path to image file or file-like object
            include_license_options: Include available license options

        Returns:
            VerifyResponse with protection status and identity details

        Raises:
            ValidationError: If no image source provided
            AuthenticationError: If API key is invalid
        """
        if not any([image_url, image_base64, image_file]):
            raise ValidationError("Must provide image_url, image_base64, or image_file")

        payload: Dict[str, Any] = {
            "include_license_options": include_license_options,
        }

        if image_url:
            payload["image_url"] = image_url
        elif image_base64:
            payload["image_base64"] = image_base64
        elif image_file:
            if isinstance(image_file, (str, Path)):
                with open(image_file, "rb") as f:
                    payload["image_base64"] = base64.b64encode(f.read()).decode()
            else:
                payload["image_base64"] = base64.b64encode(image_file.read()).decode()

        data = self._request("POST", "/api/v1/identity/verify", json=payload)
        return VerifyResponse(**data)

    def get_identity(self, identity_id: str) -> IdentityResponse:
        """
        Get identity details by ID.

        Args:
            identity_id: UUID of the identity

        Returns:
            IdentityResponse with identity details

        Raises:
            NotFoundError: If identity not found
        """
        data = self._request("GET", f"/api/v1/identity/{identity_id}")
        return IdentityResponse(**data)

    def check_consent(
        self,
        platform: str,
        intended_use: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        face_embedding: Optional[List[float]] = None,
        region: Optional[str] = None,
    ) -> ConsentCheckResponse:
        """
        Check consent status for face before AI generation.

        Args:
            platform: Platform name (e.g., "runway", "pika")
            intended_use: Intended use type (video|image|training|deepfake)
            image_url: URL of the image
            image_base64: Base64-encoded image
            face_embedding: 512D face embedding vector (fastest)
            region: ISO country code for regional restrictions

        Returns:
            ConsentCheckResponse with consent details and restrictions
        """
        if not any([image_url, image_base64, face_embedding]):
            raise ValidationError(
                "Must provide image_url, image_base64, or face_embedding"
            )

        payload: Dict[str, Any] = {
            "platform": platform,
            "intended_use": intended_use,
        }

        if image_url:
            payload["image_url"] = image_url
        if image_base64:
            payload["image_base64"] = image_base64
        if face_embedding:
            payload["face_embedding"] = face_embedding
        if region:
            payload["region"] = region

        data = self._request("POST", "/api/v1/consent/check", json=payload)
        return ConsentCheckResponse(**data)

    def list_marketplace(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        featured: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "popular",
        page: int = 1,
        limit: int = 20,
    ) -> List[MarketplaceListingResponse]:
        """
        Search marketplace listings.

        Args:
            query: Search query for title/description
            category: Filter by category (ACTOR|MODEL|INFLUENCER)
            tags: Filter by tags
            featured: Filter featured listings only
            min_price: Minimum price filter
            max_price: Maximum price filter
            sort_by: Sort order (popular|newest|price_low|price_high|rating)
            page: Page number (1-based)
            limit: Results per page (1-100)

        Returns:
            List of MarketplaceListingResponse
        """
        params: Dict[str, Any] = {
            "sort_by": sort_by,
            "page": page,
            "limit": limit,
        }

        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if tags:
            params["tags"] = ",".join(tags)
        if featured is not None:
            params["featured"] = featured
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        data = self._request("GET", "/api/v1/marketplace/listings", params=params)
        return [MarketplaceListingResponse(**item) for item in data]

    def get_my_licenses(
        self,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[LicenseResponse]:
        """
        Get licenses purchased by the current user.

        Args:
            status: Filter by status (active|expired|pending)
            page: Page number
            limit: Results per page

        Returns:
            List of LicenseResponse
        """
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if status:
            params["status"] = status

        data = self._request("GET", "/api/v1/marketplace/licenses/mine", params=params)
        return [LicenseResponse(**item) for item in data]

    def purchase_license(
        self,
        identity_id: str,
        license_type: Union[LicenseType, str],
        usage_type: Union[UsageType, str],
        project_name: str,
        project_description: str,
        duration_days: int = 30,
        allowed_platforms: Optional[List[str]] = None,
        max_impressions: Optional[int] = None,
        max_outputs: Optional[int] = None,
    ) -> PurchaseResponse:
        """
        Purchase a license for an identity.

        Args:
            identity_id: UUID of the identity to license
            license_type: Type of license (standard|extended|exclusive)
            usage_type: Usage category (personal|editorial|commercial|educational)
            project_name: Name of your project
            project_description: Description of intended use
            duration_days: License duration in days
            allowed_platforms: List of platforms where license is valid
            max_impressions: Maximum impressions allowed (optional)
            max_outputs: Maximum outputs allowed (optional)

        Returns:
            PurchaseResponse with Stripe checkout URL
        """
        if isinstance(license_type, LicenseType):
            license_type = license_type.value
        if isinstance(usage_type, UsageType):
            usage_type = usage_type.value

        payload: Dict[str, Any] = {
            "identity_id": identity_id,
            "license_type": license_type,
            "usage_type": usage_type,
            "project_name": project_name,
            "project_description": project_description,
            "duration_days": duration_days,
        }

        if allowed_platforms:
            payload["allowed_platforms"] = allowed_platforms
        if max_impressions:
            payload["max_impressions"] = max_impressions
        if max_outputs:
            payload["max_outputs"] = max_outputs

        data = self._request("POST", "/api/v1/marketplace/license/purchase", json=payload)
        return PurchaseResponse(**data)

    def train_actor_pack(
        self,
        identity_id: str,
        name: str,
        description: Optional[str] = None,
        training_images: Optional[List[Union[str, Path, BinaryIO]]] = None,
    ) -> TrainActorPackResponse:
        """
        Initiate Actor Pack training.

        Args:
            identity_id: UUID of the identity
            name: Name for the Actor Pack
            description: Optional description
            training_images: List of training image files (min 8 required)

        Returns:
            TrainActorPackResponse with training job ID
        """
        files = []
        if training_images:
            for img in training_images:
                if isinstance(img, (str, Path)):
                    files.append(("training_images", open(img, "rb")))
                else:
                    files.append(("training_images", img))

        pack_data = {"name": name}
        if description:
            pack_data["description"] = description

        response = self._client.post(
            "/api/v1/actor-packs/train",
            data={"pack_data": str(pack_data), "identity_id": identity_id},
            files=files if files else None,
        )
        data = self._handle_response(response)
        return TrainActorPackResponse(**data)

    def get_actor_pack(self, pack_id: str) -> ActorPackResponse:
        """
        Get Actor Pack status and details.

        Args:
            pack_id: UUID of the Actor Pack

        Returns:
            ActorPackResponse with training status and details
        """
        data = self._request("GET", f"/api/v1/actor-packs/status/{pack_id}")
        return ActorPackResponse(**data)

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self) -> "ActorHub":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()


class AsyncActorHub:
    """
    Asynchronous client for ActorHub.ai API.

    Usage:
        async with AsyncActorHub(api_key="your-api-key") as client:
            result = await client.verify(image_url="https://example.com/image.jpg")
            if result.protected:
                print("Protected identity detected!")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize async ActorHub client.

        Args:
            api_key: Your ActorHub API key
            base_url: API base URL (default: https://api.actorhub.ai)
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum retry attempts (default: 3)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=timeout,
            headers=self._default_headers(),
        )

    def _default_headers(self) -> Dict[str, str]:
        """Get default request headers."""
        return {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": "actorhub-python/0.1.0",
        }

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process API response and raise appropriate exceptions."""
        request_id = response.headers.get("X-Request-ID")

        if response.status_code == 401:
            raise AuthenticationError(
                message="Invalid or missing API key",
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code == 404:
            raise NotFoundError(
                message="Resource not found",
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code == 422:
            data = response.json() if response.content else {}
            raise ValidationError(
                message=data.get("detail", "Validation error"),
                errors=data.get("errors", {}),
                response_data=data,
                request_id=request_id,
            )

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message="Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None,
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code >= 500:
            raise ServerError(
                message=f"Server error: {response.status_code}",
                status_code=response.status_code,
                response_data=response.json() if response.content else {},
                request_id=request_id,
            )

        if response.status_code >= 400:
            data = response.json() if response.content else {}
            raise ActorHubError(
                message=data.get("detail", f"API error: {response.status_code}"),
                status_code=response.status_code,
                response_data=data,
                request_id=request_id,
            )

        return response.json() if response.content else {}

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Make HTTP request with retry logic."""
        last_exception: Optional[Exception] = None

        for attempt in range(self.max_retries):
            try:
                response = await self._client.request(method, path, **kwargs)
                return self._handle_response(response)
            except (RateLimitError, ServerError, httpx.TransportError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    import asyncio
                    wait_time = min(2 ** attempt, 10)
                    await asyncio.sleep(wait_time)
                continue
            except Exception:
                raise

        if last_exception:
            raise last_exception
        raise ActorHubError("Request failed after retries")

    async def verify(
        self,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_file: Optional[Union[str, Path, BinaryIO]] = None,
        include_license_options: bool = False,
    ) -> VerifyResponse:
        """
        Verify if an image contains protected identities.

        Args:
            image_url: URL of the image to verify
            image_base64: Base64-encoded image data
            image_file: Path to image file or file-like object
            include_license_options: Include available license options

        Returns:
            VerifyResponse with protection status and identity details
        """
        if not any([image_url, image_base64, image_file]):
            raise ValidationError("Must provide image_url, image_base64, or image_file")

        payload: Dict[str, Any] = {
            "include_license_options": include_license_options,
        }

        if image_url:
            payload["image_url"] = image_url
        elif image_base64:
            payload["image_base64"] = image_base64
        elif image_file:
            if isinstance(image_file, (str, Path)):
                with open(image_file, "rb") as f:
                    payload["image_base64"] = base64.b64encode(f.read()).decode()
            else:
                payload["image_base64"] = base64.b64encode(image_file.read()).decode()

        data = await self._request("POST", "/api/v1/identity/verify", json=payload)
        return VerifyResponse(**data)

    async def get_identity(self, identity_id: str) -> IdentityResponse:
        """Get identity details by ID."""
        data = await self._request("GET", f"/api/v1/identity/{identity_id}")
        return IdentityResponse(**data)

    async def check_consent(
        self,
        platform: str,
        intended_use: str,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        face_embedding: Optional[List[float]] = None,
        region: Optional[str] = None,
    ) -> ConsentCheckResponse:
        """Check consent status for face before AI generation."""
        if not any([image_url, image_base64, face_embedding]):
            raise ValidationError(
                "Must provide image_url, image_base64, or face_embedding"
            )

        payload: Dict[str, Any] = {
            "platform": platform,
            "intended_use": intended_use,
        }

        if image_url:
            payload["image_url"] = image_url
        if image_base64:
            payload["image_base64"] = image_base64
        if face_embedding:
            payload["face_embedding"] = face_embedding
        if region:
            payload["region"] = region

        data = await self._request("POST", "/api/v1/consent/check", json=payload)
        return ConsentCheckResponse(**data)

    async def list_marketplace(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        featured: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "popular",
        page: int = 1,
        limit: int = 20,
    ) -> List[MarketplaceListingResponse]:
        """Search marketplace listings."""
        params: Dict[str, Any] = {
            "sort_by": sort_by,
            "page": page,
            "limit": limit,
        }

        if query:
            params["query"] = query
        if category:
            params["category"] = category
        if tags:
            params["tags"] = ",".join(tags)
        if featured is not None:
            params["featured"] = featured
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price

        data = await self._request("GET", "/api/v1/marketplace/listings", params=params)
        return [MarketplaceListingResponse(**item) for item in data]

    async def get_my_licenses(
        self,
        status: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> List[LicenseResponse]:
        """Get licenses purchased by the current user."""
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if status:
            params["status"] = status

        data = await self._request("GET", "/api/v1/marketplace/licenses/mine", params=params)
        return [LicenseResponse(**item) for item in data]

    async def purchase_license(
        self,
        identity_id: str,
        license_type: Union[LicenseType, str],
        usage_type: Union[UsageType, str],
        project_name: str,
        project_description: str,
        duration_days: int = 30,
        allowed_platforms: Optional[List[str]] = None,
        max_impressions: Optional[int] = None,
        max_outputs: Optional[int] = None,
    ) -> PurchaseResponse:
        """Purchase a license for an identity."""
        if isinstance(license_type, LicenseType):
            license_type = license_type.value
        if isinstance(usage_type, UsageType):
            usage_type = usage_type.value

        payload: Dict[str, Any] = {
            "identity_id": identity_id,
            "license_type": license_type,
            "usage_type": usage_type,
            "project_name": project_name,
            "project_description": project_description,
            "duration_days": duration_days,
        }

        if allowed_platforms:
            payload["allowed_platforms"] = allowed_platforms
        if max_impressions:
            payload["max_impressions"] = max_impressions
        if max_outputs:
            payload["max_outputs"] = max_outputs

        data = await self._request("POST", "/api/v1/marketplace/license/purchase", json=payload)
        return PurchaseResponse(**data)

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncActorHub":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()
