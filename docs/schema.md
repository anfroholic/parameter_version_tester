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
            HEALTH["/health"]
            STATS["/stats"]
            FTYPES["/file-types"]
        end

        subgraph "Owner Endpoints"
            OWNERS["/owners"]
            OWNER["/owners/{username}"]
        end

        subgraph "Parameter Endpoints"
            PARAMS["/parameters"]
            PARAM["/parameters/{owner}/{name}"]
        end

        subgraph "Resolution Endpoints"
            RESOLVE["/resolve/{query}"]
            DEPS["/dependencies/{owner}/{name}"]
        end
    end

    subgraph "PostgreSQL :5455"
        DB[(Database)]
        subgraph "Resolver Functions"
            F1["resolve_parameter()"]
            F2["resolve_parameter_version()"]
            F3["resolve_files()"]
            F4["resolve_package()"]
            F5["resolve_dependency_tree()"]
        end
    end

    REQ --> HEALTH & STATS & FTYPES
    REQ --> OWNERS & OWNER
    REQ --> PARAMS & PARAM
    REQ --> RESOLVE & DEPS

    HEALTH --> DB
    STATS --> DB
    FTYPES --> DB
    OWNERS --> DB
    OWNER --> DB
    PARAMS --> DB
    PARAM --> DB
    RESOLVE --> F4
    DEPS --> F5
    F4 --> F1 --> F2 --> F3
    F5 --> F1
    F1 & F2 & F3 & F4 & F5 --> DB
```

## Package Resolution Flow

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
            INIT["init/<br/>01_initdb.sql<br/>02_resolver.sql<br/>03_dependencies.sql"]
        end

        subgraph "pgadmin"
            PGADMIN["PgAdmin<br/>:5050"]
        end
    end

    FASTAPI -->|psycopg2| PG
    PGADMIN -->|admin| PG
    INIT -->|auto-exec| PG

    USER((User)) --> FASTAPI
    USER --> PGADMIN
```

## Query Notation Reference

| Format | Example | Description |
|--------|---------|-------------|
| `owner/param:latest` | `evezor/Floe:latest` | Latest stable version |
| `owner/param:dev` | `evezor/Floe:dev` | Development version |
| `owner/param:N` | `evezor/Floe:2` | Specific version |
| `owner/param:selector[types]` | `evezor/Floe:latest[js,py]` | Filter file types |
