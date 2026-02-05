This file is a place where we will hold actions of overarching large shifts in the way we handle Parameters and filetypes

## Prepend Owner to Dependencies

**Purpose:** Add an owner prefix (e.g., `evezor/`) to all dependencies in `dependencies.txt` files within the Parameters folder.

**When to use:** When migrating to a system that requires owner namespacing for dependencies.

**Script:**
```python
import os
import glob

# Configuration
params_dir = r'path\to\app\Parameters'  # Update this path
owner_prefix = 'evezor/'  # Update this owner name

files = glob.glob(os.path.join(params_dir, '*', 'dependencies.txt'))

for filepath in files:
    with open(filepath, 'r') as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip empty lines and lines already prefixed
        if stripped and not stripped.startswith(owner_prefix):
            new_lines.append(owner_prefix + stripped + '\n')
        elif stripped:
            new_lines.append(stripped + '\n')

    with open(filepath, 'w') as f:
        f.writelines(new_lines)

    print(f'Updated: {os.path.basename(os.path.dirname(filepath))}')

print(f'\nTotal files updated: {len(files)}')
```

**Usage:**
1. Update `params_dir` to point to your Parameters folder
2. Update `owner_prefix` if using a different owner name
3. Run with: `python script.py`

**Example transformation:**
- Before: `Parameter`
- After: `evezor/Parameter`

-----

