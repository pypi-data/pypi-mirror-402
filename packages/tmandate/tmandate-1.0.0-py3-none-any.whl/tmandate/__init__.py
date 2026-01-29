"""
TMANDATE Python SDK

Protocol-focused execution authority SDK.
Three views of the same API response.
"""

import os
from typing import Optional
from .client import TMandateClient, TMandateError, AuthenticationError, APIError, NetworkError
from .protocol import ExecutionPermit, ExecutionLimitExceeded, extract_verdict, extract_advisory, extract_authority

# Re-export for convenience
__all__ = [
    "check",
    "advisory",
    "authority",
    "ExecutionPermit",
    "TMandateError",
    "AuthenticationError",
    "APIError",
    "NetworkError",
    "ExecutionLimitExceeded"
]

# Global client instance (lazy initialization)
_client: Optional[TMandateClient] = None


def _get_client() -> TMandateClient:
    """Get or create global client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("TMANDATE_API_KEY")
        base_url = os.getenv("TMANDATE_BASE_URL", "http://localhost:8000")
        _client = TMandateClient(api_key=api_key, base_url=base_url)
    return _client


def _safe_print(text: str) -> None:
    """
    Print text with Unicode-safe fallback for Windows console (cp1252).
    
    If Unicode cannot be printed, degrade gracefully to ASCII for stdout only.
    The returned string from functions remains unchanged.
    """
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode("ascii", errors="replace").decode())


def check(target: str, intent: str = "browse") -> str:
    """
    Check mode - authoritative, compliance-focused verdict.
    
    Returns human-readable verdict string and prints to stdout.
    
    Args:
        target: Target domain
        intent: Intent of the action (default: "browse")
        
    Returns:
        Formatted verdict string
        
    Raises:
        AuthenticationError: If API key is invalid
        APIError: If API returns error
        NetworkError: If network request fails
    """
    client = _get_client()
    response = client._request(target, intent)
    verdict = extract_verdict(response)
    _safe_print(verdict)
    return verdict


def advisory(target: str, intent: str = "browse") -> str:
    """
    Advisory mode - urgent, interpreted risk intelligence.
    
    Returns human-readable advisory string and prints to stdout.
    
    Args:
        target: Target domain
        intent: Intent of the action (default: "browse")
        
    Returns:
        Formatted advisory string
        
    Raises:
        AuthenticationError: If API key is invalid
        APIError: If API returns error
        NetworkError: If network request fails
    """
    client = _get_client()
    response = client._request(target, intent)
    advice = extract_advisory(response)
    _safe_print(advice)
    return advice


def authority(target: str, intent: str = "browse") -> ExecutionPermit:
    """
    Authority mode - machine-readable execution control.
    
    Returns ExecutionPermit context manager for client-side enforcement.
    
    Args:
        target: Target domain
        intent: Intent of the action (default: "browse")
        
    Returns:
        ExecutionPermit context manager
        
    Raises:
        AuthenticationError: If API key is invalid
        APIError: If API returns error
        NetworkError: If network request fails
        
    Example:
        with authority("google.com") as permit:
            permit.step()
            if permit.needs_checkpoint():
                permit.checkpoint()
    """
    client = _get_client()
    response = client._request(target, intent)
    authority_dict = extract_authority(response)
    return ExecutionPermit(authority_dict)
