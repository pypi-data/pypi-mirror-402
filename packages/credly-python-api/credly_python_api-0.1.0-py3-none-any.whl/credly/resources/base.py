"""Base resource class with common functionality."""

from typing import Any, Dict, Iterator, Optional


class BaseResource:
    """Base class for API resources."""

    def __init__(self, http_client):
        """
        Initialize the resource.

        Args:
            http_client: HTTPClient instance for making API requests
        """
        self.http = http_client

    def _paginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        Iterate over paginated results.

        Args:
            path: API endpoint path
            params: Additional query parameters
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Individual items from the paginated response
        """
        params = params or {}

        if per is not None:
            params["per"] = per

        # If specific page requested, fetch only that page
        if page is not None:
            params["page"] = page
            response = self.http.get(path, params=params)
            data = response.get("data", [])
            for item in data:
                yield item
            return

        # Otherwise, iterate through all pages
        current_page = 1
        while True:
            params["page"] = current_page
            response = self.http.get(path, params=params)
            data = response.get("data", [])

            if not data:
                break

            for item in data:
                yield item

            # Check if there are more pages
            metadata = response.get("metadata", {})
            if current_page >= metadata.get("total_pages", current_page):
                break

            current_page += 1
