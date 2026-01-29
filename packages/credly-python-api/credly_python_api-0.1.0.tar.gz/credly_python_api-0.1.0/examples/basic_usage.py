"""Basic usage example for the Credly API client."""

import os

from dotenv import load_dotenv

from credly import Client, NotFoundError, ValidationError

# Load environment variables
load_dotenv()

# Initialize the client
api_key = os.getenv("CREDLY_API_KEY")
client = Client(api_key=api_key)

print("Credly API Client - Basic Usage Example\n")

# List organizations
print("1. Listing organizations:")
try:
    for org in client.organizations.list():
        print(f"   - {org['name']} (ID: {org['id']})")
        # Use the first organization for subsequent examples
        org_id = org["id"]
        break
except Exception as e:
    print(f"   Error: {e}")
    exit(1)

print(f"\nUsing organization ID: {org_id}\n")

# Get a specific organization
print("2. Getting organization details:")
try:
    org = client.organizations.get(org_id)
    print(f"   Name: {org['name']}")
    print(f"   ID: {org['id']}")
except NotFoundError:
    print("   Organization not found")
except Exception as e:
    print(f"   Error: {e}")

# List badge templates
print("\n3. Listing badge templates:")
try:
    count = 0
    for template in client.badge_templates.list(org_id, per=5):
        print(f"   - {template['name']} (ID: {template['id']})")
        count += 1
        if count >= 5:
            break
    if count == 0:
        print("   No badge templates found")
except Exception as e:
    print(f"   Error: {e}")

# List issued badges
print("\n4. Listing issued badges:")
try:
    count = 0
    for badge in client.badges.list(org_id, per=5):
        print(f"   - Badge {badge['id']} to {badge.get('recipient_email', 'N/A')}")
        count += 1
        if count >= 5:
            break
    if count == 0:
        print("   No issued badges found")
except Exception as e:
    print(f"   Error: {e}")

# List employees
print("\n5. Listing employees:")
try:
    count = 0
    for employee in client.employees.list(org_id, per=5):
        print(f"   - {employee.get('email', 'N/A')} (ID: {employee['id']})")
        count += 1
        if count >= 5:
            break
    if count == 0:
        print("   No employees found")
except Exception as e:
    print(f"   Error: {e}")

# Example of error handling
print("\n6. Error handling example:")
try:
    # Try to get a non-existent badge template
    template = client.badge_templates.get(org_id, "non-existent-id")
except NotFoundError as e:
    print(f"   Caught NotFoundError: {e.message}")
except ValidationError as e:
    print(f"   Caught ValidationError: {e.message}")
except Exception as e:
    print(f"   Caught unexpected error: {e}")

print("\nExample completed!")
