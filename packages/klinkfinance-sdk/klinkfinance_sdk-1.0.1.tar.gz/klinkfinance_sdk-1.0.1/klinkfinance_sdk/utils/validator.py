"""
Configuration validator for Klink SDK
"""
from typing import Any, Dict
from ..types.exceptions import KlinkConfigException


class Validator:
    """Configuration validation"""
    
    @staticmethod
    def validate_config(config: Dict[str, Any]) -> None:
        """
        Validate SDK configuration
        
        Args:
            config: Configuration dictionary
            
        Raises:
            KlinkConfigException: If configuration is invalid
        """
        if not config.get("api_key"):
            raise KlinkConfigException("API key is required")
        
        if not isinstance(config["api_key"], str):
            raise KlinkConfigException("API key must be a string")
        
        if "api_secret" in config and config["api_secret"] is not None:
            if not isinstance(config["api_secret"], str):
                raise KlinkConfigException("API secret must be a string")
        
        if "base_url" in config:
            if not isinstance(config["base_url"], str):
                raise KlinkConfigException("Base URL must be a string")
            
            if not config["base_url"].startswith(("http://", "https://")):
                raise KlinkConfigException("Base URL must be a valid URL")
        
        if "timeout_ms" in config:
            if not isinstance(config["timeout_ms"], int):
                raise KlinkConfigException("Timeout must be an integer")
            
            if config["timeout_ms"] <= 0:
                raise KlinkConfigException("Timeout must be positive")
        
        if "debug" in config and not isinstance(config["debug"], bool):
            raise KlinkConfigException("Debug must be a boolean")
