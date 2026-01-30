"""
Configuration class for Klink SDK
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """SDK configuration"""
    
    api_key: str
    api_secret: Optional[str] = None
    base_url: str = "https://klink-quest.klink.finance/api"
    timeout_ms: int = 8000
    debug: bool = False
    
    @property
    def timeout_seconds(self) -> float:
        """Get timeout in seconds"""
        return self.timeout_ms / 1000
