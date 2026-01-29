"""
Tests for ActorHub Python SDK.
"""

import pytest
import respx
from httpx import Response

from actorhub import (
    ActorHub,
    AsyncActorHub,
    VerifyResponse,
    ConsentCheckResponse,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
)


@pytest.fixture
def api_key():
    return "test-api-key-12345"


@pytest.fixture
def client(api_key):
    return ActorHub(api_key=api_key)


class TestActorHubSync:
    """Tests for synchronous ActorHub client."""

    @respx.mock
    def test_verify_with_url(self, client):
        """Test verify endpoint with image URL."""
        mock_response = {
            "protected": True,
            "faces_detected": 1,
            "identities": [
                {
                    "protected": True,
                    "identity_id": "123e4567-e89b-12d3-a456-426614174000",
                    "similarity_score": 0.95,
                    "display_name": "Test Actor",
                    "license_required": True,
                    "blocked_categories": [],
                    "license_options": [],
                }
            ],
            "response_time_ms": 150,
            "request_id": "req-123",
        }

        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(200, json=mock_response)
        )

        result = client.verify(image_url="https://example.com/image.jpg")

        assert isinstance(result, VerifyResponse)
        assert result.protected is True
        assert result.faces_detected == 1
        assert len(result.identities) == 1
        assert result.identities[0].display_name == "Test Actor"

    @respx.mock
    def test_verify_not_protected(self, client):
        """Test verify endpoint when no protected identities found."""
        mock_response = {
            "protected": False,
            "faces_detected": 1,
            "identities": [],
            "response_time_ms": 80,
            "request_id": "req-456",
        }

        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(200, json=mock_response)
        )

        result = client.verify(image_url="https://example.com/unknown.jpg")

        assert result.protected is False
        assert result.faces_detected == 1
        assert len(result.identities) == 0

    def test_verify_validation_error(self, client):
        """Test verify raises ValidationError when no image provided."""
        with pytest.raises(ValidationError) as exc_info:
            client.verify()

        assert "Must provide" in str(exc_info.value)

    @respx.mock
    def test_authentication_error(self, client):
        """Test handling of authentication errors."""
        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(401, json={"detail": "Invalid API key"})
        )

        with pytest.raises(AuthenticationError):
            client.verify(image_url="https://example.com/image.jpg")

    @respx.mock
    def test_rate_limit_error(self, client):
        """Test handling of rate limit errors."""
        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(
                429,
                json={"detail": "Rate limit exceeded"},
                headers={"Retry-After": "60"},
            )
        )

        with pytest.raises(RateLimitError) as exc_info:
            client.verify(image_url="https://example.com/image.jpg")

        assert exc_info.value.retry_after == 60

    @respx.mock
    def test_check_consent(self, client):
        """Test consent check endpoint."""
        mock_response = {
            "request_id": "req-789",
            "protected": True,
            "faces_detected": 1,
            "faces": [
                {
                    "protected": True,
                    "identity_id": "123e4567-e89b-12d3-a456-426614174000",
                    "similarity_score": 0.92,
                    "consent": {
                        "commercial_use": True,
                        "ai_training": False,
                        "video_generation": True,
                        "deepfake": False,
                    },
                    "restrictions": {
                        "blocked_categories": ["adult"],
                        "blocked_regions": [],
                        "blocked_brands": [],
                    },
                    "license": {
                        "available": True,
                        "url": "https://actorhub.ai/license/123",
                        "pricing": {"standard": 99.99},
                    },
                }
            ],
            "response_time_ms": 200,
            "rate_limit_remaining": 950,
        }

        respx.post("https://api.actorhub.ai/api/v1/consent/check").mock(
            return_value=Response(200, json=mock_response)
        )

        result = client.check_consent(
            image_url="https://example.com/face.jpg",
            platform="runway",
            intended_use="video",
        )

        assert isinstance(result, ConsentCheckResponse)
        assert result.protected is True
        assert result.faces[0].consent.video_generation is True
        assert result.faces[0].consent.deepfake is False

    @respx.mock
    def test_list_marketplace(self, client):
        """Test marketplace listing endpoint."""
        mock_response = [
            {
                "id": "listing-1",
                "identity_id": "identity-1",
                "title": "Professional Actor",
                "description": "Experienced film actor",
                "category": "ACTOR",
                "tags": ["film", "drama"],
                "base_price_usd": 99.99,
                "display_name": "John Actor",
                "featured": True,
                "view_count": 1000,
                "license_count": 50,
            }
        ]

        respx.get("https://api.actorhub.ai/api/v1/marketplace/listings").mock(
            return_value=Response(200, json=mock_response)
        )

        results = client.list_marketplace(category="ACTOR", limit=10)

        assert len(results) == 1
        assert results[0].title == "Professional Actor"
        assert results[0].base_price_usd == 99.99

    @respx.mock
    def test_get_identity(self, client):
        """Test get identity endpoint."""
        mock_response = {
            "id": "123e4567-e89b-12d3-a456-426614174000",
            "display_name": "Test Actor",
            "status": "VERIFIED",
            "protection_level": "pro",
            "protection_mode": "marketplace",
            "total_verifications": 100,
            "total_licenses": 10,
            "total_revenue": 999.99,
            "allow_commercial": True,
            "allow_ai_training": False,
        }

        respx.get(
            "https://api.actorhub.ai/api/v1/identity/123e4567-e89b-12d3-a456-426614174000"
        ).mock(return_value=Response(200, json=mock_response))

        result = client.get_identity("123e4567-e89b-12d3-a456-426614174000")

        assert result.display_name == "Test Actor"
        assert result.protection_level.value == "pro"

    @respx.mock
    def test_not_found_error(self, client):
        """Test handling of not found errors."""
        respx.get("https://api.actorhub.ai/api/v1/identity/nonexistent").mock(
            return_value=Response(404, json={"detail": "Identity not found"})
        )

        with pytest.raises(NotFoundError):
            client.get_identity("nonexistent")


