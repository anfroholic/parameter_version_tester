# Parameter Registry - System Architecture

## Database Entity-Relationship Diagram

```mermaid
erDiagram
    owners ||--o{ parameters : "owns"
    parameters ||--o{ files : "contains"
    parameters ||--o{ parameter_versions : "has"
    file_types ||--o{ files : "categorizes"
    file_types ||--o{ parameter_version_files : "references"
    parameter_versions ||--o{ parameter_version_files : "maps"
    parameter_versions ||--o{ parameter_version_dependencies : "declares"
    parameters ||--o{ parameter_version_dependencies : "depends_on"

    owners {
        serial id PK
        text username UK
    }

    parameters {
        serial id PK
        int owner_id FK
        text name
        text description
        timestamptz created_at
    }

    file_types {
        serial id PK
        text name UK
    }

    files {
        serial id PK
        int parameter_id FK
        int file_type_id FK
        int version
        text path
        text content
        text change_note
        timestamptz created_at
    }

    parameter_versions {
        serial id PK
        int parameter_id FK
        int version "NULL for dev"
        bool is_dev
        timestamptz created_at
    }

    parameter_version_files {
        serial id PK
        int parameter_version_id FK
        int file_type_id FK
        int file_version
    }

    parameter_version_dependencies {
        serial id PK
        int parameter_version_id FK
        int depends_on_parameter_id FK
        int depends_on_version "NULL for dev"
        bool depends_on_is_dev
        text original_selector
        timestamptz created_at
    }
```

## API Endpoints Overview

```mermaid
flowchart TB
    subgraph Client
        REQ[HTTP Request]
    end

    subgraph "FastAPI Server :8000"
        subgraph "Health & Meta"
            ROOT["GET /"]
            HEALTH["GET /health"]
            STATS["GET /stats"]
            FTYPES["GET /file-types"]
            LOAD["POST /load"]
            REPLAY["POST /replay"]
        end

        subgraph "Owner Endpoints"
            OWNERS["GET /owners"]
            OWNER["GET /owners/{username}"]
            OWNER_CREATE["POST /owners"]
        end

        subgraph "Parameter Endpoints"
            PARAMS["GET /parameters"]
            PARAM["GET /parameters/{owner}/{name}"]
        end

        subgraph "Mutation Endpoints"
            FILEVERS["POST /.../file-versions"]
            PUBLISH["POST /.../publish"]
            FORK["POST /.../fork"]
        end

        subgraph "Resolution Endpoints"
            RESOLVE["GET /resolve/{query}"]
            DEPS["GET /dependencies/{owner}/{name}"]
        end
    end

    subgraph "PostgreSQL :5455"
        DB[(Database)]
        subgraph "Resolver Functions"
            F1["resolve_parameter()"]
            F2["resolve_parameter_version()"]
            F2b["resolve_version_file_map()"]
            F3["resolve_files()"]
            F4["resolve_package()"]
            F5["resolve_dependency_tree()"]
            F6["resolve_dependencies()"]
        end
        subgraph "Write Functions"
            P1["publish_parameter()"]
        end
        subgraph "Triggers"
            T1["check_cyclic_dependency()"]
            T2["prevent_file_delete_if_used()"]
        end
    end

    REQ --> ROOT & HEALTH & STATS & FTYPES & LOAD & REPLAY
    REQ --> OWNERS & OWNER & OWNER_CREATE
    REQ --> PARAMS & PARAM
    REQ --> FILEVERS & PUBLISH & FORK
    REQ --> RESOLVE & DEPS

    ROOT & HEALTH & STATS & FTYPES & LOAD & REPLAY --> DB
    OWNERS & OWNER & OWNER_CREATE --> DB
    PARAMS & PARAM --> DB
    FILEVERS --> DB
    PUBLISH --> P1
    FORK --> DB
    RESOLVE --> F4
    DEPS --> F5
    F4 --> F1 --> F2 --> F3
    F5 --> F1 --> F6
    P1 --> DB
    F1 & F2 & F2b & F3 & F4 & F5 & F6 --> DB
    T1 & T2 --> DB
```

## Package Resolution Flow

### Stable / Specific Version

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL

    C->>API: GET /resolve/evezor/Floe:latest[js,py]
    API->>API: Parse query notation

    API->>DB: resolve_package('evezor', 'Floe', 'latest', ['js','py'])

    activate DB
    DB->>DB: resolve_parameter('evezor', 'Floe')
    Note over DB: Returns parameter_id = 42

    DB->>DB: resolve_parameter_version(42, 'latest')
    Note over DB: Finds MAX(version) WHERE is_dev=FALSE
    Note over DB: Returns parameter_version_id = 87

    DB->>DB: resolve_files(42, 87, ['js','py'])
    Note over DB: Joins parameter_version_files<br/>with files table
    deactivate DB

    DB-->>API: Returns files with content
    API-->>C: ResolvedPackage JSON
```

### Dev (merged) Resolution

When the selector is `:dev`, `resolve_package` merges the dev file map over the latest stable version. Dev mappings win; any file types not touched in dev fall back to the latest stable version's mappings.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL

    C->>API: GET /resolve/evezor/Floe:dev
    API->>API: Parse query notation

    API->>DB: resolve_package('evezor', 'Floe', 'dev', NULL)

    activate DB
    DB->>DB: resolve_parameter('evezor', 'Floe')

    DB->>DB: resolve_version_file_map(dev_version_id)
    Note over DB: Dev file mappings (only touched types)

    DB->>DB: resolve_version_file_map(latest_version_id)
    Note over DB: Latest stable mappings (fills gaps)

    DB->>DB: Merge: dev wins, latest fills missing types
    DB->>DB: resolve_files(42, merged_map)
    Note over DB: Fetches actual file content
    deactivate DB

    DB-->>API: Returns merged files with content
    API-->>C: ResolvedPackage JSON
```

