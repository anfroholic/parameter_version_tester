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

## Unwrap Parameter JSON Files

**Purpose:** Remove the outer parameter name key from `{Parameter}.json` files, flattening the structure to only contain the inner object.

**When to use:** When migrating to a system where the parameter name is derived from the filename/folder rather than being a key in the JSON.

**Script:**
```python
import os
import json

# Configuration
params_dir = r'path\to\app\Parameters'  # Update this path

# Find all {Parameter}/{Parameter}.json files (folder name matches file name)
for folder in os.listdir(params_dir):
    folder_path = os.path.join(params_dir, folder)
    if os.path.isdir(folder_path):
        json_file = os.path.join(folder_path, f'{folder}.json')
        if os.path.exists(json_file):
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Check if it has the expected structure (single key matching folder name)
            if folder in data and len(data) == 1:
                inner_content = data[folder]
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(inner_content, f, indent=2)
                print(f'Updated: {folder}/{folder}.json')
            else:
                print(f'Skipped (unexpected structure): {folder}/{folder}.json')

print('\nDone!')
```

**Usage:**
1. Update `params_dir` to point to your Parameters folder
2. Run with: `python script.py`

**Example transformation:**
- Before: `{"UART": {"ports": {...}, "constants": {...}}}`
- After: `{"ports": {...}, "constants": {...}}`

-----

