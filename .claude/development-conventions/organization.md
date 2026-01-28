# Code Organization

## Principles

- Organize code into clearly separated modules and discrete, testable units
- Group code by feature or responsibility (high cohesion)
- Changes to one module should not require changes to others
- Use consistent naming conventions, file structure, and architecture patterns
- Follow DRY, but never create tight coupling just to avoid repetition
- No circular dependencies between modules
- Each function/class should have one clear purpose

## Module Design

- **Module size**: Split when a file exceeds ~800 lines or has multiple unrelated responsibilities
- **Public functions/methods at the top, private helpers below**
- **Private members**: Prefix with `_` for internal implementation details

```python
# src/package/module/file.py

# Imports
...

# Public interface
...

# Private helpers
...
```

## Import Organization

Organize imports in this order (enforced by ruff):

1. Standard library
2. Third-party packages
3. Local application imports

```python
import json
from collections.abc import Sequence
from pathlib import Path

import numpy as np
from pydantic import BaseModel

from chain_reaction.core import Config
from chain_reaction.utils import validate_input
```

Use absolute imports. Avoid `from module import *`.
