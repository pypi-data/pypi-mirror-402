"""Organizations resource for Credly API."""

from typing import Any, Dict, Iterator

from .base import BaseResource


class Organizations(BaseResource):
    """Manage organizations."""

    def list(self) -> Iterator[Dict[str, Any]]:
        """
        List all organizations.

        Yields:
            Organization data dictionaries

        Example:
            >>> for org in client.organizations.list():
            ...     print(org['id'], org['name'])
        """
        return self._paginate("/v1/organizations")

    def get(self, organization_id: str) -> Dict[str, Any]:
        """
        Get a specific organization by ID.

        Args:
            organization_id: The organization ID

        Returns:
            Organization data dictionary

        Example:
            >>> org = client.organizations.get("org123")
            >>> print(org['name'])
        """
        path = f"/v1/organizations/{organization_id}"
        response = self.http.get(path)
        return response.get("data", response)

    def update(self, organization_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an organization.

        Args:
            organization_id: The organization ID
            **kwargs: Fields to update (e.g., name, description, etc.)

        Returns:
            Updated organization data

        Example:
            >>> org = client.organizations.update(
            ...     "org123",
            ...     name="New Name",
            ...     description="New description"
            ... )
        """
        path = f"/v1/organizations/{organization_id}"
        response = self.http.put(path, data=kwargs)
        return response.get("data", response)
