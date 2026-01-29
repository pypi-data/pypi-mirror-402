"""Tests for API resources."""

import responses


class TestOrganizations:
    """Test Organizations resource."""

    @responses.activate
    def test_list_organizations(self, client):
        """Test listing organizations with pagination."""
        responses.add(
            responses.GET,
            "https://api.credly.com/v1/organizations",
            json={
                "data": [
                    {"id": "org1", "name": "Org 1"},
                    {"id": "org2", "name": "Org 2"},
                ],
                "metadata": {"total_pages": 1, "current_page": 1},
            },
            status=200,
        )

        orgs = list(client.organizations.list())
        assert len(orgs) == 2
        assert orgs[0]["id"] == "org1"
        assert orgs[1]["id"] == "org2"

    @responses.activate
    def test_get_organization(self, client, org_id):
        """Test getting a specific organization."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}",
            json={"data": {"id": org_id, "name": "Test Org"}},
            status=200,
        )

        org = client.organizations.get(org_id)
        assert org["id"] == org_id
        assert org["name"] == "Test Org"

    @responses.activate
    def test_update_organization(self, client, org_id):
        """Test updating an organization."""
        responses.add(
            responses.PUT,
            f"https://api.credly.com/v1/organizations/{org_id}",
            json={"data": {"id": org_id, "name": "Updated Org"}},
            status=200,
        )

        org = client.organizations.update(org_id, name="Updated Org")
        assert org["name"] == "Updated Org"


class TestBadgeTemplates:
    """Test BadgeTemplates resource."""

    @responses.activate
    def test_list_badge_templates(self, client, org_id):
        """Test listing badge templates."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={
                "data": [
                    {"id": "tpl1", "name": "Template 1"},
                    {"id": "tpl2", "name": "Template 2"},
                ],
                "metadata": {"total_pages": 1},
            },
            status=200,
        )

        templates = list(client.badge_templates.list(org_id))
        assert len(templates) == 2

    @responses.activate
    def test_list_badge_templates_with_filters(self, client, org_id):
        """Test listing badge templates with filters."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={"data": [], "metadata": {"total_pages": 1}},
            status=200,
        )

        list(client.badge_templates.list(org_id, filter="active", sort="name"))

        # Check query params were sent
        assert len(responses.calls) == 1
        assert "filter=active" in responses.calls[0].request.url
        assert "sort=name" in responses.calls[0].request.url

    @responses.activate
    def test_get_badge_template(self, client, org_id, badge_template_id):
        """Test getting a specific badge template."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates/{badge_template_id}",
            json={"data": {"id": badge_template_id, "name": "Python Expert"}},
            status=200,
        )

        template = client.badge_templates.get(org_id, badge_template_id)
        assert template["id"] == badge_template_id

    @responses.activate
    def test_create_badge_template(self, client, org_id):
        """Test creating a badge template."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={"data": {"id": "new_tpl", "name": "New Template"}},
            status=201,
        )

        template = client.badge_templates.create(
            org_id,
            name="New Template",
            description="Test description",
            image="https://example.com/badge.png",
        )
        assert template["name"] == "New Template"

    @responses.activate
    def test_update_badge_template(self, client, org_id, badge_template_id):
        """Test updating a badge template."""
        responses.add(
            responses.PUT,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates/{badge_template_id}",
            json={"data": {"id": badge_template_id, "name": "Updated"}},
            status=200,
        )

        template = client.badge_templates.update(org_id, badge_template_id, name="Updated")
        assert template["name"] == "Updated"

    @responses.activate
    def test_delete_badge_template(self, client, org_id, badge_template_id):
        """Test deleting a badge template."""
        responses.add(
            responses.DELETE,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates/{badge_template_id}",
            status=204,
        )

        result = client.badge_templates.delete(org_id, badge_template_id)
        assert result == {}


class TestBadges:
    """Test Badges resource."""

    @responses.activate
    def test_list_badges(self, client, org_id):
        """Test listing badges."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badges",
            json={
                "data": [{"id": "badge1", "recipient_email": "user@example.com"}],
                "metadata": {"total_pages": 1},
            },
            status=200,
        )

        badges = list(client.badges.list(org_id))
        assert len(badges) == 1

    @responses.activate
    def test_get_badge(self, client, org_id, badge_id):
        """Test getting a specific badge."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badges/{badge_id}",
            json={"data": {"id": badge_id, "state": "accepted"}},
            status=200,
        )

        badge = client.badges.get(org_id, badge_id)
        assert badge["id"] == badge_id

    @responses.activate
    def test_issue_badge(self, client, org_id):
        """Test issuing a badge."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/badges",
            json={"data": {"id": "new_badge", "recipient_email": "user@example.com"}},
            status=201,
        )

        badge = client.badges.issue(
            org_id,
            badge_template_id="template123",
            recipient_email="user@example.com",
        )
        assert badge["recipient_email"] == "user@example.com"

    @responses.activate
    def test_revoke_badge(self, client, org_id, badge_id):
        """Test revoking a badge."""
        responses.add(
            responses.PUT,
            f"https://api.credly.com/v1/organizations/{org_id}/badges/{badge_id}/revoke",
            json={"data": {"id": badge_id, "state": "revoked"}},
            status=200,
        )

        badge = client.badges.revoke(org_id, badge_id, reason="Test revocation")
        assert badge["state"] == "revoked"

    @responses.activate
    def test_replace_badge(self, client, org_id, badge_id):
        """Test replacing a badge."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/badges/{badge_id}/replace",
            json={"data": {"id": "new_badge_id"}},
            status=200,
        )

        badge = client.badges.replace(org_id, badge_id, badge_template_id="new_template")
        assert "id" in badge

    @responses.activate
    def test_bulk_search_badges(self, client, org_id):
        """Test bulk search for badges."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/badges/bulk_search",
            json={"data": [{"id": "badge1"}, {"id": "badge2"}]},
            status=200,
        )

        results = client.badges.bulk_search(org_id, state="accepted")
        # bulk_search returns the data directly (not wrapped in "data" key)
        assert len(results) == 2
        assert results[0]["id"] == "badge1"

    @responses.activate
    def test_delete_badge(self, client, org_id, badge_id):
        """Test deleting a badge."""
        responses.add(
            responses.DELETE,
            f"https://api.credly.com/v1/organizations/{org_id}/badges/{badge_id}",
            status=204,
        )

        result = client.badges.delete(org_id, badge_id)
        assert result == {}


