# marimo-utils

Utilities for working with marimo notebooks.

## Installation

```bash
pip install marimo-utils
```

## Usage

### `@add_marimo_display()` decorator

Adds a `_display_` method to Pydantic models for rich rendering in marimo notebooks.

```python
from pydantic import BaseModel
from marimo_utils import add_marimo_display

@add_marimo_display()
class MyConfig(BaseModel):
    name: str
    value: int
```

When a `MyConfig` instance is the last expression in a marimo cell, it renders with the class name, source file path, and all field values.
