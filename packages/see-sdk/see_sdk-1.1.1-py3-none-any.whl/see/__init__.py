"""
SEE - A modern Python SDK for SEE Content Sharing services.

This package provides a clean and type-safe interface for interacting
with SEE services to manage Short URLs, Text, Files, and more.
"""

from .client import SeeClient
from .exceptions import (
    APIError,
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    SeeError,
    ValidationError,
)
from .version import __version__

__all__ = [
    "APIError",
    "AuthenticationError",
    "NotFoundError",
    "RateLimitError",
    "SeeClient",
    "SeeError",
    "ValidationError",
]
