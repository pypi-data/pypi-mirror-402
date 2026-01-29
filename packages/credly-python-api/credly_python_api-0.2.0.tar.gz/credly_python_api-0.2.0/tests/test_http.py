"""Tests for HTTP client."""

import pytest
import responses

from credly.exceptions import (
    CredlyAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)
from credly.http import HTTPClient


class TestHTTPClientInit:
    """Test HTTPClient initialization."""

    def test_init_with_api_key(self, api_key, base_url):
        """Test HTTPClient initialization with API key."""
        client = HTTPClient(api_key, base_url)
        assert client.api_key == api_key
        assert client.base_url == base_url

    def test_init_with_default_base_url(self, api_key):
        """Test HTTPClient uses default base URL."""
        client = HTTPClient(api_key)
        assert client.base_url == "https://api.credly.com"

    def test_init_strips_trailing_slash(self, api_key):
        """Test HTTPClient strips trailing slash from base URL."""
        client = HTTPClient(api_key, "https://api.credly.com/")
        assert client.base_url == "https://api.credly.com"

    def test_auth_header_set(self, api_key, base_url):
        """Test authentication header is set correctly."""
        client = HTTPClient(api_key, base_url)
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"].startswith("Basic ")


class TestHTTPClientRequests:
    """Test HTTP client request methods."""

    @responses.activate
    def test_get_request_success(self, api_key, base_url):
        """Test successful GET request."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"data": {"id": "123", "name": "Test"}},
            status=200,
        )

        client = HTTPClient(api_key, base_url)
        result = client.get("/v1/test")

        assert result == {"data": {"id": "123", "name": "Test"}}

    @responses.activate
    def test_get_request_with_params(self, api_key, base_url):
        """Test GET request with query parameters."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"data": []},
            status=200,
        )

        client = HTTPClient(api_key, base_url)
        result = client.get("/v1/test", params={"page": 1, "per": 10})

        assert result == {"data": []}
        assert len(responses.calls) == 1
        assert "page=1" in responses.calls[0].request.url
        assert "per=10" in responses.calls[0].request.url

    @responses.activate
    def test_post_request_success(self, api_key, base_url):
        """Test successful POST request."""
        responses.add(
            responses.POST,
            f"{base_url}/v1/test",
            json={"data": {"id": "123", "created": True}},
            status=201,
        )

        client = HTTPClient(api_key, base_url)
        result = client.post("/v1/test", data={"name": "Test"})

        assert result == {"data": {"id": "123", "created": True}}

    @responses.activate
    def test_put_request_success(self, api_key, base_url):
        """Test successful PUT request."""
        responses.add(
            responses.PUT,
            f"{base_url}/v1/test/123",
            json={"data": {"id": "123", "updated": True}},
            status=200,
        )

        client = HTTPClient(api_key, base_url)
        result = client.put("/v1/test/123", data={"name": "Updated"})

        assert result == {"data": {"id": "123", "updated": True}}

    @responses.activate
    def test_delete_request_success(self, api_key, base_url):
        """Test successful DELETE request."""
        responses.add(
            responses.DELETE,
            f"{base_url}/v1/test/123",
            status=204,
        )

        client = HTTPClient(api_key, base_url)
        result = client.delete("/v1/test/123")

        assert result == {}


class TestHTTPClientErrorHandling:
    """Test HTTP client error handling."""

    @responses.activate
    def test_401_raises_unauthorized_error(self, api_key, base_url):
        """Test 401 status raises UnauthorizedError."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"message": "Invalid credentials"},
            status=401,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(UnauthorizedError) as exc_info:
            client.get("/v1/test")

        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in exc_info.value.message

    @responses.activate
    def test_403_raises_forbidden_error(self, api_key, base_url):
        """Test 403 status raises ForbiddenError."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"message": "Access denied"},
            status=403,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(ForbiddenError) as exc_info:
            client.get("/v1/test")

        assert exc_info.value.status_code == 403

    @responses.activate
    def test_404_raises_not_found_error(self, api_key, base_url):
        """Test 404 status raises NotFoundError."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test/999",
            json={"message": "Resource not found"},
            status=404,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(NotFoundError) as exc_info:
            client.get("/v1/test/999")

        assert exc_info.value.status_code == 404

    @responses.activate
    def test_422_raises_validation_error(self, api_key, base_url):
        """Test 422 status raises ValidationError."""
        responses.add(
            responses.POST,
            f"{base_url}/v1/test",
            json={"message": "Validation failed", "errors": ["Name is required"]},
            status=422,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(ValidationError) as exc_info:
            client.post("/v1/test", data={})

        assert exc_info.value.status_code == 422
        assert exc_info.value.response["errors"] == ["Name is required"]

    @responses.activate
    def test_429_raises_rate_limit_error(self, api_key, base_url):
        """Test 429 status raises RateLimitError."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"message": "Too many requests"},
            status=429,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(RateLimitError) as exc_info:
            client.get("/v1/test")

        assert exc_info.value.status_code == 429

    @responses.activate
    def test_500_raises_generic_error(self, api_key, base_url):
        """Test 500 status raises generic CredlyAPIError."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            json={"message": "Internal server error"},
            status=500,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(CredlyAPIError) as exc_info:
            client.get("/v1/test")

        assert exc_info.value.status_code == 500

    @responses.activate
    def test_non_json_response_handled(self, api_key, base_url):
        """Test non-JSON response is handled gracefully."""
        responses.add(
            responses.GET,
            f"{base_url}/v1/test",
            body="Plain text error",
            status=500,
        )

        client = HTTPClient(api_key, base_url)
        with pytest.raises(CredlyAPIError) as exc_info:
            client.get("/v1/test")

        assert exc_info.value.status_code == 500
        assert "Plain text error" in exc_info.value.response["message"]
