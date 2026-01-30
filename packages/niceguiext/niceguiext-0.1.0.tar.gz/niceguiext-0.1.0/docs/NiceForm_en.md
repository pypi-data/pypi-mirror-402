# NiceForm Component Documentation

NiceForm is a form component based on field definition lists, supporting multiple input types (text, number, select, etc.), with data validation logic and submit/reset functionality.

## Features

- Multiple input types support (text, number, date, select, slider, etc.)
- Automatic type conversion and validation
- Optional and required field support
- Submit and reset callbacks
- Field change callbacks
- Reactive form validation state

## Installation

```bash
pip install niceguiext
```

## Basic Usage

```python
from nicegui import ui
from niceguiext import NiceForm, FormConfig
from niceguiext.form import FieldDefinition

# Define form fields
fields = [
    FieldDefinition(
        name="name",
        field_type=str,
        title="Name",
        description="Enter your name",
        required=True,
        default="",
    ),
    FieldDefinition(
        name="age",
        field_type=int,
        title="Age",
        min_value=0,
        max_value=120,
        default=25,
    ),
    FieldDefinition(
        name="email",
        field_type=str,
        title="Email",
        required=False,
        default="",
    ),
]

# Form configuration
config = FormConfig(
    title="User Info",
    submit_button_text="Submit",
    reset_button_text="Reset",
)

async def handle_submit(form_data: dict):
    print("Submitted data:", form_data)
    ui.notify("Submit successful!", color="positive")

# Create form
form = NiceForm(
    fields=fields,
    config=config,
    on_submit=handle_submit,
)

ui.run()
```

## FieldDefinition Field Definition

The `FieldDefinition` used by NiceForm is a dataclass, slightly different from the one in NiceTable/NiceCRUD.

### Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `name` | str | Required | Field name |
| `field_type` | Any | Required | Field type (Python type) |
| `default` | Any | None | Default value |
| `title` | str | None | Field display title |
| `description` | str | None | Field description (shown as placeholder or tooltip) |
| `required` | bool | True | Whether required |
| `min_value` | float | None | Minimum value (numeric types) |
| `max_value` | float | None | Maximum value (numeric types) |
| `step` | float | None | Step value (numeric types) |
| `input_type` | str | None | Input type: `"select"`, `"multiselect"`, `"slider"`, `"number"` |
| `readonly` | bool | False | Whether readonly |
| `selections` | dict | None | Selection options |
| `exclude` | bool | False | Whether to exclude from display |

### Supported field_type Types

| Python Type | Input Component |
|-------------|-----------------|
| `str` | Text input |
| `int` | Number input |
| `float` | Number input |
| `bool` | Switch |
| `date` | Date picker |
| `time` | Time picker |
| `datetime` | DateTime picker |
| `Path` | Text input |
| `list[str]` | Text input (comma separated) |
| `list[int]` | Text input (comma separated) |
| `Literal[...]` | Dropdown select |
| `Optional[T]` | Clearable input of corresponding type |

## FormConfig Configuration Class

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `title` | str | None | Form title |
| `submit_button_text` | str | "Submit" | Submit button text |
| `reset_button_text` | str | "Reset" | Reset button text |
| `class_heading` | str | "text-xl font-bold" | Heading style class |
| `class_form_card` | str | "w-full p-4" | Form card style class |
| `column_count` | int | None | Form column count (auto-calculated) |
| `show_validation_errors` | bool | True | Whether to show validation errors |

## Complete Example

```python
from datetime import date
from pathlib import Path
from typing import Union, Literal

from nicegui import ui
from niceguiext import NiceForm, FormConfig
from niceguiext.form import FieldDefinition

@ui.page("/")
async def main():
    # Define form fields
    fields = [
        # Text field
        FieldDefinition(
            name="name",
            field_type=str,
            title="Name",
            description="Enter your name",
            required=True,
            default="",
        ),
        # Number field (with range limits)
        FieldDefinition(
            name="age",
            field_type=int,
            title="Age",
            description="Enter your age",
            min_value=0,
            max_value=120,
            default=25,
        ),
        # Optional field
        FieldDefinition(
            name="email",
            field_type=Union[str, type(None)],
            title="Email",
            description="Enter your email address",
            required=False,
            default=None,
        ),
        # Select field
        FieldDefinition(
            name="gender",
            field_type=str,
            title="Gender",
            input_type="select",
            selections={"male": "Male", "female": "Female", "other": "Other"},
            default="male",
        ),
        # Slider field
        FieldDefinition(
            name="salary",
            field_type=float,
            title="Expected Salary",
            min_value=0.0,
            max_value=100000.0,
            input_type="slider",
            step=1000.0,
            default=10000.0,
        ),
        # List field
        FieldDefinition(
            name="skills",
            field_type=list[str],
            title="Skills",
            description="Enter your skills, separated by commas",
            default=[],
        ),
        # Boolean field
        FieldDefinition(
            name="is_active",
            field_type=bool,
            title="Is Active",
            default=True,
        ),
        # Date field
        FieldDefinition(
            name="birth_date",
            field_type=date,
            title="Birth Date",
            default=date(1990, 1, 1),
        ),
        # Path field (optional)
        FieldDefinition(
            name="profile_path",
            field_type=Union[Path, type(None)],
            title="Profile Path",
            required=False,
            default=None,
        ),
        # Literal type (enum select)
        FieldDefinition(
            name="priority",
            field_type=Literal["low", "medium", "high"],
            title="Priority",
            default="medium",
        ),
    ]

    # Form configuration
    config = FormConfig(
        title="User Information Form",
        submit_button_text="Submit",
        reset_button_text="Reset",
        column_count=2,
        show_validation_errors=True,
    )

    async def handle_submit(form_data: dict):
        """Handle form submission"""
        print("Form submission data:", form_data)
        ui.notify("Submit successful!", color="positive")

    def handle_change(field_name: str, form_data: dict):
        """Handle field change"""
        print(f"Field {field_name} changed: {form_data.get(field_name)}")

    # Create form
    form = NiceForm(
        fields=fields,
        config=config,
        on_submit=handle_submit,
        on_change=handle_change,
    )

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="NiceForm Example")
```

## Dynamic Selection Options

Use the `select_options` parameter to dynamically get selection options:

```python
async def get_select_options(field_name: str, form_data: dict) -> dict:
    """Dynamically get selection options"""
    if field_name == "city":
        # Return city list based on province
        province = form_data.get("province")
        if province == "california":
            return {"la": "Los Angeles", "sf": "San Francisco", "sd": "San Diego"}
        elif province == "texas":
            return {"houston": "Houston", "dallas": "Dallas"}
    return {}

form = NiceForm(
    fields=fields,
    config=config,
    on_submit=handle_submit,
    select_options=get_select_options,
)
```

## Accessing Form Data

Access current form data through `form.form_data`:

```python
form = NiceForm(fields=fields, config=config)

# Get current form data
current_data = form.form_data

# Check form validation state
is_valid = form.form_valid
```

## Form Validation

NiceForm automatically performs type validation and range validation:

- **Type validation**: Automatically converts and validates values based on `field_type`
- **Range validation**: Checks `min_value` and `max_value` for numeric types
- **Required validation**: Checks if non-optional fields have values

Validation errors are displayed at the bottom of the form (if `show_validation_errors=True`), and the submit button is disabled when the form is invalid.

## Manually Refresh Form

To manually refresh the form, call:

```python
form.create_form.refresh()
```

## Reset Form

Clicking the reset button restores all fields to default values. You can also call it manually:

```python
form.handle_reset()
```
