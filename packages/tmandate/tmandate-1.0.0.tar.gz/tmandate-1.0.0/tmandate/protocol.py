"""
Protocol view extractors and ExecutionPermit.

All extractors read the SAME API response.
Different views, same data.
"""

from typing import Dict, Any
from .types import CheckResponse
from .formatters import (
    format_check_mode,
    format_advisory_mode,
    format_authority_mode
)


class ExecutionLimitExceeded(Exception):
    """Step count exceeded max_continuous_steps."""
    pass


class ExecutionPermit:
    """
    Context manager for execution authority enforcement.
    
    Client-side enforcement only. TMANDATE API remains advisory.
    """
    
    def __init__(self, authority_dict: Dict[str, Any]):
        """
        Initialize permit from authority mode output.
        
        Args:
            authority_dict: Output from authority() mode (machine-readable dict)
        """
        self.authority = authority_dict
        self.step_count = 0
        self.max_steps = authority_dict.get("max_continuous_steps", 20)
        # FIX 2: NO strategy field - only use authority_level, execution_verdict, max_continuous_steps
    
    def step(self):
        """
        Track execution step.
        
        Raises:
            ExecutionLimitExceeded: If step count exceeds max_continuous_steps
        """
        self.step_count += 1
        if self.step_count > self.max_steps:
            raise ExecutionLimitExceeded(
                f"Exceeded {self.max_steps} continuous steps. "
                f"Checkpoint required (authority_level: {self.authority.get('authority_level')})"
            )
    
    def needs_checkpoint(self) -> bool:
        """
        Check if checkpoint is needed based on authority strictness.
        
        FIX 1: Uses authority_level, not strategy string.
        Checkpointing is implied by strict authority + step limit.
        
        Returns:
            True if authority_level == "strict" AND step_count >= max_steps
        """
        authority_level = self.authority.get("authority_level") if self.authority else None
        return (
            authority_level == "strict"
            and self.step_count >= self.max_steps
        )
    
    def checkpoint(self):
        """
        Reset step counter after checkpoint.
        
        Call this when agent performs checkpoint action (re-observation).
        """
        self.step_count = 0
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        
        Optional micro-nit: Allow passthrough of exceptions.
        """
        return False


def extract_verdict(response: CheckResponse) -> str:
    """
    Extract verdict view (check mode).
    
    Returns formatted string for compliance/authority view.
    """
    return format_check_mode(response)


def extract_advisory(response: CheckResponse) -> str:
    """
    Extract advisory view (advisory mode).
    
    Returns formatted string for urgency/memory view.
    """
    return format_advisory_mode(response)


def extract_authority(response: CheckResponse) -> Dict[str, Any]:
    """
    Extract authority view (authority mode).
    
    Returns machine-readable dict for execution control.
    """
    return format_authority_mode(response)
