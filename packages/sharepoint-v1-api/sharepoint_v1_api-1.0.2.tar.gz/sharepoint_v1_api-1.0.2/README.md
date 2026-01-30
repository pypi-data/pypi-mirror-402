# SharePoint API Python Client – Documentation

A modern Python client for SharePoint REST API operations using a client pattern for better abstraction.

## Features

- Site-scoped operations through `SharePointSite` client
- User management via `SharePointUser`
- List item operations with `SharePointListItem`
- NTLM authentication support
- Comprehensive error handling
- Metadata discovery and batch operations

## Installation

```bash
pip install sharepoint-v1-api
```

From source:

```bash
git clone https://github.com/your-org/nc-devops-sharepoint-v1-api.git
cd nc-devops-sharepoint-v1-api
pip install -e .
```

## Authentication & Initialization

```python
import requests
from requests_ntlm import HttpNtlmAuth
from sharepoint import SharePointSite

# Create authenticated session
session = requests.Session()
session.auth = HttpNtlmAuth('your_user', 'your_password')
session.proxies = {}  # Add proxies if needed

# Initialize site client
site = SharePointSite(
    url="https://your.sharepoint.com/_api/Web",
    session=session
)
```

## Core Operations

### List Operations

```python
# Get all lists
all_lists = site.get_lists()

# Get list by title
tasks_list = site.get_list(list_title="Tasks")

# Filter items with OData syntax
active_tasks = tasks_list.get_items(
    filters="Status eq 'Active'",
    select_fields=["Title", "DueDate"]
)

# Get items with pagination (for large lists)
# First page
first_page = tasks_list.get_items_paged(top=100)
for item in first_page["items"]:
    print(f"Item ID: {item.id}")

# Get next page using the skiptoken
if first_page["has_next"]:
    second_page = tasks_list.get_items_paged(
        top=100,
        skiptoken=first_page["next_skiptoken"]
    )

# Iterate through all items in a large list automatically
for item in tasks_list.iterate_all_items(page_size=1000):
    print(f"Processing item {item.id}")
```


### User Management

```python
# Get user by ID
user = site.get_user(42)
print(f"User: {user.Title} ({user.Email})")
```

### List Items

```python
# Get specific item
task_item = tasks_list.get_item(101)

# Update item
update_data = {
    "Status": "Completed",
    "PercentComplete": 1.0
}
task_item.update_item(update_data)

# Check modification history
print(f"Last modified: {task_item.modified}")
```

## Advanced Usage

### Field Management

```python
# Get list fields
fields = tasks_list.get_fields()
required_fields = [f for f in fields if f.required]

# Update field properties (requires 'Manage Lists' permission)
try:
    description_field = next((f for f in fields if f.title == "TaskDescription"), None)
    if description_field:
        description_field.update_field({
            "Description": "Max length increased to 500 characters",
            "MaxLength": 500
        })
except PermissionError:
    print("Update failed - insufficient permissions")

# Delete obsolete field (irreversible operation)
if description_field and not description_field.required and description_field.hidden:
    success = description_field.delete_field()
    if success:
        print(f"Field '{description_field.title}' deleted")
    else:
        print("Field deletion failed")
else:
    print("Skipping deletion - field is required or visible")
    
# Check field metadata
if description_field:
    print(f"Field '{description_field.title}' type: {description_field.type_as_string}")
    print(f"Hidden: {description_field.hidden}, Read-only: {description_field.read_only}")
```

### Site Metadata

```python
print(f"Site Title: {site.title}")
print(f"Created Date: {site.created.strftime('%Y-%m-%d')}")
print(f"Default Language: {site.language_name}")
```

### Working with Large Lists (Pagination)
SharePoint has list view thresholds that prevent retrieving too many items at once. When working with large lists, use the pagination methods:

```python
# For manual pagination control
page_result = tasks_list.get_items_paged(top=1000)
items = page_result["items"]
has_next = page_result["has_next"]
next_token = page_result["next_skiptoken"]

# For automatic pagination through all items
for item in tasks_list.iterate_all_items(page_size=1000):
    # Process each item
    print(f"Processing item {item.id}")
```

### Batch Operations

```python
# Get multiple lists with filtering
recent_lists = site.get_lists(
    filters="Created gt datetime'2023-01-01T00:00:00Z'",
    select_fields=["Title", "ItemCount"],
    top=10
)
```

### Error Handling

```python
from requests.exceptions import ConnectionError

try:
    site.get_lists()
except ConnectionError as e:
    print(f"Network error: {e}")
except PermissionError:
    print("Authentication failed - check credentials")
except FileNotFoundError:
    print("Requested resource not found")
```

## Class Reference

| Class                | Description                                  | Key Methods/Properties           |
|----------------------|----------------------------------------------|----------------------------------|
| `SharePointSite`     | Main entry point for site operations        | `get_lists`, `get_folder`, `get_user` |
| `SharePointUser`     | User profile management                     | `Email`, `UserName`, `Title`     |
| `SharePointList`     | List operations and metadata                | `get_items`, `get_items_paged`, `iterate_all_items`, `get_item`, `get_fields`|
| `SharePointListItem` | Individual item manipulation                | `update_item`, `delete_item`     |
| `SharePointFolder`   | File/folder operations                      | `get_folders`, `get_folder`      |
| `SharePointListField`| Field metadata and validation               | `update_field`, `delete_field`, `title`, `type_as_string`, `required` |

## Best Practices

1. **Reuse Sessions**: Create one `SharePointSite` instance per site and reuse it
2. **Selective Loading**: Use `select_fields` parameter to optimize payload sizes
3. **Error Recovery**: Implement retry logic for transient network errors
4. **Field Validation**: Check `required` and `read_only` properties before updates
5. **Metadata Caching**: Cache frequently accessed metadata like list GUIDs

## Migration from v0.x

```python
# Old style (deprecated)
from sharepoint_api import SharePointAPI
api = SharePointAPI._compact_init(creds)
items = api.get_lists("cases")

# New client pattern
from sharepoint import SharePointSite
site = SharePointSite(url=site_url, session=session)
items = site.get_lists()
```

## License

MIT License - See [LICENSE](LICENSE) for details.
