"""Badge Templates resource for Credly API."""

from typing import Iterator, Optional

from .base import BaseResource, ResourceData


class BadgeTemplates(BaseResource):
    """Manage badge templates."""

    def list(
        self,
        organization_id: str,
        page: Optional[int] = None,
        per: Optional[int] = None,
        filter: Optional[str] = None,
        sort: Optional[str] = None,
    ) -> Iterator[ResourceData]:
        """
        List badge templates for an organization.

        Args:
            organization_id: The organization ID
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page
            filter: Filter criteria
            sort: Sort order

        Yields:
            Badge template ResourceData objects with dot notation access

        Example:
            >>> for template in client.badge_templates.list("org123"):
            ...     print(template.id, template.name)
        """
        path = f"/v1/organizations/{organization_id}/badge_templates"
        params = {}
        if filter:
            params["filter"] = filter
        if sort:
            params["sort"] = sort

        return self._paginate(path, params=params, page=page, per=per)

    def get(self, organization_id: str, badge_template_id: str) -> ResourceData:
        """
        Get a specific badge template.

        Args:
            organization_id: The organization ID
            badge_template_id: The badge template ID

        Returns:
            Badge template ResourceData object with dot notation access

        Example:
            >>> template = client.badge_templates.get("org123", "template456")
            >>> print(template.name)
        """
        path = f"/v1/organizations/{organization_id}/badge_templates/{badge_template_id}"
        response = self.http.get(path)
        return self._wrap(response.get("data", response))

    def create(
        self, organization_id: str, name: str, description: str, image: str, **kwargs
    ) -> ResourceData:
        """
        Create a new badge template.

        Args:
            organization_id: The organization ID
            name: Badge template name
            description: Badge template description
            image: Badge template image URL or data
            **kwargs: Additional fields (skills, activities, alignment, etc.)

        Returns:
            Created badge template ResourceData object with dot notation access

        Example:
            >>> template = client.badge_templates.create(
            ...     "org123",
            ...     name="Python Expert",
            ...     description="Awarded for Python expertise",
            ...     image="https://example.com/badge.png",
            ...     skills=["Python", "Django"]
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badge_templates"
        data = {"name": name, "description": description, "image": image, **kwargs}
        response = self.http.post(path, data=data)
        return self._wrap(response.get("data", response))

    def update(self, organization_id: str, badge_template_id: str, **kwargs) -> ResourceData:
        """
        Update a badge template.

        Args:
            organization_id: The organization ID
            badge_template_id: The badge template ID
            **kwargs: Fields to update

        Returns:
            Updated badge template ResourceData object with dot notation access

        Example:
            >>> template = client.badge_templates.update(
            ...     "org123",
            ...     "template456",
            ...     name="Updated Name"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badge_templates/{badge_template_id}"
        response = self.http.put(path, data=kwargs)
        return self._wrap(response.get("data", response))

    def delete(self, organization_id: str, badge_template_id: str) -> ResourceData:
        """
        Delete a badge template.

        Args:
            organization_id: The organization ID
            badge_template_id: The badge template ID

        Returns:
            Deletion response as ResourceData object

        Example:
            >>> client.badge_templates.delete("org123", "template456")
        """
        path = f"/v1/organizations/{organization_id}/badge_templates/{badge_template_id}"
        return self._wrap(self.http.delete(path))
