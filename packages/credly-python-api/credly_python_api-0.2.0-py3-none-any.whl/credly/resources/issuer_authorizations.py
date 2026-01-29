"""Issuer Authorizations resource for Credly API."""

from typing import Iterator, Optional

from .base import BaseResource, ResourceData


class IssuerAuthorizations(BaseResource):
    """Manage issuer authorizations."""

    def list(
        self,
        organization_id: str,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[ResourceData]:
        """
        List issuer authorizations for an organization.

        Args:
            organization_id: The organization ID
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Issuer authorization ResourceData objects with dot notation access

        Example:
            >>> for auth in client.issuer_authorizations.list("org123"):
            ...     print(auth.id)
        """
        path = f"/v1/organizations/{organization_id}/issuer_authorizations"
        return self._paginate(path, page=page, per=per)

    def get_grantors(self, organization_id: str) -> ResourceData:
        """
        Get grantors for an organization.

        Args:
            organization_id: The organization ID

        Returns:
            Grantors ResourceData object with dot notation access

        Example:
            >>> grantors = client.issuer_authorizations.get_grantors("org123")
        """
        path = f"/v1/organizations/{organization_id}/issuer_authorizations/grantors"
        response = self.http.get(path)
        return self._wrap(response.get("data", response))

    def delete(self, organization_id: str, issuer_authorization_id: str) -> ResourceData:
        """
        Delete (deauthorize) an issuer authorization.

        Args:
            organization_id: The organization ID
            issuer_authorization_id: The issuer authorization ID

        Returns:
            Deletion response as ResourceData object

        Example:
            >>> client.issuer_authorizations.delete("org123", "auth456")
        """
        path = (
            f"/v1/organizations/{organization_id}/issuer_authorizations/{issuer_authorization_id}"
        )
        return self._wrap(self.http.delete(path))
