"""Shared pytest fixtures for Credly API tests."""

import pytest

from credly import Client


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def base_url():
    """Return the base URL for the API."""
    return "https://api.credly.com"


@pytest.fixture
def client(api_key, base_url):
    """Return a configured Client instance."""
    return Client(api_key=api_key, base_url=base_url)


@pytest.fixture
def org_id():
    """Return a test organization ID."""
    return "org_123"


@pytest.fixture
def badge_template_id():
    """Return a test badge template ID."""
    return "template_456"


@pytest.fixture
def badge_id():
    """Return a test badge ID."""
    return "badge_789"


@pytest.fixture
def employee_id():
    """Return a test employee ID."""
    return "employee_101"
