# Parameter Registry Specification

## Overview

The **Parameter Registry** is a package management system for *Parameters*: structured, versioned objects composed of multiple file types (`.py`, `.js`, `.md`, etc.), explicit dependencies, ownership, and deterministic resolution rules.

Unlike traditional package managers that version a single artifact, a **Parameter version** is a *composite* that binds together specific versions of multiple file types.

This design supports:

* deterministic builds
* language-agnostic consumption
* independent evolution of file types
* explicit ownership and provenance
* a first-class `dev` channel

---

## Core Concepts

### Parameter

A **Parameter** is a named package owned by a user or organization.

Properties:

* `owner`
* `name`
* `description`
* `dependencies` (other Parameters)

A Parameter **does not contain files directly** — files are attached through versions.

---

### Ownership

Parameters are **namespaced by owner**.

```haskell
owner/parameter
```

This allows:

* forks
* competing implementations
* safe reuse of names

Examples:

```haskell
andrew/Axis
evezor/Axis
```

Ownership is resolved first during package lookup.

---

## Versioning Model

### Parameter Versions (Major Versions)

* Versions are **integers only**: `1, 2, 3, ...`
* Each version represents a **stable release**
* Versions are immutable once published

In addition:

* Each Parameter may have **exactly one dev version**
* `dev` has **no version number**
* `dev` is mutable and may change at any time

**Design Note:** There is no patch mechanism. If a bug is found in version 3, the fix must be released as version 4. This is intentional — Parameters are designed to be small (nano/picoservices), and this approach forces the ecosystem forward without fragmentation.

---

### File Versions (Minor Versions)

Each file type evolves independently.

A Parameter version **pins** a specific version of each file type.

Example evolution:

| Parameter Version | JS | PY | MD |
| ----------------- | -- | -- | -- |
| 1                 | 1  | 1  | 1  |
| 2                 | 2  | 3  | 1  |
| 3                 | 2  | 4  | 2  |
| 4                 | 3  | 4  | 2  |

This allows:

* documentation updates without code changes
* language-specific iteration
* reuse of stable components

---

## File Types

Each file belongs to:

* one Parameter
* one file type (`js`, `py`, `md`, `dependencies`, …)
* one integer version

File versions are **monotonic per file type**, but not required to align across types.

### New File Types

If a new file type is added to the system after a Parameter version has been published, queries for that file type against old versions will return a **default document**. This ensures backwards compatibility as the system evolves.

---

## Dev Semantics

The `dev` version:

* has `version = NULL`
* is marked `is_dev = true`
* **does not participate in "latest" resolution**
* always resolves to explicitly defined file versions

Typical usage:

* active development
* CI pipelines
* internal tooling

### Dev Workflow

All edits made in the Parameter Editor are pushed to `:dev`. The dev version is fully mutable — any file can be changed to any content at any time. This includes "rolling back" by simply overwriting with previous content.

Promotion from `dev` to a stable version is **explicit and intentional**. When a stable version is created, it pulls the current state from `:dev` and freezes it.

---

## Latest Semantics

**Latest** is defined as:

> The highest numbered stable version (`MAX(version) WHERE is_dev = false`)

Rules:

* `latest` never refers to `dev`
* deterministic
* cacheable
* safe for production use

---

## Package Notation

### Canonical Notation

```haskell
owner/parameter:selector
```

Where `selector` is one of:

* an integer version (`:3`)
* `:latest`
* `:dev`

---

### Examples

```haskell
andrew/Axis:1
andrew/Axis:latest
andrew/Axis:dev
evezor/Planner:2
```

---

### Filetype Selectors

Append `[filetypes]` to query specific file types from a resolved version:

```haskell
owner/Parameter:selector[filetypes]
```

Where `filetypes` is one of:

* a single type (`[js]`)
* a comma-separated list (`[py,md]`)
* wildcard (`[*]`) — all file types

---

### Filetype Selector Examples

```haskell
owner/Parameter:latest[js]
owner/Parameter:dev[py,md]
owner/Parameter:4[*]
```

| Query                        | Resolves To                     |
| ---------------------------- | ------------------------------- |
| `andrew/Axis:latest[js]`     | JS file from latest version     |
| `andrew/Axis:dev[py,md]`     | PY and MD files from dev        |
| `andrew/Axis:4[*]`           | All files from version 4        |

If omitted, `[*]` is implied (all file types are returned).

---

### Implicit Defaults

If omitted:

* owner → **required**
* selector → `:latest`
* filetype → `[*]`

```haskell
andrew/Axis
→ andrew/Axis:latest[*]
```

---

## Resolution Rules

Resolution occurs in the following order:

