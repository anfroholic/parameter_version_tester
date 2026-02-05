# Parameter Registry API

A versioned package registry for reusable parameters. Each parameter can contain multiple file types (js, py, html, etc.), each versioned independently. Parameters can declare dependencies on other parameters.

**Base URL:** `http://localhost:8000`

---

## Concepts

- **Owner** — a namespace (e.g. `evezor`). All parameters belong to an owner.
- **Parameter** — a named, versioned package under an owner (e.g. `evezor/GuiButton`).
- **File types** — each parameter can hold multiple file types (`js`, `py`, `html`, `config`, `environments`, `readme`, `requirements`, `dependencies`). Each file type is versioned independently.
- **Parameter version** — a numbered snapshot (v1, v2…) that pins specific file versions together. There is also a `dev` version that always points to the latest file edits.
- **Selector** — how you pick a version when resolving: `latest` (highest stable), `dev`, or a specific number like `1`.

---

## Health & Stats

### `GET /health`

Returns `healthy` if the database is reachable.

```
GET /health

200 OK
{ "status": "healthy" }
```

### `GET /stats`

Counts across the whole registry.

```
GET /stats

200 OK
{
  "owners": 1,
  "parameters": 80,
  "stable_versions": 80,
  "dev_versions": 0,
  "files": 340,
  "dependencies": 45
}
```

---

## Owners

### `GET /owners`

List every owner in the registry.

```
GET /owners

200 OK
[
  { "id": 1, "username": "evezor", "display_name": null, "email": null }
]
```

### `GET /owners/{username}`

Get a single owner. Returns **404** if not found.

```
GET /owners/evezor

200 OK
{ "id": 1, "username": "evezor", "display_name": null, "email": null }
```

---

## Parameters

### `GET /parameters`

List all parameters. Add `?owner=` to filter by owner.

```
GET /parameters?owner=evezor

200 OK
[
  {
    "id": 13,
    "owner": "evezor",
    "name": "ESP32Core",
    "description": null,
    "versions": [1],
    "has_dev": false
  },
  {
    "id": 22,
    "owner": "evezor",
    "name": "GuiButton",
    "description": null,
    "versions": [1],
    "has_dev": true
  }
]
```

- `versions` — list of stable (published) version numbers.
- `has_dev` — `true` if there are uncommitted changes in the dev version.

### `GET /parameters/{owner}/{name}`

Detailed view of a single parameter, including every version and which file versions each one pins.

```
GET /parameters/evezor/GuiButton

200 OK
{
  "id": 22,
  "owner": "evezor",
  "name": "GuiButton",
  "description": null,
  "versions": [
    {
      "version": 1,
      "is_dev": false,
      "file_mappings": { "js": 1, "py": 1, "html": 1, "config": 1 }
    },
    {
      "version": null,
      "is_dev": true,
      "file_mappings": { "js": 2, "py": 1, "html": 1, "config": 1 }
    }
  ]
}
```

In the example above, stable version 1 pins `js` at file version 1. The dev version has since moved `js` to file version 2.

---

## File Versioning

### `POST /parameters/{owner}/{name}/file-versions`

Push new content for one or more file types. This creates a new file version for each type and automatically updates the **dev** version mapping. It does **not** publish a stable version.

**Request body:**

```json
{
  "files": [
    { "file_type": "js",  "content": "console.log('hello');", "change_note": "initial draft" },
    { "file_type": "py",  "content": "print('hello')" }
  ]
}
```

`change_note` is optional on each file.

**Response:**

```
POST /parameters/evezor/GuiButton/file-versions

200 OK
{
  "parameter": "evezor/GuiButton",
  "created": [
    { "file_type": "js",  "new_version": 2, "path": "js.js", "change_note": "initial draft" },
    { "file_type": "py",  "new_version": 1, "path": "GuiButton.py", "change_note": null }
  ]
}
```

Returns **400** if `files` is empty or a `file_type` is not recognised. Returns **404** if the parameter does not exist.

---

## Package Resolution

### `GET /resolve/{query}`

The main way to fetch a parameter's files. The query string encodes everything:

