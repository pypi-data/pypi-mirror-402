# NiceCRUD Component Documentation

NiceCRUD is a CRUD (Create, Read, Update, Delete) component based on NiceTable, inheriting table display and query capabilities while adding create, edit, and delete functionality.

## Features

- Inherits all NiceTable features (query, pagination, detail view, etc.)
- Create new data
- Edit data
- Single and batch delete
- Table mode and card grid mode support
- Auto-generated edit forms

## Installation

```bash
pip install niceguiext
```

## Basic Usage

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition, PageData

# Data storage
products = [
    {"id": 1, "name": "Laptop", "price": 5999.00, "category": "Electronics"},
    {"id": 2, "name": "Mouse", "price": 99.00, "category": "Electronics"},
]

class ProductCRUD(NiceCRUD):
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        filtered_data = products.copy()
        # Implement query filter logic
        for field_name, value in query_values.items():
            if value:
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        # Pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return PageData(data=filtered_data[start_idx:end_idx], total=len(filtered_data))
    
    async def create(self, item: dict):
        # Generate new ID
        max_id = max((p["id"] for p in products), default=0)
        item["id"] = max_id + 1
        products.append(item)
    
    async def update(self, item: dict):
        for i, p in enumerate(products):
            if p["id"] == item["id"]:
                products[i] = item
                break
    
    async def delete(self, item_id: str):
        global products
        products = [p for p in products if str(p["id"]) != str(item_id)]