1. Resolve **owner**
2. Resolve **parameter**
3. Resolve **parameter version**
4. Resolve **file mappings**
5. Resolve **dependencies (recursively)**

---

### Resolution Examples

#### Example 1: Stable Resolution

```haskell
andrew/Axis:3
```

Resolves to:

```json
{
  "parameter": "Axis",
  "owner": "andrew",
  "version": 3,
  "files": {
    "js": 2,
    "py": 4,
    "md": 2
  }
}
```

---

#### Example 2: Latest

```haskell
andrew/Axis:latest
```

Equivalent to:

```haskell
andrew/Axis:4
```

---

#### Example 3: Dev

```haskell
andrew/Axis:dev
```

Resolves to:

```json
{
  "parameter": "Axis",
  "owner": "andrew",
  "version": "dev",
  "files": {
    "js": 3,
    "py": 4,
    "md": 2
  }
}
```

> Note: dev mappings are explicit — not inferred.

---

## Dependencies

Dependencies are declared in `dependencies.txt` and **frozen with each published version**.

Each dependency may specify:

* owner
* selector (`:version`, `:latest`, `:dev`)

Example:

```json
{
  "dependencies": [
    "evezor/Planner:latest",
    "andrew/Servo:2"
  ]
}
```

### Dependency Snapshot Behavior

When a Parameter version is published, its dependencies are resolved and frozen at that moment. For example:

* You publish `andrew/Axis:1` with dependency `evezor/Planner:latest`
* At publish time, `evezor/Planner:latest` resolves to version 2
* Version 1 of Axis is frozen with Planner v2

Later, even if Planner releases v5, installing `andrew/Axis:1` will still resolve to Planner v2. This ensures **deterministic, reproducible builds**.

Dependencies are resolved **recursively** and deterministically.

---

## Why This Design?

### 1. Integer Versions Only

* Simple mental model
* Fast comparison
* No semantic ambiguity
* Easy indexing and constraints

---

### 2. Composite Versions

Traditional package managers assume a single artifact.

This system acknowledges reality:

* documentation
* bindings
* reference implementations
* language variants

All evolve independently.

---

### 3. Explicit Dev Channel

* No accidental promotion
* No "dirty latest"
* Clear CI vs production boundary

---

### 4. Ownership as First-Class

* Enables forks
* Avoids naming conflicts
* Supports ecosystem growth

---

### 5. Database-Native Resolution

* All invariants enforced at the DB level
* No "best effort" resolution
* Strong guarantees under concurrency

---

## Invariants (Enforced by Schema)

* Only one `dev` version per Parameter
* Stable versions are unique per Parameter
* `dev` cannot have a version number
* Stable versions must have a version number
* File versions are immutable once referenced
* `latest` excludes `dev`

---

## Common Use Cases

### Production Deployment

```haskell
andrew/Axis:latest
```

### Reproducible Build

```haskell
andrew/Axis:3
```

### Active Development

```haskell
andrew/Axis:dev
```

### Cross-Organization Dependency

```haskell
evezor/Planner:latest
```

---

## Summary

This registry design prioritizes:

* **determinism**
* **clarity**
* **composability**
* **long-term maintainability**

It avoids the pitfalls of semantic versioning complexity while still enabling real-world evolution of multi-language systems.

---

## Future Considerations

The following features are not part of the initial specification but may be added as the system matures. Any additions should be **backwards-compatible** with the existing notation and behavior.

### 1. Version Blacklisting / Deprecation

A flag to mark specific versions (or file versions) as deprecated or blacklisted due to security vulnerabilities or critical bugs.

Open questions:
* Should blacklisted versions prevent installation, warn, or just flag in UI?
* Should blacklisting a file version automatically taint all Parameter versions that reference it?
* Should there be an audit trail recording why a version was blacklisted?

---

### 2. Dependency Constraint Notation

Extended selector syntax for dependency constraints:

```haskell
evezor/Planner:>=3      # at least version 3
evezor/Planner:2|3      # version 2 or 3
evezor/Planner:!dev     # any stable version
```

This would be handled by the package manager's lexer and has no impact on the underlying data model.

---

### 3. URL Encoding Rules

The canonical notation `owner/parameter:selector[filetypes]` contains characters (`:`, `[`, `]`) that require escaping in URLs. Define standard encoding rules for use in:

* REST APIs
* Web URLs
* CLI arguments

---

### 4. Lockfile Format

A standardized format for capturing the fully-resolved dependency tree of a project. This would enable:

* Reproducible builds across machines
* Dependency auditing
* Offline resolution

---

### 5. Cyclic Dependency Detection

Formal rules for detecting and rejecting cyclic dependencies during resolution. Currently implied by "recursive resolution" but may need explicit handling.
