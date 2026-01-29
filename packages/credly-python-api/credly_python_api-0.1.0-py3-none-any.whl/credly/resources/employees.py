"""Employees resource for Credly API."""

from typing import Any, Dict, Iterator, Optional

from .base import BaseResource


class Employees(BaseResource):
    """Manage employees."""

    def list(
        self,
        organization_id: str,
        page: Optional[int] = None,
        per: Optional[int] = None,
    ) -> Iterator[Dict[str, Any]]:
        """
        List employees for an organization.

        Args:
            organization_id: The organization ID
            page: Specific page number (if None, iterates all pages)
            per: Number of items per page

        Yields:
            Employee data dictionaries

        Example:
            >>> for employee in client.employees.list("org123"):
            ...     print(employee['id'], employee['email'])
        """
        path = f"/v1/organizations/{organization_id}/employees"
        return self._paginate(path, page=page, per=per)

    def get(self, organization_id: str, employee_id: str) -> Dict[str, Any]:
        """
        Get a specific employee.

        Args:
            organization_id: The organization ID
            employee_id: The employee ID

        Returns:
            Employee data dictionary

        Example:
            >>> employee = client.employees.get("org123", "emp456")
            >>> print(employee['email'])
        """
        path = f"/v1/organizations/{organization_id}/employees/{employee_id}"
        response = self.http.get(path)
        return response.get("data", response)

    def get_data(self, organization_id: str, employee_id: str) -> Dict[str, Any]:
        """
        Get employee data.

        Args:
            organization_id: The organization ID
            employee_id: The employee ID

        Returns:
            Employee data dictionary

        Example:
            >>> data = client.employees.get_data("org123", "emp456")
        """
        path = f"/v1/organizations/{organization_id}/employees/{employee_id}/data"
        response = self.http.get(path)
        return response.get("data", response)

    def create(self, organization_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new employee.

        Args:
            organization_id: The organization ID
            **kwargs: Employee data (email, first_name, last_name, etc.)

        Returns:
            Created employee data

        Example:
            >>> employee = client.employees.create(
            ...     "org123",
            ...     email="user@example.com",
            ...     first_name="John",
            ...     last_name="Doe"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/employees"
        response = self.http.post(path, data=kwargs)
        return response.get("data", response)

    def update(self, organization_id: str, employee_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update an employee.

        Args:
            organization_id: The organization ID
            employee_id: The employee ID
            **kwargs: Fields to update

        Returns:
            Updated employee data

        Example:
            >>> employee = client.employees.update(
            ...     "org123",
            ...     "emp456",
            ...     first_name="Jane"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/employees/{employee_id}"
        response = self.http.put(path, data=kwargs)
        return response.get("data", response)

    def delete(self, organization_id: str, employee_id: str) -> Dict[str, Any]:
        """
        Delete an employee.

        Args:
            organization_id: The organization ID
            employee_id: The employee ID

        Returns:
            Deletion response

        Example:
            >>> client.employees.delete("org123", "emp456")
        """
        path = f"/v1/organizations/{organization_id}/employees/{employee_id}"
        return self.http.delete(path)

    def send_invitations(self, organization_id: str, **kwargs) -> Dict[str, Any]:
        """
        Send invitations to employees.

        Args:
            organization_id: The organization ID
            **kwargs: Invitation data (employee_ids, message, etc.)

        Returns:
            Invitation response

        Example:
            >>> response = client.employees.send_invitations(
            ...     "org123",
            ...     employee_ids=["emp1", "emp2"],
            ...     message="Join our platform!"
            ... )
        """
        path = f"/v1/organizations/{organization_id}/employees/invitations"
        response = self.http.post(path, data=kwargs)
        return response.get("data", response)

    def external_badges(self, organization_id: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        List external badges for employees.

        Args:
            organization_id: The organization ID
            **kwargs: Filter parameters

        Yields:
            External badge data dictionaries

        Example:
            >>> for badge in client.employees.external_badges("org123"):
            ...     print(badge['id'])
        """
        path = f"/v1/organizations/{organization_id}/employees/external_badges"
        return self._paginate(path, params=kwargs)

    def skills(self, organization_id: str, **kwargs) -> Iterator[Dict[str, Any]]:
        """
        List skills for employees.

        Args:
            organization_id: The organization ID
            **kwargs: Filter parameters

        Yields:
            Skill data dictionaries

        Example:
            >>> for skill in client.employees.skills("org123"):
            ...     print(skill['name'])
        """
        path = f"/v1/organizations/{organization_id}/employees/skills"
        return self._paginate(path, params=kwargs)
