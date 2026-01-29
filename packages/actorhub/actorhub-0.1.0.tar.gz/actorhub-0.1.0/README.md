# ActorHub Python SDK

Official Python SDK for [ActorHub.ai](https://actorhub.ai) - Verify AI-generated content against protected identities.

## Installation

```bash
pip install actorhub
```

## Quick Start

```python
from actorhub import ActorHub

# Initialize the client
client = ActorHub(api_key="your-api-key")

# Verify if an image contains protected identities
result = client.verify(image_url="https://example.com/image.jpg")

if result.protected:
    print(f"Protected identity detected!")
    for identity in result.identities:
        print(f"  - {identity.display_name} (similarity: {identity.similarity_score})")
```

## Features

- **Identity Verification**: Check if images contain protected identities
- **Consent Checking**: Verify consent before AI generation
- **Marketplace Access**: Browse and license identities
- **Actor Pack Training**: Train custom Actor Packs
- **Async Support**: Full async/await support with `AsyncActorHub`
- **Automatic Retries**: Built-in retry logic with exponential backoff
- **Type Hints**: Full type annotations for IDE support

## Usage Examples

### Verify Image

```python
from actorhub import ActorHub

client = ActorHub(api_key="your-api-key")

# From URL
result = client.verify(image_url="https://example.com/image.jpg")

# From file
result = client.verify(image_file="/path/to/image.jpg")

# From base64
result = client.verify(image_base64="base64-encoded-data...")

print(f"Protected: {result.protected}")
print(f"Faces detected: {result.faces_detected}")
```

### Check Consent (for AI Platforms)

```python
result = client.check_consent(
    image_url="https://example.com/face.jpg",
    platform="runway",
    intended_use="video",
    region="US"
)

if result.protected:
    for face in result.faces:
        print(f"Consent for video: {face.consent.video_generation}")
        print(f"License available: {face.license.available}")
```

### Browse Marketplace

```python
# Search listings
listings = client.list_marketplace(
    query="actor",
    category="ACTOR",
    sort_by="popular",
    limit=10
)

for listing in listings:
    print(f"{listing.title} - ${listing.base_price_usd}")
```

### Purchase License

```python
from actorhub import LicenseType, UsageType

purchase = client.purchase_license(
    identity_id="uuid-here",
    license_type=LicenseType.STANDARD,
    usage_type=UsageType.COMMERCIAL,
    project_name="My AI Project",
    project_description="Creating promotional content",
    duration_days=30,
)

# Redirect user to Stripe checkout
print(f"Checkout URL: {purchase.checkout_url}")
```

### Get My Licenses

```python
licenses = client.get_my_licenses(status="active")

for lic in licenses:
    print(f"{lic.identity_name} - {lic.license_type} - Expires: {lic.expires_at}")
```

## Async Usage

```python
import asyncio
from actorhub import AsyncActorHub

async def main():
    async with AsyncActorHub(api_key="your-api-key") as client:
        result = await client.verify(image_url="https://example.com/image.jpg")
        print(f"Protected: {result.protected}")

asyncio.run(main())
```

## Error Handling

```python
from actorhub import (
    ActorHub,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError,
)

client = ActorHub(api_key="your-api-key")

try:
    result = client.verify(image_url="https://example.com/image.jpg")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limit exceeded. Retry after: {e.retry_after} seconds")
except ValidationError as e:
    print(f"Validation error: {e.message}")
except NotFoundError:
    print("Resource not found")
```

## Configuration

```python
client = ActorHub(
    api_key="your-api-key",
    base_url="https://api.actorhub.ai",  # Custom base URL
    timeout=30.0,                         # Request timeout in seconds
    max_retries=3,                        # Max retry attempts
)
```

## API Reference

### ActorHub Client

| Method | Description |
|--------|-------------|
| `verify()` | Verify if image contains protected identities |
| `get_identity()` | Get identity details by ID |
| `check_consent()` | Check consent status for AI generation |
| `list_marketplace()` | Search marketplace listings |
| `get_my_licenses()` | Get user's purchased licenses |
| `purchase_license()` | Purchase a license |
| `train_actor_pack()` | Initiate Actor Pack training |
| `get_actor_pack()` | Get Actor Pack status |

## Requirements

- Python 3.8+
- httpx
- pydantic
- tenacity

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Documentation](https://docs.actorhub.ai)
- [API Reference](https://api.actorhub.ai/docs)
- [GitHub](https://github.com/actorhub/actorhub-python)
- [PyPI](https://pypi.org/project/actorhub/)