@ui.page('/')
def main():
    fields = [
        FieldDefinition(name="id", title="ID", type="integer", readonly=True),
        FieldDefinition(name="name", title="Product Name", type="text", required=True, show_in_query=True),
        FieldDefinition(name="price", title="Price", type="number", min_value=0, step=0.01),
        FieldDefinition(name="category", title="Category", type="text", show_in_query=True),
    ]
    
    crud = ProductCRUD(
        fields=fields,
        id_field="id",
        heading="Product Management",
        add_button_text="Add Product",
        delete_button_text="Delete Selected",
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
```

## NiceCRUDConfig Configuration Class

`NiceCRUDConfig` inherits from `NiceTableConfig` and adds CRUD-specific configuration options.

### Additional Configuration Options

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `add_button_text` | str | "Add" | Add button text |
| `delete_button_text` | str | "Delete Selected" | Delete selected button text |
| `new_item_dialog_heading` | str | None | New item dialog heading |
| `update_item_dialog_heading` | str | None | Edit item dialog heading |
| `additional_exclude` | List[str] | [] | Additional fields to exclude |
| `show_detail_action` | bool | False | CRUD mode defaults to not showing detail button |
| `table_type` | str | "table" | Table display type: `"table"` or `"grid"` |
| `class_card_selected` | str | "dark:bg-slate-800 bg-slate-100" | Grid mode selected card style |
| `column_count` | int | None | Form column count (auto-calculated) |

### Inherited Configuration Options

See `NiceTableConfig` configuration in [NiceTable Documentation](./NiceTable_en.md).

## Using Local Data

NiceCRUD has built-in default CRUD implementation based on local data, which can be used directly:

```python
from niceguiext import NiceCRUD, FieldDefinition

# Initial data
data = [
    {"id": 1, "name": "Item 1", "value": 100},
    {"id": 2, "name": "Item 2", "value": 200},
]

fields = [
    FieldDefinition(name="id", title="ID", type="integer", readonly=True),
    FieldDefinition(name="name", title="Name", type="text"),
    FieldDefinition(name="value", title="Value", type="number"),
]

# Use directly without overriding methods
crud = NiceCRUD(
    fields=fields,
    data=data,  # Pass local data
    id_field="id",
    heading="Data Management",
)
```

## Grid Mode

NiceCRUD supports card grid mode for displaying richer content:

```python
crud = NiceCRUD(
    fields=fields,
    id_field="id",
    heading="Product Management",
    table_type="grid",  # Use grid mode
)
```

## Methods to Override

### query Method

Query data, same as NiceTable:

```python
async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
    """
    Query data
    
    Args:
        query_values: Query condition dictionary
        page: Current page number
        page_size: Items per page
    
    Returns:
        PageData: Paginated data
    """
    # Implement query logic
    return PageData(data=[], total=0)
```

### create Method

Create new data:

```python
async def create(self, item: dict):
    """
    Create new item
    
    Args:
        item: New item data dictionary
    """
    # Save to database
    pass
```

### update Method

Update data:

```python
async def update(self, item: dict):
    """
    Update item
    
    Args:
        item: Updated item data dictionary
    """
    # Update database
    pass
```

### delete Method

Delete data:

```python
async def delete(self, item_id: str):
    """
    Delete item
    
    Args:
        item_id: ID of item to delete
    """
    # Delete from database
    pass
```

### detail Method (Optional)

Get detail data:

```python
async def detail(self, item_id: str):
    """
    Get item details
    
    Args:
        item_id: Item ID
    
    Returns:
        Item data dictionary
    """
    # Get details from database
    return {}
```

### select_options Method (Optional)

Dynamically get selection options:

```python
async def select_options(self, field_name: str, item: dict) -> dict:
    """
    Get field selection options
    
    Args:
        field_name: Field name
        item: Current data
    
    Returns:
        Options dictionary {"value": "label"}
    """
    if field_name == "category":
        return {"cat1": "Category 1", "cat2": "Category 2"}
    return {}
```

## Complete Example

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition, PageData, ActionConfig

# Simulated database
users = [
    {"id": 1, "name": "John", "age": 25, "role": "admin", "active": True},
    {"id": 2, "name": "Jane", "age": 30, "role": "user", "active": True},
    {"id": 3, "name": "Bob", "age": 28, "role": "user", "active": False},
]

class UserCRUD(NiceCRUD):
    async def select_options(self, field_name: str, item: dict) -> dict:
        if field_name == "role":
            return {"admin": "Admin", "user": "User", "guest": "Guest"}
        return {}
    
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        filtered = users.copy()
        
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue
            if field_name == "role":
                filtered = [u for u in filtered if u.get("role") == value]
            else:
                filtered = [
                    u for u in filtered
                    if str(u.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        
        return PageData(data=filtered[start:end], total=total)
    
    async def create(self, item: dict):
        max_id = max((u["id"] for u in users), default=0)
        item["id"] = max_id + 1
        users.append(item)
        ui.notify(f"Created: {item['name']}", color="positive")
    
    async def update(self, item: dict):
        for i, u in enumerate(users):
            if u["id"] == item["id"]:
                users[i] = item
                break
        ui.notify(f"Updated: {item['name']}", color="positive")
    
    async def delete(self, item_id: str):
        global users
        users = [u for u in users if str(u["id"]) != str(item_id)]
        ui.notify("Deleted successfully", color="positive")

@ui.page('/')
def main():
    ui.page_title("User Management System")
    
    fields = [
        FieldDefinition(
            name="id",
            title="ID",
            type="integer",
            readonly=True,
            show_in_table=True,
        ),
        FieldDefinition(
            name="name",
            title="Name",
            type="text",
            required=True,
            show_in_table=True,
            show_in_query=True,
        ),
        FieldDefinition(
            name="age",
            title="Age",
            type="integer",
            min_value=0,
            max_value=150,
            show_in_table=True,
        ),
        FieldDefinition(
            name="role",
            title="Role",
            type="tag",
            input_type="select",
            selections={
                "admin": "Admin|blue",
                "user": "User|green",
                "guest": "Guest|gray",
            },
            show_in_table=True,
            show_in_query=True,
        ),
        FieldDefinition(
            name="active",
            title="Active",
            type="boolean",
            default=True,
            show_in_table=True,
        ),
    ]
    
    # Custom action
    def handle_reset_password(row_data):
        ui.notify(f"Reset password for {row_data.get('name')}", color="info")
    
    crud = UserCRUD(
        fields=fields,
        id_field="id",
        heading="User Management",
        add_button_text="Add User",
        delete_button_text="Batch Delete",
        new_item_dialog_heading="Add New User",
        update_item_dialog_heading="Edit User Info",
        page_size=10,
        actions=[
            ActionConfig(
                label="Reset Password",
                call=handle_reset_password,
                color="warning",
                icon="lock_reset",
            ),
        ],
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080)
```

## NiceCRUDCard Component

`NiceCRUDCard` is a card component for edit forms, usually used internally by NiceCRUD but can also be used standalone:

```python
from niceguiext.nicecrud import NiceCRUDCard, NiceCRUDConfig

# Create edit card
card = NiceCRUDCard(
    item={"id": 1, "name": "Test"},
    fields=fields,
    config=NiceCRUDConfig(),
    id_editable=False,  # ID not editable
    on_change_extra=lambda field, data: print(f"Changed: {field}"),
    on_validation_result=lambda valid: print(f"Valid: {valid}"),
)
```

## Field Types in Forms

| Field Type | Input Component |
|------------|-----------------|
| `text` | Text input |
| `integer` | Number input |
| `number` | Number input |
| `boolean` | Checkbox |
| `date` | Date picker |
| `datetime` | DateTime input |
| `select` | Dropdown select |
| `multiselect` | Multi-select dropdown |
| `slider` | Slider |

## Validation

NiceCRUD supports field validation:

```python
FieldDefinition(
    name="email",
    title="Email",
    type="text",
    required=True,
    validation=lambda v: "Please enter a valid email address" if "@" not in str(v) else None,
)
```

You can also use dictionary format to define multiple validation rules:

```python
FieldDefinition(
    name="password",
    title="Password",
    type="text",
    validation={
        "Password must be at least 8 characters": lambda v: len(str(v)) >= 8,
        "Password must contain a number": lambda v: any(c.isdigit() for c in str(v)),
    },
)
```
