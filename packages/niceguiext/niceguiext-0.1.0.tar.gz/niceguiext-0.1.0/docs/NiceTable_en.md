# NiceTable Component Documentation

NiceTable is a feature-rich table component that supports query configuration, expandable action buttons, detail view, pagination, and multiple field types for querying.

## Features

- Query configuration support (text, select, date range, etc.)
- Expandable action buttons
- Detail view functionality
- Pagination support
- Multiple field types (text, integer, number, date, datetime, json, html, tag, etc.)
- Row expansion for detailed information

## Installation

```bash
pip install niceguiext
```

## Basic Usage

```python
from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, PageData

# Define fields
fields = [
    FieldDefinition(
        name="id",
        title="ID",
        type="integer",
        show_in_table=True,
        show_in_detail=True,
    ),
    FieldDefinition(
        name="name",
        title="Name",
        type="text",
        show_in_table=True,
        show_in_query=True,
        show_in_detail=True,
    ),
    FieldDefinition(
        name="status",
        title="Status",
        type="tag",
        input_type="select",
        selections={"active": "Active|green", "inactive": "Inactive|red"},
        show_in_table=True,
        show_in_query=True,
    ),
]

# Create custom table class
class MyTable(NiceTable):
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        # Implement data query logic
        data = [...]  # Get data from database or other sources
        return PageData(data=data, total=len(data))

# Create table
table = MyTable(
    fields=fields,
    id_field="id",
    heading="Data List",
    page_size=10,
)

ui.run()
```

## FieldDefinition Field Definition

`FieldDefinition` is the configuration class for defining table fields.

### Basic Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | str | Required | Field name |
| `title` | str | Required | Field display title |
| `type` | str | "text" | Field type |
| `description` | str | None | Field description (shown as tooltip) |
| `default` | Any | None | Default value |
| `required` | bool | True | Whether required |

### Numeric Type Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `min_value` | float | None | Minimum value |
| `max_value` | float | None | Maximum value |
| `step` | float | None | Step value |

### Selection Type Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `input_type` | str | None | Input type: `"select"`, `"multiselect"`, `"slider"`, `"number"` |
| `selections` | dict | None | Selection options, format: `{"value": "label"}` |
| `show_selection_label` | bool | None | Whether to show selection label |

### Display Control Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `readonly` | bool | False | Whether readonly |
| `exclude` | bool | False | Whether to exclude from display |
| `show_in_table` | bool | False | Whether to show in table |
| `show_in_query` | bool | False | Whether to use as query condition |
| `show_in_expand` | bool | False | Whether to show in expanded row |
| `show_in_detail` | bool | False | Whether to show in detail dialog |

### Other Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `max_length` | int | None | Maximum length (text type) |
| `datetime_format` | str | "%Y-%m-%d %H:%M:%S" | Datetime format string |
| `validation` | Callable/dict | None | Validation rules |
| `validation_error` | str | None | Validation error message |

### Supported Field Types

| Type | Description |
|------|-------------|
| `text` | Text type |
| `integer` | Integer type |
| `number` | Number type (float) |
| `boolean` | Boolean type |
| `date` | Date type |
| `datetime` | DateTime type |
| `json` | JSON type (formatted display) |
| `html` | HTML type (direct rendering) |
| `tag` | Tag type (colored label) |

## NiceTableConfig Configuration Class

`NiceTableConfig` is used to configure table behavior and appearance.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `id_field` | str | "" | ID field name |
| `id_label` | str | None | ID field label |
| `no_data_label` | str | "No data" | Text shown when no data |
| `heading` | str | "List" | Table heading |
| `query_button_text` | str | "Query" | Query button text |
| `reset_button_text` | str | "Reset" | Reset button text |
| `detail_button_text` | str | "Details" | Detail button text |
| `detail_dialog_heading` | str | None | Detail dialog heading |
| `show_detail_action` | bool | True | Whether to show detail button |
| `page_size` | int | 20 | Items per page |
| `actions` | List[ActionConfig] | [] | Table row action buttons |
| `class_heading` | str | "text-xl font-bold" | Heading style class |
| `class_card` | str | "dark:bg-slate-900 bg-slate-200" | Card style class |
| `class_card_header` | str | "dark:bg-slate-700 bg-slate-50" | Card header style class |

## ActionConfig Action Button Configuration

