"""
HTTP client for Klink SDK
"""
import requests
from typing import Any, Dict, Optional
from ..types import (
    Config,
    KlinkAPIException,
    KlinkAuthException,
    KlinkNetworkException,
)
from ..utils import Logger


class HttpClient:
    """HTTP client with authentication and error handling"""
    
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update(self._build_headers())
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request
        
        Args:
            path: API endpoint path
            params: Query parameters
            
        Returns:
            Response data as dictionary
        """
        return self._request("GET", path, params=params)
    
    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a POST request
        
        Args:
            path: API endpoint path
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        return self._request("POST", path, json=data)
    
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request with error handling
        
        Args:
            method: HTTP method
            path: API endpoint path
            params: Query parameters
            json: Request body data
            
        Returns:
            Response data as dictionary
            
        Raises:
            KlinkAuthException: For authentication errors
            KlinkAPIException: For API errors
            KlinkNetworkException: For network errors
        """
        url = f"{self.config.base_url}{path}"
        
        self.logger.debug(f"Making {method} request", {
            "url": url,
            "params": params,
            "json": json,
        })
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                timeout=self.config.timeout_seconds,
            )
            
            self.logger.debug("Response received", {
                "status_code": response.status_code,
                "body": response.text[:200],  # First 200 chars
            })
            
            # Raise for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            try:
                data = response.json()
            except ValueError:
                raise KlinkAPIException(
                    "Invalid JSON response from API",
                    response.status_code
                )
            
            return data
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            
            self.logger.error("Request failed", {
                "error": str(e),
                "status_code": status_code,
            })
            
            if status_code in (401, 403):
                raise KlinkAuthException(
                    "Authentication failed. Please check your API credentials."
                )
            
            if 400 <= status_code < 500:
                raise KlinkAPIException(
                    f"API error: {str(e)}",
                    status_code
                )
            
            if status_code >= 500:
                raise KlinkAPIException(
                    f"Server error: {str(e)}",
                    status_code
                )
            
        except requests.exceptions.RequestException as e:
            self.logger.error("Network error", {"error": str(e)})
            raise KlinkNetworkException(f"Network error: {str(e)}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        
        if self.config.api_secret:
            headers["X-API-Secret"] = self.config.api_secret
        
        return headers
