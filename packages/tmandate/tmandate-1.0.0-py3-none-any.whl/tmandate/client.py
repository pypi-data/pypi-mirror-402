"""
HTTP client for TMANDATE API.

Single client instance, no business logic.
"""

import os
import requests
from typing import Optional
from .types import CheckResponse


class TMandateError(Exception):
    """Base exception for TMANDATE SDK."""
    pass


class AuthenticationError(TMandateError):
    """API key authentication failed (401)."""
    pass


class APIError(TMandateError):
    """API returned error (500)."""
    pass


class NetworkError(TMandateError):
    """Network connection error."""
    pass


class TMandateClient:
    """HTTP client for TMANDATE API."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:8000"):
        """
        Initialize TMANDATE client.
        
        Args:
            api_key: API key (required, must be provided or set via TMANDATE_API_KEY env var)
            base_url: Base URL for API (defaults to http://localhost:8000)
        """
        if api_key is None:
            api_key = os.getenv("TMANDATE_API_KEY")
        
        if not api_key:
            raise AuthenticationError(
                "TMANDATE_API_KEY not set. Set it with: export TMANDATE_API_KEY=tm_live_..."
            )
        
        self.api_key = api_key
        
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        })
    
    def _request(self, target: str, intent: str = "browse") -> CheckResponse:
        """
        Make POST request to /aweo/v1/check endpoint.
        
        Args:
            target: Target domain
            intent: Intent of the action (default: "browse")
            
        Returns:
            CheckResponse dict
            
        Raises:
            AuthenticationError: If API key is invalid (401)
            APIError: If API returns error (400, 404, 500+)
            NetworkError: If network request fails
        """
        url = f"{self.base_url}/aweo/v1/check"
        payload = {
            "target": target,
            "intent": intent
        }
        
        try:
            response = self.session.post(url, json=payload, timeout=30)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 400:
                raise APIError("Bad request: check target/intent")
            elif response.status_code == 404:
                raise APIError("Endpoint not found")
            elif response.status_code >= 500:
                raise APIError(f"API error: {response.status_code} - {response.text}")
            elif response.status_code != 200:
                raise APIError(f"Unexpected status: {response.status_code} - {response.text}")
            
            return response.json()
            
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.Timeout as e:
            raise NetworkError(f"Request timeout: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Network error: {str(e)}")
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {str(e)}")
