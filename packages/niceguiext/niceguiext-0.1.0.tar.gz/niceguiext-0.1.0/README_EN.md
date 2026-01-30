# NiceGUIExt

English | [简体中文](./README.md)

NiceGUIExt is an extension component library based on [NiceGUI](https://nicegui.io), providing commonly used components such as tables, CRUD interfaces, and forms to help quickly build data management interfaces.

## Features

- **NiceTable** - Feature-rich table component with query, pagination, detail view, and custom action buttons
- **NiceCRUD** - CRUD component based on NiceTable, supporting create, read, update, delete operations with table and card display modes
- **NiceForm** - Form component based on field definitions, supporting multiple input types and validation
- **show_error/show_warn** - Error and warning message display components

## Installation

```bash
pip install niceguiext
```

## Quick Start

### NiceCRUD Example

```python
from nicegui import ui
from niceguiext import NiceCRUD, FieldDefinition

# Define fields
fields = [
    FieldDefinition(name="id", title="ID", type="integer", readonly=True, show_in_table=True),
    FieldDefinition(name="name", title="Name", type="text", required=True, show_in_table=True, show_in_query=True),
    FieldDefinition(name="price", title="Price", type="number", min_value=0, show_in_table=True),
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

### NiceTable Example

```python
from nicegui import ui
from niceguiext import NiceTable, FieldDefinition, PageData

class UserTable(NiceTable):
    async def query(self, query_values: dict, page: int = 1, page_size: int = 20) -> PageData:
        # Implement data query logic
        data = [{"id": 1, "name": "John", "status": "active"}]
        return PageData(data=data, total=1)

fields = [
    FieldDefinition(name="id", title="ID", type="integer", show_in_table=True),
    FieldDefinition(name="name", title="Name", type="text", show_in_table=True, show_in_query=True),
    FieldDefinition(
        name="status", 
        title="Status", 
        type="tag",
        input_type="select",
        selections={"active": "Active|green", "inactive": "Inactive|red"},
        show_in_table=True,
    ),
]

table = UserTable(fields=fields, id_field="id", heading="User List")
ui.run()
```

### NiceForm Example

```python
from nicegui import ui
from niceguiext import NiceForm, FormConfig
from niceguiext.form import FieldDefinition

fields = [
    FieldDefinition(name="name", field_type=str, title="Name", required=True),
    FieldDefinition(name="age", field_type=int, title="Age", min_value=0, max_value=120),
    FieldDefinition(name="email", field_type=str, title="Email"),
]

async def handle_submit(form_data: dict):
    print("Submitted data:", form_data)
    ui.notify("Submit successful!", color="positive")

form = NiceForm(
    fields=fields,
    config=FormConfig(title="User Info"),
    on_submit=handle_submit,
)

ui.run()
```

## Documentation

Full documentation is available in the [docs](./docs) directory:

- [Documentation Home](./docs/index_en.md)
- [NiceTable Component](./docs/NiceTable_en.md)
- [NiceCRUD Component](./docs/NiceCRUD_en.md)
- [NiceForm Component](./docs/NiceForm_en.md)
- [show_error Utilities](./docs/show_error_en.md)

## Examples

More examples are available in the [examples](./examples) directory:

| Example | Description |
|---------|-------------|
| `nicecrud_simple.py` | NiceCRUD simple example |
| `nicecrud_example.py` | NiceCRUD complete example |
| `nicecrud_advanced.py` | NiceCRUD advanced usage |
| `nicecrud_grid.py` | NiceCRUD grid mode |
| `nicetable_example.py` | NiceTable example |
| `form_field_definition_example.py` | NiceForm example |
| `validation_example.py` | Validation example |

## Contributing

Contributions are welcome!

### Publishing New Versions

Make sure the environment variable `UV_PUBLISH_TOKEN` is set to a PyPI secret token.

```bash
uv build
uv publish
```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).
