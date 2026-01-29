"""Tests for main Client class."""

from credly import Client
from credly.http import HTTPClient
from credly.resources import (
    AuthorizationTokens,
    Badges,
    BadgeTemplates,
    Employees,
    IssuerAuthorizations,
    Organizations,
)


class TestClientInit:
    """Test Client initialization."""

    def test_client_init_with_api_key(self, api_key):
        """Test Client initializes with API key."""
        client = Client(api_key=api_key)
        assert client.http.api_key == api_key

    def test_client_init_with_custom_base_url(self, api_key):
        """Test Client initializes with custom base URL."""
        custom_url = "https://custom.api.com"
        client = Client(api_key=api_key, base_url=custom_url)
        assert client.http.base_url == custom_url

    def test_client_init_with_default_base_url(self, api_key):
        """Test Client uses default base URL."""
        client = Client(api_key=api_key)
        assert client.http.base_url == "https://api.credly.com"

    def test_client_has_http_instance(self, client):
        """Test Client has HTTPClient instance."""
        assert isinstance(client.http, HTTPClient)


class TestClientResources:
    """Test Client resource attributes."""

    def test_client_has_organizations_resource(self, client):
        """Test Client has organizations resource."""
        assert hasattr(client, "organizations")
        assert isinstance(client.organizations, Organizations)

    def test_client_has_badge_templates_resource(self, client):
        """Test Client has badge_templates resource."""
        assert hasattr(client, "badge_templates")
        assert isinstance(client.badge_templates, BadgeTemplates)

    def test_client_has_badges_resource(self, client):
        """Test Client has badges resource."""
        assert hasattr(client, "badges")
        assert isinstance(client.badges, Badges)

    def test_client_has_employees_resource(self, client):
        """Test Client has employees resource."""
        assert hasattr(client, "employees")
        assert isinstance(client.employees, Employees)

    def test_client_has_authorization_tokens_resource(self, client):
        """Test Client has authorization_tokens resource."""
        assert hasattr(client, "authorization_tokens")
        assert isinstance(client.authorization_tokens, AuthorizationTokens)

    def test_client_has_issuer_authorizations_resource(self, client):
        """Test Client has issuer_authorizations resource."""
        assert hasattr(client, "issuer_authorizations")
        assert isinstance(client.issuer_authorizations, IssuerAuthorizations)

    def test_all_resources_share_same_http_client(self, client):
        """Test all resources use the same HTTPClient instance."""
        assert client.organizations.http is client.http
        assert client.badge_templates.http is client.http
        assert client.badges.http is client.http
        assert client.employees.http is client.http
        assert client.authorization_tokens.http is client.http
        assert client.issuer_authorizations.http is client.http
