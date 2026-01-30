# show_error and show_warn Component Documentation

`show_error` and `show_warn` are utility functions for displaying error and warning messages with consistent visual styling.

## Features

- Eye-catching error/warning styles
- Message display with icons
- Returns UI element references for dynamic binding

## Installation

```bash
pip install niceguiext
```

## Basic Usage

### show_error

Display error messages with red text and yellow background:

```python
from nicegui import ui
from niceguiext import show_error

# Display static error message
show_error("An error occurred!")

ui.run()
```

### show_warn

Display warning messages with orange text and white background:

```python
from nicegui import ui
from niceguiext import show_warn

# Display warning message
show_warn("This is a warning message")

ui.run()
```

## Function Signatures

### show_error

```python
def show_error(message: str = "Something went horribly wrong") -> tuple[ui.label, ui.row]:
    """
    Display error message
    
    Args:
        message: Error message text
    
    Returns:
        tuple: (label_element, row_element) - The label element and row container element
    """
```

### show_warn

```python
def show_warn(message: str = "Something went not quite as horribly wrong, but still not good") -> None:
    """
    Display warning message
    
    Args:
        message: Warning message text
    """
```

## Dynamic Binding

`show_error` returns the label element and row container element for dynamic binding:

```python
from nicegui import ui
from niceguiext import show_error

# Create reactive error state
error_state = {"msg": "", "visible": False}

# Create error display component
label_element, row_element = show_error("")

# Bind text and visibility
label_element.bind_text_from(error_state, "msg")
row_element.bind_visibility_from(error_state, "visible")

# Simulate error occurrence
def trigger_error():
    error_state["msg"] = "Operation failed: Unable to connect to server"
    error_state["visible"] = True

def clear_error():
    error_state["visible"] = False

ui.button("Trigger Error", on_click=trigger_error)
ui.button("Clear Error", on_click=clear_error)

ui.run()
```

## Style Description

### show_error Styles

- Background color: Yellow (`bg-yellow-100`)
- Text color: Red (`text-red-500`)
- Left border: Yellow thick border (`border-l-8 border-yellow-500`)
- Icon: Error icon (`error`)
- Font: Bold (`font-bold`)

### show_warn Styles

- Background color: White (`bg-white`)
- Text color: Orange (`text-orange-500`)
- Left border: Orange border (`border-l-4 border-orange-500`)
- Icon: Warning icon (`warning`)
- Padding: `p-4`

## Using in Forms

Common usage in form validation to display errors:

```python
from nicegui import ui
from niceguiext import show_error

class MyForm:
    def __init__(self):
        self.errormsg = {"msg": "", "visible": False}
        
        with ui.card():
            ui.input("Username", on_change=self.validate)
            ui.input("Password", password=True, on_change=self.validate)
            
            # Error display area
            errlabel, errrow = show_error("")
            errlabel.bind_text_from(self.errormsg, "msg")
            errrow.bind_visibility_from(self.errormsg, "visible")
            
            ui.button("Submit", on_click=self.submit)
    
    def validate(self, e):
        if len(e.value) < 3:
            self.errormsg["msg"] = "Input must be at least 3 characters"
            self.errormsg["visible"] = True
        else:
            self.errormsg["visible"] = False
    
    def submit(self):
        if self.errormsg["visible"]:
            ui.notify("Please fix errors before submitting", color="negative")
        else:
            ui.notify("Submit successful", color="positive")

MyForm()
ui.run()
```

## Custom Styles

If you need custom styles, directly modify the returned elements:

```python
from nicegui import ui
from niceguiext import show_error

label, row = show_error("Custom error")

# Modify row container styles
row.classes(remove="bg-yellow-100", add="bg-red-100")

# Modify label styles
label.classes(add="text-lg")

ui.run()
```
