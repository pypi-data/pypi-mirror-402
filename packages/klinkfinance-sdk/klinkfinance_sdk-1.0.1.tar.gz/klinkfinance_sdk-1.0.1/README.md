# Klink Finance Python SDK

Official Python SDK for the Klink platform. This SDK provides a simple and consistent interface for both Publishers and Advertisers to integrate with Klink's API.

## Features

* 🚀 Easy to use - Simple initialization and intuitive API
* 🔐 Built-in authentication - Automatic request signing and auth headers
* 📝 Full type hints - Complete type annotations for better IDE support
* 🐛 Debug mode - Detailed logging for troubleshooting
* ⚡ Lightweight - Minimal dependencies (only requests library)
* 🐍 Python 3.8+ - Modern Python with dataclasses and type hints

## Installation

```bash
pip install klinkfinance-sdk
```

## Requirements

* Python >= 3.8
* requests >= 2.28.0

## Quick Start

### Basic Usage (Publisher)

```python
from klinkfinance_sdk import KlinkSDK

# Initialize SDK using factory method - performs health check before initialization
# SDK will only be created if health check returns status 200
client = KlinkSDK.create({
    "api_key": "your-api-key",
    "api_secret": "your-api-secret",  # Required for Publisher
})

# Use the publisher client
publisher = client.publisher()

# Fetch offers
response = publisher.get_offers({
    "page": 1,
    "limit": 50,
    "category": ["gaming", "finance"],
    "country": "US",
    "device_name": "android",
})

print(f"Fetched {len(response['data'])} offers")
```

### Basic Usage (Advertiser)

```python
from klinkfinance_sdk import KlinkSDK

# Initialize SDK - api_secret is optional for Advertiser
client = KlinkSDK.create({
    "api_key": "your-api-key",
    # "api_secret": "your-api-secret",  # Optional for Advertiser
})

# Use the advertiser client
advertiser = client.advertiser()

# Send postback
advertiser.send_postback({
    "event_name": "create_account",
    "offer_id": "offer_123",
    "sub1": "sub1_value",
    "tx_id": "tx_123",
    "isChargeback": False,
    "chargebackReason": "",
    "isTest": True,
})
```

## Error Handling

```python
from klinkfinance_sdk import (
    KlinkSDK,
    KlinkConfigException,
    KlinkAuthException,
    KlinkAPIException,
    KlinkNetworkException,
)

try:
    client = KlinkSDK.create({
        "api_key": "invalid-key",
        "api_secret": "invalid-secret",
    })
except KlinkConfigException as e:
    print(f"Configuration error: {e}")
except KlinkAuthException as e:
    print(f"Authentication failed: {e}")
except KlinkAPIException as e:
    print(f"API error: {e} (Status: {e.status_code})")
except KlinkNetworkException as e:
    print(f"Network error: {e}")
```

## License

MIT