## Versioning Model

```mermaid
flowchart LR
    subgraph "Parameter: Floe"
        subgraph "Parameter Versions"
            DEV[":dev"]
            V1[":1"]
            V2[":2"]
            V3[":3 (latest)"]
        end

        subgraph "File Versions"
            JS1["js v1"]
            JS2["js v2"]
            JS3["js v3"]
            PY1["py v1"]
            PY2["py v2"]
            MD1["md v1"]
            MD2["md v2"]
        end
    end

    DEV -.->|mutable| JS3
    DEV -.->|mutable| PY2
    DEV -.->|mutable| MD2

    V1 -->|frozen| JS1
    V1 -->|frozen| PY1
    V1 -->|frozen| MD1

    V2 -->|frozen| JS2
    V2 -->|frozen| PY1
    V2 -->|frozen| MD1

    V3 -->|frozen| JS2
    V3 -->|frozen| PY2
    V3 -->|frozen| MD2
```

## Dependency Resolution

```mermaid
flowchart TB
    subgraph "Dependency Tree for Axis:1"
        AXIS["Axis:1<br/>(depth 0)"]
        PLANNER["Planner:2<br/>(depth 1)"]
        FLOE["Floe:3<br/>(depth 1)"]
        CORE["Core:1<br/>(depth 2)"]
        UTILS["Utils:4<br/>(depth 2)"]
    end

    AXIS --> PLANNER
    AXIS --> FLOE
    PLANNER --> CORE
    FLOE --> CORE
    FLOE --> UTILS

    style AXIS fill:#e1f5fe
    style PLANNER fill:#fff3e0
    style FLOE fill:#fff3e0
    style CORE fill:#f3e5f5
    style UTILS fill:#f3e5f5
```

## Docker Architecture

```mermaid
flowchart TB
    subgraph "Docker Compose"
        subgraph "api"
            FASTAPI["FastAPI<br/>:8000"]
        end

        subgraph "db"
            PG["PostgreSQL 16<br/>:5455"]
            INIT["init/<br/>01_initdb.sql<br/>02_resolver.sql<br/>03_dependencies.sql<br/>04_publish.sql"]
        end
    end

    FASTAPI -->|psycopg2| PG
    INIT -->|auto-exec| PG

    USER((User)) --> FASTAPI
```

## Query Notation Reference

| Format | Example | Description |
|--------|---------|-------------|
| `owner/param:latest` | `evezor/Floe:latest` | Latest stable version |
| `owner/param:dev` | `evezor/Floe:dev` | Development version |
| `owner/param:N` | `evezor/Floe:2` | Specific version |
| `owner/param:selector[types]` | `evezor/Floe:latest[js,py]` | Filter file types |

## Publish Flow

Publishing snapshots the current dev state as a new numbered stable version, then resets dev to a clean slate.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL

    C->>API: POST /parameters/evezor/Floe/publish
    API->>DB: publish_parameter(parameter_id)

    activate DB
    Note over DB: 1. Verify dev version exists
    Note over DB: 2. Next version = MAX(version) + 1
    Note over DB: 3. Create new stable parameter_version
    Note over DB: 4. Snapshot file map (dev wins, latest fills gaps)
    Note over DB: 5. Freeze deps — resolve :latest refs to actual versions
    Note over DB: 6. Clear dev file mappings (clean slate)
    deactivate DB

    DB-->>API: Returns new version number
    API-->>C: {"parameter": "Floe", "published_version": 4}
```

## Fork Flow

Forking copies a parameter (dev state if available, otherwise latest stable) into a new owner's namespace as version 1.

```mermaid
sequenceDiagram
    participant C as Client
    participant API as FastAPI
    participant DB as PostgreSQL

    C->>API: POST /parameters/evezor/Floe/fork
    Note over C: Body: {"target_owner": "andrew"}

    API->>DB: Resolve source (dev if exists, else latest)
    API->>DB: Ensure target owner exists
    API->>DB: Create parameter under target owner
    API->>DB: Copy all files as v1
    API->>DB: Create stable version 1 with file mappings

    DB-->>API: Files copied count
    API-->>C: {"source": "evezor/Floe", "forked_to": "andrew/Floe", "files_copied": 5}
```

## Endpoint Reference

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Serves interactive HTML UI |
| GET | `/health` | Health check |
| GET | `/stats` | Counts: owners, parameters, versions, files, dependencies |
| GET | `/file-types` | List registered file types |
| POST | `/load` | Load parameters from `/app/Parameters` folder |
| POST | `/replay` | Replay all recorded mutations from `replay.json` |
| GET | `/owners` | List all owners |
| GET | `/owners/{username}` | Get single owner |
| POST | `/owners` | Create owner |
| GET | `/parameters?owner={owner}` | List parameters (optional owner filter) |
| GET | `/parameters/{owner}/{name}` | Full parameter detail with all versions |
| POST | `/parameters/{owner}/{name}/file-versions` | Create new file versions, update dev mapping |
| POST | `/parameters/{owner}/{name}/publish` | Publish dev → new stable version |
| POST | `/parameters/{owner}/{name}/fork` | Fork parameter to another owner |
| GET | `/resolve/{query}` | Resolve package query → files with content |
| GET | `/dependencies/{owner}/{name}?selector=` | Full recursive dependency tree |
