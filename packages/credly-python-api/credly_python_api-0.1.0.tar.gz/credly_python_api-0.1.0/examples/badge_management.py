"""Badge management example for the Credly API client."""

import os

from dotenv import load_dotenv

from credly import Client, NotFoundError, ValidationError

# Load environment variables
load_dotenv()

# Initialize the client
api_key = os.getenv("CREDLY_API_KEY")
client = Client(api_key=api_key)

print("Credly API Client - Badge Management Example\n")

# Get organization ID
org_id = None
for org in client.organizations.list():
    org_id = org["id"]
    print(f"Using organization: {org['name']} (ID: {org_id})\n")
    break

if not org_id:
    print("No organization found!")
    exit(1)

# Create a badge template
print("1. Creating a badge template:")
try:
    template = client.badge_templates.create(
        org_id,
        name="Python Expert Badge",
        description="Awarded to developers who demonstrate expert-level Python skills",
        image="https://example.com/python-expert-badge.png",
        skills=["Python", "Software Development", "Problem Solving"],
        activities=[
            {
                "title": "Complete Advanced Python Course",
                "description": "Successfully complete an advanced Python programming course",
            }
        ],
    )
    print(f"   Created template: {template['name']} (ID: {template['id']})")
    template_id = template["id"]
except ValidationError as e:
    print(f"   Validation error: {e.message}")
    print(f"   Response: {e.response}")
    exit(1)
except Exception as e:
    print(f"   Error: {e}")
    # If creation fails, try to use an existing template
    print("   Trying to use existing template instead...")
    for t in client.badge_templates.list(org_id, per=1):
        template_id = t["id"]
        print(f"   Using template: {t['name']} (ID: {template_id})")
        break

# Issue a badge
print("\n2. Issuing a badge:")
try:
    badge = client.badges.issue(
        org_id,
        badge_template_id=template_id,
        recipient_email="developer@example.com",
        issued_at="2024-01-15",
        expires_at="2025-01-15",
        suppress_badge_notification=True,  # Don't send email for this example
    )
    print(f"   Issued badge {badge['id']} to {badge['recipient_email']}")
    badge_id = badge["id"]
except ValidationError as e:
    print(f"   Validation error: {e.message}")
    badge_id = None
except Exception as e:
    print(f"   Error: {e}")
    badge_id = None

# Get badge details
if badge_id:
    print("\n3. Getting badge details:")
    try:
        badge = client.badges.get(org_id, badge_id)
        print(f"   Badge ID: {badge['id']}")
        print(f"   Recipient: {badge['recipient_email']}")
        print(f"   State: {badge.get('state', 'N/A')}")
    except NotFoundError:
        print("   Badge not found")
    except Exception as e:
        print(f"   Error: {e}")

    # Revoke the badge
    print("\n4. Revoking the badge:")
    try:
        badge = client.badges.revoke(
            org_id, badge_id, reason="Example revocation for testing purposes"
        )
        print(f"   Badge {badge_id} has been revoked")
    except Exception as e:
        print(f"   Error: {e}")

# Search for badges
print("\n5. Searching for badges:")
try:
    results = client.badges.bulk_search(org_id, badge_template_id=template_id, state="accepted")
    print(f"   Found {len(results.get('data', []))} accepted badges for this template")
except Exception as e:
    print(f"   Error: {e}")

# List all badges with pagination
print("\n6. Listing all badges (first page, 5 items):")
try:
    for badge in client.badges.list(org_id, page=1, per=5):
        print(f"   - Badge {badge['id']} to {badge.get('recipient_email', 'N/A')}")
except Exception as e:
    print(f"   Error: {e}")

# Update the template
print("\n7. Updating the badge template:")
try:
    updated = client.badge_templates.update(
        org_id,
        template_id,
        description="Updated: Awarded to developers who demonstrate expert-level Python skills",
    )
    print(f"   Updated template {template_id}")
except NotFoundError:
    print("   Template not found")
except Exception as e:
    print(f"   Error: {e}")

# Clean up - delete the template (optional)
# Uncomment the following code if you want to delete the template
# print("\n8. Deleting the badge template:")
# try:
#     client.badge_templates.delete(org_id, template_id)
#     print(f"   Deleted template {template_id}")
# except Exception as e:
#     print(f"   Error: {e}")

print("\nBadge management example completed!")
