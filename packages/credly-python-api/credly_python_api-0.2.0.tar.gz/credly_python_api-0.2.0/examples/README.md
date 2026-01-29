# Credly API Examples

This directory contains example scripts demonstrating how to use the Credly Python API client.

## Setup

Before running any examples, you need to:

1. **Install the package and dependencies**:
   ```bash
   pip install -e .
   # or
   pip install -r requirements.txt
   ```

2. **Set up your API key**:

   Create a `.env` file in the project root directory:
   ```bash
   CREDLY_API_KEY=your_api_key_here
   ```

   Or set it as an environment variable:
   ```bash
   export CREDLY_API_KEY=your_api_key_here
   ```

3. **Get your API key** from your Credly account settings.

## Available Examples

### 1. Basic Usage (`basic_usage.py`)

A comprehensive introduction to the Credly API client covering the most common operations.

**What it does**:
- Lists and retrieves organizations
- Lists badge templates
- Lists issued badges
- Lists employees
- Demonstrates error handling

**How to run**:
```bash
python examples/basic_usage.py
```

**Output**: Displays information about your organizations, templates, badges, and employees.

---

### 2. Badge Management (`badge_management.py`)

Demonstrates the complete lifecycle of badge templates and issued badges.

**What it does**:
- Creates a new badge template
- Issues a badge to a recipient
- Retrieves badge details
- Revokes a badge
- Searches for badges
- Updates badge templates
- Shows pagination

**How to run**:
```bash
python examples/badge_management.py
```

**Note**: This script will create and revoke test badges. The badge notification is suppressed to avoid sending actual emails.

---

### 3. Export Issued Badges (`export_list_of_issued_badges.py`)

Export issued badges for an organization to CSV file(s) for reporting and analysis.

**What it does**:
- Exports all issued badges for an organization to CSV
- Supports filtering by specific badge template
- Can create separate CSV files for each badge template
- Prompts for organization selection if not specified

**How to run**:

**Basic usage** (will prompt to select organization):
```bash
python examples/export_list_of_issued_badges.py
```

**Export for a specific organization**:
```bash
python examples/export_list_of_issued_badges.py --org-id org_abc123
```

**Export only badges for a specific template**:
```bash
python examples/export_list_of_issued_badges.py --org-id org_abc123 --template-id template_xyz789
```

**Create separate CSV files for each badge template**:
```bash
python examples/export_list_of_issued_badges.py --org-id org_abc123 --separate-files
```

**Custom output location**:
```bash
python examples/export_list_of_issued_badges.py --output-file my_badges.csv
```

**All options combined**:
```bash
python examples/export_list_of_issued_badges.py \
  --org-id org_abc123 \
  --separate-files \
  --output-dir exports/2024
```

**Command-line options**:
- `--org-id ORG_ID` - Organization ID (if not provided, will prompt to select)
- `--template-id TEMPLATE_ID` - Export only badges for a specific template
- `--separate-files` - Create separate CSV files for each badge template
- `--output-dir DIR` - Output directory for CSV files (default: `badge_exports`)
- `--output-file FILE` - Output filename for single file mode (default: `issued_badges.csv`)

**CSV Output includes**:
- Badge ID
- Recipient email and name
- Template ID and name
- Badge state (issued, accepted, revoked, etc.)
- Issued, accepted, expires, and revoked dates
- Image URL

---

## Common Patterns

### Error Handling

All examples demonstrate proper error handling using the client's exception classes:

```python
from credly import Client, NotFoundError, ValidationError

try:
    badge = client.badges.get(org_id, badge_id)
except NotFoundError as e:
    print(f"Badge not found: {e.message}")
except ValidationError as e:
    print(f"Validation error: {e.message}")
```

### Pagination

The client handles pagination automatically:

```python
# Iterate through all items
for badge in client.badges.list(org_id):
    print(badge['id'])

# Get a specific page with custom page size
for badge in client.badges.list(org_id, page=2, per=50):
    print(badge['id'])
```

### Resource Access

Access different resources through the client:

```python
client = Client(api_key=api_key)

# Organizations
client.organizations.list()
client.organizations.get(org_id)

# Badge Templates
client.badge_templates.list(org_id)
client.badge_templates.get(org_id, template_id)
client.badge_templates.create(org_id, name="...", description="...", image="...")

# Badges
client.badges.list(org_id)
client.badges.get(org_id, badge_id)
client.badges.issue(org_id, badge_template_id="...", recipient_email="...")
client.badges.revoke(org_id, badge_id, reason="...")

# Employees
client.employees.list(org_id)
```

## Troubleshooting

### API Key Issues

If you get authentication errors:
- Verify your `.env` file exists and contains the correct API key
- Check that the `.env` file is in the project root directory
- Ensure the API key format is: `CREDLY_API_KEY=your_key_here` (no quotes)

### Rate Limiting

The Credly API has rate limits. If you encounter rate limiting:
- Add delays between requests for large batch operations
- Use pagination with appropriate page sizes
- Consider the `bulk_search` endpoint for high-volume queries

### Module Import Errors

If you get import errors:
```bash
# Install in development mode
pip install -e .

# Or install from the current directory
pip install .
```

## Additional Resources

- [Main README](../README.md) - Full library documentation
- [Credly API Documentation](https://www.credly.com/docs/api) - Official API reference
- [API Authentication](https://www.credly.com/docs/api#authentication) - How to get your API key

## Contributing

Have an example you'd like to add? Please submit a pull request with:
- A descriptive filename
- Clear comments explaining what the example demonstrates
- Error handling where appropriate
- An entry in this README explaining the example
