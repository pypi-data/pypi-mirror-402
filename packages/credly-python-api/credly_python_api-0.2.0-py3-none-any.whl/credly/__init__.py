"""
Credly Python API Client

A clean, resource-based Python SDK for Credly's API v1.

Example:
    >>> from credly import Client
    >>> client = Client(api_key="your_api_key")
    >>> for org in client.organizations.list():
    ...     print(org['name'])
"""

from .client import Client
from .exceptions import (
    CredlyAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)

__version__ = "0.2.0"

__all__ = [
    "Client",
    "CredlyAPIError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
]
