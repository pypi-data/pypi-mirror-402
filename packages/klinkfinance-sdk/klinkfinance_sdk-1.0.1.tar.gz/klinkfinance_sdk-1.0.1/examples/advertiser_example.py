"""
Advertiser API example for Klink SDK
"""
import os
import uuid
from klinkfinance_sdk import KlinkSDK, KlinkException

try:
    # Initialize SDK with health check
    # API secret is optional for Advertiser
    client = KlinkSDK.create({
        "api_key": os.getenv("KLINK_API_KEY"),
        "debug": True,
    })

    # Get advertiser client
    advertiser = client.advertiser()

    # Example 1: Health check
    print("Performing health check...")
    health = advertiser.health_check()
    print(f"Health status: {health['status']}\n")

    # Example 2: Send postback
    print("Sending postback...")
    response = advertiser.send_postback({
        "event_name": "create_account",
        "offer_id": "offer_123",
        "sub1": "sub1_value",
        "tx_id": f"tx_{uuid.uuid4().hex[:8]}",
        "isChargeback": False,
        "chargebackReason": "",
        "isTest": True,  # Set to True for testing
    })
    
    if response.get("success"):
        print("Postback sent successfully!")

except KlinkException as e:
    print(f"Error: {e}")
    exit(1)