`ActionConfig` is used to configure custom action buttons for table rows.

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `label` | str | Required | Button display text |
| `call` | str/Callable | Required | Function name or function object to call |
| `color` | str | "primary" | Button color |
| `icon` | str | None | Button icon |
| `tooltip` | str | None | Button tooltip |

## PageData Pagination Data Class

`PageData` is used to encapsulate paginated query results.

| Property | Type | Description |
|----------|------|-------------|
| `data` | List[Dict] | Current page data |
| `total` | int | Total data count |

## Complete Example

```python
from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, ActionConfig, PageData

# Test data
TEST_DATA = [
    {"id": i, "name": f"User {i}", "email": f"user{i}@example.com", "status": "active"}
    for i in range(1, 51)
]

class UserTable(NiceTable):
    async def select_options(self, field_name: str, item) -> dict:
        """Get selection options"""
        if field_name == "status":
            return {"active": "Active", "inactive": "Inactive", "pending": "Pending"}
        return {}
    
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        """Implement query and pagination"""
        filtered_data = TEST_DATA.copy()
        
        # Apply query conditions
        for field_name, value in query_values.items():
            if value is None or value == "":
                continue
            if field_name == "status":
                filtered_data = [item for item in filtered_data if item.get(field_name) == value]
            else:
                filtered_data = [
                    item for item in filtered_data
                    if str(item.get(field_name, "")).lower().find(str(value).lower()) >= 0
                ]
        
        # Pagination
        total_count = len(filtered_data)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_data = filtered_data[start_idx:end_idx]
        
        return PageData(data=page_data, total=total_count)

@ui.page('/')
async def main():
    # Define fields
    fields = [
        FieldDefinition(
            name="id",
            title="ID",
            type="integer",
            show_in_table=True,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="name",
            title="Name",
            type="text",
            show_in_table=True,
            show_in_query=True,
            show_in_expand=True,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="email",
            title="Email",
            type="html",
            show_in_table=True,
            show_in_detail=True,
        ),
        FieldDefinition(
            name="status",
            title="Status",
            type="tag",
            input_type="select",
            selections={"active": "Active|green", "inactive": "Inactive|red", "pending": "Pending|orange"},
            show_in_table=True,
            show_in_query=True,
            show_in_detail=True,
        ),
    ]

    # Custom action handlers
    def handle_edit(row_data):
        ui.notify(f"Edit: {row_data.get('name')}", color="info")

    def handle_delete(row_data):
        ui.notify(f"Delete: {row_data.get('name')}", color="negative")

    # Create table
    table = UserTable(
        fields=fields,
        id_field="id",
        heading="User List",
        page_size=10,
        actions=[
            ActionConfig(label="Edit", call=handle_edit, color="info", icon="edit"),
            ActionConfig(label="Delete", call=handle_delete, color="negative", icon="delete"),
        ],
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run()
```

## Tag Type Usage

Tag type is used to display colored status labels. Use `"value": "label|color"` format in `selections`:

```python
FieldDefinition(
    name="status",
    title="Status",
    type="tag",
    input_type="select",
    selections={
        "active": "Active|green",
        "inactive": "Inactive|red",
        "pending": "Pending|orange",
        "approved": "Approved|blue",
    },
    show_in_table=True,
)
```

Supported colors: `red`, `green`, `blue`, `orange`, `yellow`, `purple`, `pink`, `cyan`, `gray`

## Methods to Override

### query Method

Subclasses must override the `query` method to implement data query logic:

```python
async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
    """
    Query data
    
    Args:
        query_values: Query condition dictionary
        page: Current page number (starting from 1)
        page_size: Items per page
    
    Returns:
        PageData: Contains current page data and total count
    """
    # Implement query logic
    return PageData(data=[], total=0)
```

### select_options Method (Optional)

If there are selection type fields, override this method to dynamically get options:

```python
async def select_options(self, field_name: str, item: Dict[str, Any]) -> Dict[str, str]:
    """
    Get field selection options
    
    Args:
        field_name: Field name
        item: Current row data
    
    Returns:
        Options dictionary {"value": "label"}
    """
    if field_name == "category":
        return {"cat1": "Category 1", "cat2": "Category 2"}
    return {}
```

### detail Method (Optional)

If you need to customize the detail data retrieval logic, override this method:

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
    return {"id": item_id, "name": "..."}
```