class TestEmployees:
    """Test Employees resource."""

    @responses.activate
    def test_list_employees(self, client, org_id):
        """Test listing employees."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/employees",
            json={
                "data": [{"id": "emp1", "email": "employee@example.com"}],
                "metadata": {"total_pages": 1},
            },
            status=200,
        )

        employees = list(client.employees.list(org_id))
        assert len(employees) == 1

    @responses.activate
    def test_get_employee(self, client, org_id, employee_id):
        """Test getting a specific employee."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/employees/{employee_id}",
            json={"data": {"id": employee_id, "email": "test@example.com"}},
            status=200,
        )

        employee = client.employees.get(org_id, employee_id)
        assert employee["id"] == employee_id

    @responses.activate
    def test_create_employee(self, client, org_id):
        """Test creating an employee."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/employees",
            json={"data": {"id": "new_emp", "email": "new@example.com"}},
            status=201,
        )

        employee = client.employees.create(
            org_id,
            email="new@example.com",
            first_name="John",
            last_name="Doe",
        )
        assert employee["email"] == "new@example.com"

    @responses.activate
    def test_update_employee(self, client, org_id, employee_id):
        """Test updating an employee."""
        responses.add(
            responses.PUT,
            f"https://api.credly.com/v1/organizations/{org_id}/employees/{employee_id}",
            json={"data": {"id": employee_id, "first_name": "Jane"}},
            status=200,
        )

        employee = client.employees.update(org_id, employee_id, first_name="Jane")
        assert employee["first_name"] == "Jane"

    @responses.activate
    def test_delete_employee(self, client, org_id, employee_id):
        """Test deleting an employee."""
        responses.add(
            responses.DELETE,
            f"https://api.credly.com/v1/organizations/{org_id}/employees/{employee_id}",
            status=204,
        )

        result = client.employees.delete(org_id, employee_id)
        assert result == {}

    @responses.activate
    def test_send_invitations(self, client, org_id):
        """Test sending employee invitations."""
        responses.add(
            responses.POST,
            f"https://api.credly.com/v1/organizations/{org_id}/employees/invitations",
            json={"data": {"sent": 2}},
            status=200,
        )

        result = client.employees.send_invitations(org_id, employee_ids=["emp1", "emp2"])
        assert result["sent"] == 2


class TestPagination:
    """Test pagination behavior."""

    @responses.activate
    def test_automatic_pagination(self, client, org_id):
        """Test automatic pagination through multiple pages."""
        # Page 1
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={
                "data": [{"id": "tpl1"}, {"id": "tpl2"}],
                "metadata": {"total_pages": 2, "current_page": 1},
            },
            status=200,
        )
        # Page 2
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={
                "data": [{"id": "tpl3"}],
                "metadata": {"total_pages": 2, "current_page": 2},
            },
            status=200,
        )

        templates = list(client.badge_templates.list(org_id))

        # Should have fetched all 3 items across 2 pages
        assert len(templates) == 3
        assert len(responses.calls) == 2

    @responses.activate
    def test_manual_pagination(self, client, org_id):
        """Test manual pagination with specific page."""
        responses.add(
            responses.GET,
            f"https://api.credly.com/v1/organizations/{org_id}/badge_templates",
            json={
                "data": [{"id": "tpl1"}],
                "metadata": {"total_pages": 2, "current_page": 1},
            },
            status=200,
        )

        templates = list(client.badge_templates.list(org_id, page=1, per=10))

        # Should only fetch one page
        assert len(templates) == 1
        assert len(responses.calls) == 1
        assert "page=1" in responses.calls[0].request.url
        assert "per=10" in responses.calls[0].request.url
