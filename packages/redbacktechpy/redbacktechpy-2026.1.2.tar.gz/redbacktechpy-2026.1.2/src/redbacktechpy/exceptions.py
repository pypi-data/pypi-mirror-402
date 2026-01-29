"""Exceptions for RedbackTech"""

from typing import Any

class AuthError(Exception):
    """Authentication issue from Redback api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)
        
class RedbackTechClientError(Exception):
    """Error from Redback api."""

    def __init__(self, *args: Any) -> None:
        """Initialize the exception."""
        Exception.__init__(self, *args)