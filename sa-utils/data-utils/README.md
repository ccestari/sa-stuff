# Data Utilities

Reusable data transformation utilities for SA data engineering projects.

## Modules

### column_transformers.py

Column naming and structure transformation utilities.

**Functions:**

- `camel_to_snake(name)` - Convert camelCase to snake_case
- `flatten_dict(d, parent_key='', sep='_', convert_to_snake=False)` - Flatten nested dictionaries

**Usage:**

```python
from sa_utils.data_utils.column_transformers import camel_to_snake, flatten_dict

# Convert column names
camel_to_snake('studentId')  # Returns: 'student_id'

# Flatten nested structure
data = {'student': {'id': 123, 'name': 'John'}}
flatten_dict(data)  # Returns: {'student_id': 123, 'student_name': 'John'}

# Flatten without renaming
flatten_dict(data, convert_to_snake=False)  # Returns: {'student_id': 123, 'student_name': 'John'}
```

## When to Use

Use these utilities when you need to transform data for specific downstream systems that require different naming conventions. 

**Default behavior**: Keep original API column names to maintain compatibility with existing reports and systems.
