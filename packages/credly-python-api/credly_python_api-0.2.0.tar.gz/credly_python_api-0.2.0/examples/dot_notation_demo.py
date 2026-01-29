"""
Demonstration of dot notation access for resource properties.

This example shows how you can now access resource properties using
both dot notation (e.g., badge.id) and traditional bracket notation
(e.g., badge['id']) for backward compatibility.
"""

from credly import Client

# Initialize the client
client = Client(api_key="your_api_key_here")

# Example 1: Using dot notation with organizations
print("Example 1: Dot notation with organizations")
print("-" * 50)
for org in client.organizations.list():
    # New dot notation - cleaner and more Pythonic
    print(f"Organization: {org.name} (ID: {org.id})")

    # Old bracket notation still works for backward compatibility
    print(f"  Legacy access: {org['name']}")
    print()

# Example 2: Using dot notation with badges
print("\nExample 2: Dot notation with badges")
print("-" * 50)
org_id = "your_org_id"
for badge in client.badges.list(org_id):
    # Access nested properties with dot notation
    print(f"Badge ID: {badge.id}")
    print(f"Recipient: {badge.recipient_email}")
    print(f"State: {badge.state}")

    # Mix dot and bracket notation as needed
    if badge.state == "accepted":
        print(f"  Accepted on: {badge.get('accepted_at', 'N/A')}")
    print()

# Example 3: Getting a specific resource
print("\nExample 3: Getting a specific resource")
print("-" * 50)
badge = client.badges.get(org_id, "badge_id")

# All of these work:
print(f"Dot notation: {badge.recipient_email}")
print(f"Bracket notation: {badge['recipient_email']}")
print(f"Get method: {badge.get('recipient_email')}")
print(f"With default: {badge.get('nonexistent', 'default')}")

# Example 4: Converting back to dict
print("\nExample 4: Converting to dictionary")
print("-" * 50)
badge_dict = badge.to_dict()
print(f"Type: {type(badge_dict)}")
print(f"Keys: {list(badge_dict.keys())}")

# Example 5: Using 'in' operator
print("\nExample 5: Checking for keys")
print("-" * 50)
print(f"'id' in badge: {'id' in badge}")
print(f"'nonexistent' in badge: {'nonexistent' in badge}")

# Example 6: Working with bulk search results
print("\nExample 6: Bulk search with list results")
print("-" * 50)
results = client.badges.bulk_search(org_id, state="accepted")
print(f"Number of results: {len(results)}")

# Access individual results with indexing
if len(results) > 0:
    first_result = results[0]
    print(f"First result ID: {first_result.id}")

# Iterate over results
for result in results:
    print(f"  - {result.id}: {result.recipient_email}")