class TestActorHubAsync:
    """Tests for asynchronous ActorHub client."""

    @pytest.fixture
    def async_client(self, api_key):
        return AsyncActorHub(api_key=api_key)

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_verify(self, async_client):
        """Test async verify endpoint."""
        mock_response = {
            "protected": False,
            "faces_detected": 0,
            "identities": [],
            "response_time_ms": 50,
            "request_id": "req-async-123",
        }

        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(200, json=mock_response)
        )

        result = await async_client.verify(image_url="https://example.com/image.jpg")

        assert isinstance(result, VerifyResponse)
        assert result.protected is False

        await async_client.close()

    @respx.mock
    @pytest.mark.asyncio
    async def test_async_context_manager(self, api_key):
        """Test async client as context manager."""
        mock_response = {
            "protected": True,
            "faces_detected": 1,
            "identities": [],
            "response_time_ms": 100,
            "request_id": "req-ctx-123",
        }

        respx.post("https://api.actorhub.ai/api/v1/identity/verify").mock(
            return_value=Response(200, json=mock_response)
        )

        async with AsyncActorHub(api_key=api_key) as client:
            result = await client.verify(image_url="https://example.com/image.jpg")
            assert result.protected is True


class TestClientConfiguration:
    """Tests for client configuration."""

    def test_custom_base_url(self, api_key):
        """Test custom base URL configuration."""
        client = ActorHub(
            api_key=api_key,
            base_url="https://custom.actorhub.ai",
        )
        assert client.base_url == "https://custom.actorhub.ai"

    def test_custom_timeout(self, api_key):
        """Test custom timeout configuration."""
        client = ActorHub(api_key=api_key, timeout=60.0)
        assert client.timeout == 60.0

    def test_context_manager(self, api_key):
        """Test sync client as context manager."""
        with ActorHub(api_key=api_key) as client:
            assert client.api_key == api_key
