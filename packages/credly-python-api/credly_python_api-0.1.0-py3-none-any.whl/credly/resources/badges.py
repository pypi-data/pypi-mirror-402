"""Badges resource for Credly API."""

from typing import Any, Dict, Iterator, Optional

from .base import BaseResource


class Badges(BaseResource):
    """Manage issued badges."""

    def list(
        self,
        organization_id: str,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        List issued badges for an organization.

        Args:
            organization_id: The organization ID
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Badge data dictionaries

        Example:
            >>> for badge in client.badges.list("org123"):
            ...     print(badge['id'], badge['recipient_email'])
        """
        path = f"/v1/organizations/{organization_id}/badges"
        return self._paginate(path, page=page, per=per)

    def get(self, organization_id: str, badge_id: str) -> Dict[str, Any]:
        """
        Get a specific issued badge.

        Args:
            organization_id: The organization ID
            badge_id: The badge ID

        Returns:
            Badge data dictionary

        Example:
            >>> badge = client.badges.get("org123", "badge789")
            >>> print(badge['recipient_email'])
        """
        path = f"/v1/organizations/{organization_id}/badges/{badge_id}"
        response = self.http.get(path)
        return response.get("data", response)

    def issue(self, organization_id: str, **kwargs) -> Dict[str, Any]:
        """
        Issue a new badge.

        Args:
            organization_id: The organization ID
            **kwargs: Badge data (badge_template_id, recipient_email, issued_at, etc.)

        Returns:
            Issued badge data

        Example:
            >>> badge = client.badges.issue(
            ...     "org123",
            ...     badge_template_id="template456",
            ...     recipient_email="user@example.com",
            ...     issued_at="2024-01-15"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badges"
        response = self.http.post(path, data=kwargs)
        return response.get("data", response)

    def delete(self, organization_id: str, badge_id: str) -> Dict[str, Any]:
        """
        Delete an issued badge.

        Args:
            organization_id: The organization ID
            badge_id: The badge ID

        Returns:
            Deletion response

        Example:
            >>> client.badges.delete("org123", "badge789")
        """
        path = f"/v1/organizations/{organization_id}/badges/{badge_id}"
        return self.http.delete(path)

    def replace(self, organization_id: str, badge_id: str, **kwargs) -> Dict[str, Any]:
        """
        Replace an issued badge.

        Args:
            organization_id: The organization ID
            badge_id: The badge ID to replace
            **kwargs: New badge data

        Returns:
            Replacement badge data

        Example:
            >>> badge = client.badges.replace(
            ...     "org123",
            ...     "badge789",
            ...     badge_template_id="new_template",
            ...     recipient_email="user@example.com"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badges/{badge_id}/replace"
        response = self.http.post(path, data=kwargs)
        return response.get("data", response)

    def revoke(self, organization_id: str, badge_id: str, **kwargs) -> Dict[str, Any]:
        """
        Revoke an issued badge.

        Args:
            organization_id: The organization ID
            badge_id: The badge ID to revoke
            **kwargs: Revocation data (reason, etc.)

        Returns:
            Revoked badge data

        Example:
            >>> badge = client.badges.revoke(
            ...     "org123",
            ...     "badge789",
            ...     reason="No longer valid"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badges/{badge_id}/revoke"
        response = self.http.put(path, data=kwargs)
        return response.get("data", response)

    def bulk_search(self, organization_id: str, **kwargs) -> Dict[str, Any]:
        """
        High-volume search for badges.

        Args:
            organization_id: The organization ID
            **kwargs: Search criteria

        Returns:
            Search results

        Example:
            >>> results = client.badges.bulk_search(
            ...     "org123",
            ...     badge_template_id="template456",
            ...     state="accepted"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/badges/bulk_search"
        response = self.http.post(path, data=kwargs)
        return response.get("data", response)