```
owner/parameter:selector[file_type,file_type,...]
```

| Part | Required | Description |
|---|---|---|
| `owner` | yes | Owner username |
| `parameter` | yes | Parameter name |
| `:selector` | no (defaults to `latest`) | `latest`, `dev`, or an integer version |
| `[types]` | no (returns all) | Comma-separated file types to include |

**Examples:**

Fetch all files from the latest stable version of ESP32Core:

```
GET /resolve/evezor/ESP32Core:latest

200 OK
{
  "owner": "evezor",
  "parameter": "ESP32Core",
  "selector": "latest",
  "version": 1,
  "is_dev": false,
  "files": [
    { "file_type": "py",   "file_version": 1, "path": "ESP32Core.py",   "content": "..." },
    { "file_type": "js",   "file_version": 1, "path": "js.js",          "content": "..." },
    { "file_type": "html", "file_version": 1, "path": "html.html",      "content": "..." },
    { "file_type": "config", "file_version": 1, "path": "ESP32Core.json", "content": "..." }
  ]
}
```

Fetch only the `py` and `js` files from the dev version of GuiButton:

```
GET /resolve/evezor/GuiButton:dev[py,js]

200 OK
{
  "owner": "evezor",
  "parameter": "GuiButton",
  "selector": "dev",
  "version": null,
  "is_dev": true,
  "files": [
    { "file_type": "py", "file_version": 1, "path": "GuiButton.py", "content": "..." },
    { "file_type": "js", "file_version": 2, "path": "js.js",        "content": "..." }
  ]
}
```

Fetch a specific pinned version:

```
GET /resolve/evezor/AnalogInput:1

200 OK
{
  "owner": "evezor",
  "parameter": "AnalogInput",
  "selector": "1",
  "version": 1,
  "is_dev": false,
  "files": [ ... ]
}
```

Returns **400** if the query format is wrong, **404** if the parameter or version does not exist.

---

## Dependencies

### `GET /dependencies/{owner}/{name}?selector=`

Returns the full recursive dependency tree for a parameter version. The tree is resolved in the database using a recursive CTE with cycle detection (max depth 50).

`selector` defaults to `latest`.

```
GET /dependencies/evezor/AnalogInput?selector=latest

200 OK
{
  "root": "evezor/AnalogInput:latest",
  "dependencies": [
    { "depth": 0, "owner": "evezor", "parameter": "AnalogInput", "version": 1, "is_dev": false },
    { "depth": 1, "owner": "evezor", "parameter": "ESP32Core",   "version": 1, "is_dev": false }
  ]
}
```

`depth: 0` is the parameter itself. Each subsequent level represents a transitive dependency. In this example, `AnalogInput` depends directly on `ESP32Core`.

A deeper tree example — `GRBLScara` depends on `GRBLAxis`, which in turn depends on `GRBL`:

```
GET /dependencies/evezor/GRBLScara?selector=1

200 OK
{
  "root": "evezor/GRBLScara:1",
  "dependencies": [
    { "depth": 0, "owner": "evezor", "parameter": "GRBLScara", "version": 1, "is_dev": false },
    { "depth": 1, "owner": "evezor", "parameter": "GRBLAxis",  "version": 1, "is_dev": false },
    { "depth": 2, "owner": "evezor", "parameter": "GRBL",      "version": 1, "is_dev": false }
  ]
}
```

---

## File Types

### `GET /file-types`

List every registered file type.

```
GET /file-types

200 OK
[
  { "id": 1, "name": "js" },
  { "id": 2, "name": "py" },
  { "id": 3, "name": "html" },
  { "id": 4, "name": "config" },
  { "id": 5, "name": "environments" },
  { "id": 6, "name": "readme" },
  { "id": 7, "name": "requirements" },
  { "id": 8, "name": "dependencies" }
]
```

---

## Utility Endpoints

### `GET /`

Serves the interactive HTML UI.

### `GET /load`

Reloads all parameters from the `Parameters/` folder on disk into the database. Idempotent — safe to call multiple times. Also serves the interactive UI after loading.
