"""
Publisher API example for Klink SDK
"""
import os
from klinkfinance_sdk import KlinkSDK, KlinkException

try:
    # Initialize SDK with health check
    client = KlinkSDK.create({
        "api_key": os.getenv("KLINK_API_KEY"),
        "api_secret": os.getenv("KLINK_API_SECRET"),  # Required for Publisher
        "debug": True,
    })

    # Get publisher client
    publisher = client.publisher()

    # Example 1: Fetch offers
    print("Fetching offers...")
    offers = publisher.get_offers({
        "page": 1,
        "limit": 10,
        "category": ["gaming"],
        "country": "US",
    })
    print(f"Found {len(offers['data'])} offers\n")

    # Example 2: Fetch conversions
    print("Fetching conversions...")
    conversions = publisher.get_conversions({
        "page": 1,
        "limit": 5,
        "status": "approved",
    })
    print(f"Found {len(conversions['data'])} conversions\n")

    # Example 3: Fetch countries
    print("Fetching countries...")
    countries = publisher.get_countries()
    print(f"Found {len(countries['data'])} countries\n")

    # Example 4: Health check
    print("Performing health check...")
    health = publisher.health_check()
    print(f"Health status: {health['status']}\n")

except KlinkException as e:
    print(f"Error: {e}")
    exit(1)
