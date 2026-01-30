"""
Publisher API client for Klink SDK
"""
from typing import Any, Dict, Optional
from ..types import KlinkConfigException
from ..utils import Logger
from .http_client import HttpClient


class PublisherClient:
    """Publisher API client"""
    
    def __init__(
        self,
        http_client: HttpClient,
        logger: Logger,
        api_secret: Optional[str]
    ):
        if not api_secret:
            raise KlinkConfigException(
                "API secret is required for Publisher API access"
            )
        
        self.http_client = http_client
        self.logger = logger
        self.api_secret = api_secret
    
    def get_offers(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch offers with optional filters
        
        Args:
            params: Query parameters for filtering offers
            
        Returns:
            Response containing offers data
        """
        self.logger.info("Fetching offers", params or {})
        return self.http_client.get("/v1/publisher/offers", params)
    
    def get_conversions(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch conversions with optional filters
        
        Args:
            params: Query parameters for filtering conversions
            
        Returns:
            Response containing conversions data
        """
        self.logger.info("Fetching conversions", params or {})
        return self.http_client.get("/v1/publisher/conversions", params)
    
    def get_users(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch publisher users
        
        Args:
            params: Query parameters for filtering users
            
        Returns:
            Response containing users data
        """
        self.logger.info("Fetching users", params or {})
        return self.http_client.get("/v1/publisher/users", params)
    
    def get_postbacks(self, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Fetch postback logs
        
        Args:
            params: Query parameters for filtering postbacks
            
        Returns:
            Response containing postback logs
        """
        self.logger.info("Fetching postbacks", params or {})
        return self.http_client.get("/v1/publisher/postbacks", params)
    
    def get_countries(self, reload: bool = False) -> Dict[str, Any]:
        """
        Fetch supported countries
        
        Args:
            reload: Force reload from source
            
        Returns:
            Response containing countries data
        """
        params = {"reload": reload} if reload else None
        self.logger.info("Fetching countries", params or {})
        return self.http_client.get("/v1/publisher/countries", params)
    
    def get_categories(self, reload: bool = False) -> Dict[str, Any]:
        """
        Fetch supported categories
        
        Args:
            reload: Force reload from source
            
        Returns:
            Response containing categories data
        """
        params = {"reload": reload} if reload else None
        self.logger.info("Fetching categories", params or {})
        return self.http_client.get("/v1/publisher/categories", params)
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check
        
        Returns:
            Health status response
        """
        self.logger.info("Performing health check")
        return self.http_client.get("/health")
    
    def send_test_postback(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send test postback
        
        Args:
            data: Postback data with params
            
        Returns:
            Response from postback endpoint
        """
        self.logger.info("Sending test postback", data)
        return self.http_client.post("/v1/publisher/postback/test", data)
