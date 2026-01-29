"""Base resource class with common functionality."""

from typing import Any, Dict, Iterator, Optional


class ResourceData:
    """Wrapper class that allows dot notation access to dictionary data."""

    def __init__(self, data: Dict[str, Any]):
        """
        Initialize ResourceData with a dictionary.

        Args:
            data: Dictionary containing the resource data
        """
        self._data = data

    def __getattr__(self, name: str) -> Any:
        """
        Allow attribute-style access to dictionary keys.

        Args:
            name: The attribute/key name

        Returns:
            The value associated with the key

        Raises:
            AttributeError: If the key doesn't exist
        """
        if name.startswith("_"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __getitem__(self, key):
        """
        Allow dictionary-style or list-style access for backward compatibility.

        Args:
            key: The dictionary key or list index

        Returns:
            The value associated with the key/index
        """
        result = self._data[key]
        # If the result is a dict, wrap it in ResourceData for chaining
        if isinstance(result, dict):
            return ResourceData(result)
        return result

    def __setitem__(self, key, value: Any) -> None:
        """
        Allow dictionary-style or list-style assignment.

        Args:
            key: The dictionary key or list index
            value: The value to set
        """
        self._data[key] = value

    def __contains__(self, key) -> bool:
        """
        Check if a key exists in the data.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._data

    def __repr__(self) -> str:
        """Return string representation of the resource data."""
        return f"ResourceData({self._data})"

    def __eq__(self, other: Any) -> bool:
        """
        Compare ResourceData with another object.

        Args:
            other: The object to compare with

        Returns:
            True if equal, False otherwise
        """
        if isinstance(other, ResourceData):
            return self._data == other._data
        if isinstance(other, dict):
            return self._data == other
        return False

    def __len__(self) -> int:
        """
        Return the length of the underlying data.

        Returns:
            Length of the data (for lists/dicts)
        """
        return len(self._data)

    def __iter__(self):
        """
        Make ResourceData iterable if underlying data is a list.

        Yields:
            Wrapped items if data is a list, otherwise iterates dict keys
        """
        if isinstance(self._data, list):
            for item in self._data:
                if isinstance(item, dict):
                    yield ResourceData(item)
                else:
                    yield item
        else:
            # For dict, iterate over keys (standard dict behavior)
            yield from self._data

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value with a default fallback.

        Args:
            key: The key to retrieve
            default: Default value if key doesn't exist

        Returns:
            The value or default
        """
        return self._data.get(key, default)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert back to a plain dictionary.

        Returns:
            The underlying dictionary data
        """
        return self._data


class BaseResource:
    """Base class for API resources."""

    def __init__(self, http_client):
        """
        Initialize the resource.

        Args:
            http_client: HTTPClient instance for making API requests
        """
        self.http = http_client

    def _wrap(self, data: Dict[str, Any]) -> ResourceData:
        """
        Wrap dictionary data in a ResourceData object.

        Args:
            data: Dictionary to wrap

        Returns:
            ResourceData object with dot notation access
        """
        return ResourceData(data)

    def _paginate(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[ResourceData]:
        """
        Iterate over paginated results.

        Args:
            path: API endpoint path
            params: Additional query parameters
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Individual items from the paginated response as ResourceData objects
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
                yield self._wrap(item)
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
                yield self._wrap(item)

            # Check if there are more pages
            metadata = response.get("metadata", {})
            if current_page >= metadata.get("total_pages", current_page):
                break

            current_page += 1
