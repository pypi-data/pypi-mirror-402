"""Main Credly API client."""

from .http import HTTPClient
from .resources import (
    AuthorizationTokens,
    Badges,
    BadgeTemplates,
    Employees,
    IssuerAuthorizations,
    Organizations,
)


class Client:
    """
    Credly API client.

    This is the main entry point for interacting with the Credly API.

    Example:
        >>> from credly import Client
        >>> client = Client(api_key="your_api_key")
        >>> for org in client.organizations.list():
        ...     print(org['name'])
    """

    def __init__(self, api_key: str, base_url: str = "https://api.credly.com"):
        """
        Initialize the Credly API client.

        Args:
            api_key: Your Credly API key
            base_url: Base URL for the API (default: https://api.credly.com)

        Example:
            >>> client = Client(api_key="your_api_key")
        """
        self.http = HTTPClient(api_key, base_url)

        # Initialize all resource endpoints
        self.organizations = Organizations(self.http)
        self.badge_templates = BadgeTemplates(self.http)
        self.badges = Badges(self.http)
        self.employees = Employees(self.http)
        self.authorization_tokens = AuthorizationTokens(self.http)
        self.issuer_authorizations = IssuerAuthorizations(self.http)
