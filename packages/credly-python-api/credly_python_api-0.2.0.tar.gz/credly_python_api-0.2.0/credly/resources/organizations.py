"""Organizations resource for Credly API."""

from typing import Iterator

from .base import BaseResource, ResourceData


class Organizations(BaseResource):
    """Manage organizations."""

    def list(self) -> Iterator[ResourceData]:
        """
        List all organizations.

        Yields:
            Organization ResourceData objects with dot notation access

        Example:
            >>> for org in client.organizations.list():
            ...     print(org.id, org.name)
        """
        return self._paginate("/v1/organizations")

    def get(self, organization_id: str) -> ResourceData:
        """
        Get a specific organization by ID.

        Args:
            organization_id: The organization ID

        Returns:
            Organization ResourceData object with dot notation access

        Example:
            >>> org = client.organizations.get("org123")
            >>> print(org.name)
        """
        path = f"/v1/organizations/{organization_id}"
        response = self.http.get(path)
        return self._wrap(response.get("data", response))

    def update(self, organization_id: str, **kwargs) -> ResourceData:
        """
        Update an organization.

        Args:
            organization_id: The organization ID
            **kwargs: Fields to update (e.g., name, description, etc.)

        Returns:
            Updated organization ResourceData object with dot notation access

        Example:
            >>> org = client.organizations.update(
            ...     "org123",
            ...     name="New Name",
            ...     description="New description"
            ... )
        """
        path = f"/v1/organizations/{organization_id}"
        response = self.http.put(path, data=kwargs)
        return self._wrap(response.get("data", response))
