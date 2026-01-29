"""Export issued badges to CSV file(s) for a given organization."""

import argparse
import csv
import os
from collections import defaultdict
from typing import Dict, List

from dotenv import load_dotenv

from credly import Client

# Load environment variables
load_dotenv()


def get_organization_id(client: Client, org_id: str = None) -> str:
    """
    Get organization ID from argument or prompt user to select one.

    Args:
        client: Credly API client
        org_id: Optional organization ID

    Returns:
        Organization ID
    """
    if org_id:
        # Verify the organization exists
        try:
            org = client.organizations.get(org_id)
            print(f"Using organization: {org['name']} (ID: {org_id})")
            return org_id
        except Exception as e:
            print(f"Error: Organization {org_id} not found: {e}")
            exit(1)

    # List available organizations
    print("Available organizations:")
    orgs = []
    for org in client.organizations.list():
        orgs.append(org)
        print(f"  {len(orgs)}. {org['name']} (ID: {org['id']})")

    if not orgs:
        print("No organizations found!")
        exit(1)

    # Prompt user to select
    while True:
        try:
            choice = input(f"\nSelect organization (1-{len(orgs)}): ")
            idx = int(choice) - 1
            if 0 <= idx < len(orgs):
                selected_org = orgs[idx]
                print(f"Selected: {selected_org['name']}")
                return selected_org["id"]
            else:
                print(f"Please enter a number between 1 and {len(orgs)}")
        except (ValueError, KeyboardInterrupt):
            print("\nExiting...")
            exit(0)


def get_all_badges(client: Client, org_id: str, template_id: str = None) -> List[Dict]:
    """
    Fetch all badges for an organization, optionally filtered by template.

    Args:
        client: Credly API client
        org_id: Organization ID
        template_id: Optional badge template ID to filter by

    Returns:
        List of badge dictionaries
    """
    print("\nFetching badges...")
    badges = []

    for badge in client.badges.list(org_id):
        # Filter by template if specified
        if template_id and badge.get("badge_template", {}).get("id") != template_id:
            continue
        badges.append(badge)

        # Print progress
        if len(badges) % 100 == 0:
            print(f"  Fetched {len(badges)} badges...")

    print(f"Total badges fetched: {len(badges)}")
    return badges


def get_template_info(client: Client, org_id: str) -> Dict[str, Dict]:
    """
    Fetch all badge templates for reference.

    Args:
        client: Credly API client
        org_id: Organization ID

    Returns:
        Dictionary mapping template IDs to template info
    """
    templates = {}
    for template in client.badge_templates.list(org_id):
        templates[template["id"]] = template
    return templates


def export_to_csv(badges: List[Dict], filename: str, template_name: str = None):
    """
    Export badges to a CSV file.

    Args:
        badges: List of badge dictionaries
        filename: Output filename
        template_name: Optional template name for display
    """
    if not badges:
        print(f"No badges to export{f' for template {template_name}' if template_name else ''}.")
        return

    # Define CSV fields
    fieldnames = [
        "badge_id",
        "recipient_email",
        "recipient_name",
        "template_id",
        "template_name",
        "state",
        "issued_at",
        "accepted_at",
        "expires_at",
        "revoked_at",
        "image_url",
    ]

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for badge in badges:
            # Extract nested data safely
            recipient = badge.get("recipient", {})
            badge_template = badge.get("badge_template", {})

            row = {
                "badge_id": badge.get("id", ""),
                "recipient_email": badge.get("recipient_email", recipient.get("email", "")),
                "recipient_name": (
                    f"{recipient.get('first_name', '')} {recipient.get('last_name', '')}".strip()
                ),
                "template_id": badge_template.get("id", ""),
                "template_name": badge_template.get("name", ""),
                "state": badge.get("state", ""),
                "issued_at": badge.get("issued_at", ""),
                "accepted_at": badge.get("accepted_at", ""),
                "expires_at": badge.get("expires_at", ""),
                "revoked_at": badge.get("revoked_at", ""),
                "image_url": badge.get("image_url", badge_template.get("image_url", "")),
            }
            writer.writerow(row)

    print(f"Exported {len(badges)} badges to {filename}")


def main():
    """Execute the badge export workflow."""
    parser = argparse.ArgumentParser(
        description="Export issued badges for a Credly organization to CSV file(s)."
    )
    parser.add_argument("--org-id", help="Organization ID (if not provided, will prompt to select)")
    parser.add_argument("--template-id", help="Export only badges for a specific template ID")
    parser.add_argument(
        "--separate-files",
        action="store_true",
        help="Create separate CSV files for each badge template",
    )
    parser.add_argument(
        "--output-dir",
        default="badge_exports",
        help="Output directory for CSV files (default: badge_exports)",
    )
    parser.add_argument(
        "--output-file",
        default="issued_badges.csv",
        help="Output filename when using single file mode (default: issued_badges.csv)",
    )

    args = parser.parse_args()

    # Initialize client
    api_key = os.getenv("CREDLY_API_KEY")
    if not api_key:
        print("Error: CREDLY_API_KEY not found in environment variables.")
        print("Please create a .env file with your API key or set the environment variable.")
        exit(1)

    client = Client(api_key=api_key)

    print("Credly Badge Export Tool\n")

    # Get organization ID
    org_id = get_organization_id(client, args.org_id)

    # Fetch all badges
    badges = get_all_badges(client, org_id, args.template_id)

    if not badges:
        print("No badges found!")
        exit(0)

    # Create output directory if needed
    if args.separate_files:
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"\nExporting to directory: {args.output_dir}/")

    # Export based on mode
    if args.separate_files and not args.template_id:
        # Group badges by template
        badges_by_template = defaultdict(list)
        for badge in badges:
            template_id = badge.get("badge_template", {}).get("id", "unknown")
            badges_by_template[template_id].append(badge)

        # Export each template to a separate file
        print(f"\nExporting {len(badges_by_template)} template(s)...")
        for template_id, template_badges in badges_by_template.items():
            template_name = template_badges[0].get("badge_template", {}).get("name", "unknown")
            # Sanitize filename
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in template_name
            )
            filename = os.path.join(args.output_dir, f"{safe_name}_{template_id}.csv")
            export_to_csv(template_badges, filename, template_name)
    else:
        # Export all to a single file
        if args.separate_files:
            # If --separate-files is set with --template-id, use template name in filename
            template_name = badges[0].get("badge_template", {}).get("name", "badges")
            safe_name = "".join(
                c if c.isalnum() or c in (" ", "-", "_") else "_" for c in template_name
            )
            filename = os.path.join(args.output_dir, f"{safe_name}_{args.template_id}.csv")
        else:
            filename = args.output_file

        export_to_csv(badges, filename)

    print("\nExport completed successfully!")


if __name__ == "__main__":
    main()
