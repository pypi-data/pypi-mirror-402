"""
Exception classes for Klink SDK
"""
from typing import Any, Dict, Optional


class KlinkException(Exception):
    """Base exception class for all Klink SDK errors"""
    pass


class KlinkConfigException(KlinkException):
    """Configuration validation errors"""
    pass


class KlinkAuthException(KlinkException):
    """Authentication and authorization errors"""
    pass


class KlinkAPIException(KlinkException):
    """API errors with status codes"""
    
    def __init__(
        self,
        message: str,
        status_code: int,
        response_data: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class KlinkNetworkException(KlinkException):
    """Network and connectivity errors"""
    pass
