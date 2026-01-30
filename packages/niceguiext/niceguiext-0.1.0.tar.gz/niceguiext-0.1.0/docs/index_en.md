# NiceGUIExt Documentation

NiceGUIExt is an extension component library based on [NiceGUI](https://nicegui.io), providing commonly used components such as CRUD interfaces, tables, and forms to help quickly build data management interfaces.

## Features

- **NiceTable** - Feature-rich table component with query, pagination, and detail view
- **NiceCRUD** - CRUD component based on NiceTable, supporting create, read, update, delete
- **NiceForm** - Form component based on field definitions, supporting multiple input types
- **show_error/show_warn** - Error and warning message display components

## Installation

```bash
pip install niceguiext
```

## Quick Start

### Simple CRUD Example

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition

# Define fields
fields = [
    FieldDefinition(name="id", title="ID", type="integer", readonly=True),
    FieldDefinition(name="name", title="Name", type="text", required=True, show_in_query=True),
    FieldDefinition(name="price", title="Price", type="number", min_value=0),
]

# Initial data
data = [
    {"id": 1, "name": "Product A", "price": 100},
    {"id": 2, "name": "Product B", "price": 200},
]

# Create CRUD component
crud = NiceCRUD(
    fields=fields,
    data=data,
    id_field="id",
    heading="Product Management",
)

ui.run()
```

## Component Documentation

- [NiceTable](./NiceTable_en.md) - Table component
- [NiceCRUD](./NiceCRUD_en.md) - CRUD component
- [NiceForm](./NiceForm_en.md) - Form component
- [show_error](./show_error_en.md) - Error/warning display component

## Import Methods

```python
# Recommended import method
from niceguiext import (
    NiceTable,
    NiceTableConfig,
    NiceCRUD,
    NiceCRUDConfig,
    NiceForm,
    FormConfig,
    FieldDefinition,
    PageData,
    ActionConfig,
    show_error,
    show_warn,
)

# Or import from submodules
from niceguiext.nicetable import NiceTable, FieldDefinition, PageData
from niceguiext.nicecrud import NiceCRUD, NiceCRUDCard
from niceguiext.form import NiceForm, FormConfig
from niceguiext.show_error import show_error, show_warn
```

## Core Concepts

### FieldDefinition

`FieldDefinition` is the core class for defining fields, describing the type, validation rules, and display methods of data fields.

```python
from niceguiext import FieldDefinition

field = FieldDefinition(
    name="email",           # Field name
    title="Email",          # Display title
    type="text",            # Field type
    required=True,          # Whether required
    show_in_table=True,     # Show in table
    show_in_query=True,     # Use as query condition
    show_in_detail=True,    # Show in detail view
)
```

### PageData

`PageData` is used to encapsulate paginated query results:

```python
from niceguiext import PageData

# Query method returns PageData
async def query(self, query_values: dict, page: int, page_size: int) -> PageData:
    data = [...]  # Current page data
    total = 100   # Total count
    return PageData(data=data, total=total)
```

### ActionConfig

`ActionConfig` is used to configure custom action buttons for table rows:

```python
from niceguiext import ActionConfig

action = ActionConfig(
    label="Edit",
    call=handle_edit,  # Can be a function or method name string
    color="primary",
    icon="edit",
    tooltip="Edit this item",
)
```

## Field Types

| Type | Description | Applicable Components |
|------|-------------|----------------------|
| `text` | Text | NiceTable, NiceCRUD |
| `integer` | Integer | NiceTable, NiceCRUD |
| `number` | Float | NiceTable, NiceCRUD |
| `boolean` | Boolean | NiceTable, NiceCRUD |
| `date` | Date | NiceTable, NiceCRUD |
| `datetime` | DateTime | NiceTable, NiceCRUD |
| `json` | JSON data | NiceTable, NiceCRUD |
| `html` | HTML content | NiceTable, NiceCRUD |
| `tag` | Colored tag | NiceTable, NiceCRUD |

## Example Projects

Check the [examples](../examples) directory for more examples:

| Example | Description |
|---------|-------------|
| `nicecrud_simple.py` | NiceCRUD simple example |
| `nicecrud_example.py` | NiceCRUD complete example |
| `nicecrud_advanced.py` | NiceCRUD advanced usage |
| `nicecrud_grid.py` | NiceCRUD grid mode |
| `nicetable_example.py` | NiceTable example |
| `form_field_definition_example.py` | NiceForm example |
| `validation_example.py` | Validation example |

## License

MIT License
