"""Authorization Tokens resource for Credly API."""

from typing import Iterator, Optional

from .base import BaseResource, ResourceData


class AuthorizationTokens(BaseResource):
    """Manage authorization tokens."""

    def list(
        self,
        organization_id: str,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[ResourceData]:
        """
        List authorization tokens for an organization.

        Args:
            organization_id: The organization ID
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Token ResourceData objects with dot notation access

        Example:
            >>> for token in client.authorization_tokens.list("org123"):
            ...     print(token.id, token.name)
        """
        path = f"/v1/organizations/{organization_id}/authorization_tokens"
        return self._paginate(path, page=page, per=per)

    def create(self, organization_id: str, **kwargs) -> ResourceData:
        """
        Create a new authorization token.

        Args:
            organization_id: The organization ID
            **kwargs: Token data (name, scopes, etc.)

        Returns:
            Created token ResourceData object with dot notation access

        Example:
            >>> token = client.authorization_tokens.create(
            ...     "org123",
            ...     name="API Token",
            ...     scopes=["read", "write"]
            ... )
        """
        path = f"/v1/organizations/{organization_id}/authorization_tokens"
        response = self.http.post(path, data=kwargs)
        return self._wrap(response.get("data", response))

    def rotate(self, organization_id: str, **kwargs) -> ResourceData:
        """
        Rotate authorization tokens.

        Args:
            organization_id: The organization ID
            **kwargs: Rotation parameters

        Returns:
            Rotation response as ResourceData object

        Example:
            >>> response = client.authorization_tokens.rotate(
            ...     "org123",
            ...     token_id="token456"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/authorization_tokens/rotate"
        response = self.http.post(path, data=kwargs)
        return self._wrap(response.get("data", response))
