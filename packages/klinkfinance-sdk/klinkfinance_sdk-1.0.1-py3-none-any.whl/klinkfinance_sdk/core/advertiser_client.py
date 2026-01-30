"""
Advertiser API client for Klink SDK
"""
from typing import Any, Dict
from ..utils import Logger
from .http_client import HttpClient


class AdvertiserClient:
    """Advertiser API client"""
    
    def __init__(self, http_client: HttpClient, logger: Logger, api_key: str):
        self.http_client = http_client
        self.logger = logger
        self.api_key = api_key
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health status response
        """
        self.logger.info("Performing health check")
        return self.http_client.get("/health")
    
    def send_postback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send postback
        
        Args:
            data: Postback data with required fields:
                - event_name: Event name
                - offer_id: Offer ID
                - sub1: Sub1 parameter
                - tx_id: Transaction ID
                - isChargeback: Whether this is a chargeback
                - chargebackReason: Chargeback reason
                - isTest: Whether this is a test postback
        
        Returns:
            Response from postback endpoint
            
        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        required_fields = [
            "event_name",
            "offer_id",
            "sub1",
            "tx_id",
            "isChargeback",
            "chargebackReason",
            "isTest"
        ]
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        self.logger.info("Sending postback", data)
        
        # Use apiKey as advertiserId in the route
        return self.http_client.post(
            f"/v1/advertiser/{self.api_key}/postback",
            data
        )
