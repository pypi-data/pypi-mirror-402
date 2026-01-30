"""
Klink Finance SDK - Main SDK class
"""
from typing import Optional
from .types import Config
from .core import HttpClient, PublisherClient, AdvertiserClient
from .utils import Logger, Validator


class KlinkSDK:
    """Main SDK class for Klink Finance API"""
    
    def __init__(self, config: Config):
        """
        Initialize SDK (use create() factory method instead)
        
        Args:
            config: SDK configuration
        """
        self.config = config
        self.logger = Logger(config.debug)
        self.http_client = HttpClient(config, self.logger)
        self._publisher_client: Optional[PublisherClient] = None
        self._advertiser_client: Optional[AdvertiserClient] = None
        
        self.logger.info("Klink SDK initialized", {
            "base_url": config.base_url,
            "debug": config.debug,
        })
    
    @classmethod
    def create(cls, config_dict: dict) -> "KlinkSDK":
        """
        Create SDK instance with health check
        
        Args:
            config_dict: Configuration dictionary with keys:
                - api_key: API key (required)
                - api_secret: API secret (optional for Advertiser, required for Publisher)
                - base_url: Base API URL (optional)
                - timeout_ms: Request timeout in milliseconds (optional)
                - debug: Enable debug logging (optional)
        
        Returns:
            Initialized SDK instance
            
        Raises:
            Exception: If health check fails or configuration is invalid
        """
        # Validate configuration
        Validator.validate_config(config_dict)
        
        # Create config object
        config = Config(
            api_key=config_dict["api_key"],
            api_secret=config_dict.get("api_secret"),
            base_url=config_dict.get("base_url", "https://klink-quest.klink.finance/api"),
            timeout_ms=config_dict.get("timeout_ms", 8000),
            debug=config_dict.get("debug", False),
        )
        
        # Create temporary instance for health check
        logger = Logger(config.debug)
        http_client = HttpClient(config, logger)
        
        # Perform health check
        try:
            logger.info("Performing health check before initialization")
            health = http_client.get("/health")
            
            if health.get("status") != "ok":
                raise Exception("Health check failed: Invalid status")
            
            logger.info("Health check passed")
        except Exception as e:
            logger.error("Health check failed", {"error": str(e)})
            raise Exception(f"Failed to initialize SDK: {str(e)}") from e
        
        # Create and return SDK instance
        return cls(config)
    
    def publisher(self) -> PublisherClient:
        """
        Get Publisher client
        
        Returns:
            Publisher API client
            
        Raises:
            Exception: If API secret is not configured
        """
        if self._publisher_client is None:
            self._publisher_client = PublisherClient(
                self.http_client,
                self.logger,
                self.config.api_secret
            )
        
        return self._publisher_client
    
    def advertiser(self) -> AdvertiserClient:
        """
        Get Advertiser client
        
        Returns:
            Advertiser API client
        """
        if self._advertiser_client is None:
            self._advertiser_client = AdvertiserClient(
                self.http_client,
                self.logger,
                self.config.api_key
            )
        
        return self._advertiser_client
