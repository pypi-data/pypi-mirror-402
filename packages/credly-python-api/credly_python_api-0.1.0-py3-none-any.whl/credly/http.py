"""HTTP client for Credly API with authentication and error handling."""

import base64
from typing import Any, Dict, Optional

import requests

from .exceptions import (
    CredlyAPIError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)


class HTTPClient:
    """HTTP client for making authenticated requests to Credly API."""

    def __init__(self, api_key: str, base_url: str = "https://api.credly.com"):
        """
        Initialize the HTTP client.

        Args:
            api_key: The API key for authentication
            base_url: Base URL for the Credly API (default: https://api.credly.com)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self):
        """Set up Basic Authentication headers."""
        # Credly uses Basic Auth with format: Base64(token:)
        credentials = f"{self.api_key}:"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update(
            {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        )

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response and raise appropriate exceptions.

        Args:
            response: The response object from requests

        Returns:
            Parsed JSON response data

        Raises:
            UnauthorizedError: For 401 status codes
            ForbiddenError: For 403 status codes
            NotFoundError: For 404 status codes
            ValidationError: For 422 status codes
            RateLimitError: For 429 status codes
            CredlyAPIError: For other error status codes
        """
        try:
            data = response.json()
        except ValueError:
            data = {"message": response.text}

        if response.status_code == 200 or response.status_code == 201:
            return data
        elif response.status_code == 204:
            return {}
        elif response.status_code == 401:
            raise UnauthorizedError(
                data.get("message", "Unauthorized"), status_code=401, response=data
            )
        elif response.status_code == 403:
            raise ForbiddenError(data.get("message", "Forbidden"), status_code=403, response=data)
        elif response.status_code == 404:
            raise NotFoundError(data.get("message", "Not Found"), status_code=404, response=data)
        elif response.status_code == 422:
            raise ValidationError(
                data.get("message", "Validation Error"), status_code=422, response=data
            )
        elif response.status_code == 429:
            raise RateLimitError(
                data.get("message", "Rate Limit Exceeded"), status_code=429, response=data
            )
        else:
            raise CredlyAPIError(
                data.get("message", f"API Error: {response.status_code}"),
                status_code=response.status_code,
                response=data,
            )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a GET request.

        Args:
            path: API endpoint path
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{path}"
        response = self.session.get(url, params=params)
        return self._handle_response(response)

    def post(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a POST request.

        Args:
            path: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{path}"
        response = self.session.post(url, json=data)
        return self._handle_response(response)

    def put(self, path: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make a PUT request.

        Args:
            path: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{path}"
        response = self.session.put(url, json=data)
        return self._handle_response(response)

    def delete(self, path: str) -> Dict[str, Any]:
        """
        Make a DELETE request.

        Args:
            path: API endpoint path

        Returns:
            Parsed JSON response
        """
        url = f"{self.base_url}{path}"
        response = self.session.delete(url)
        return self._handle_response(response)
