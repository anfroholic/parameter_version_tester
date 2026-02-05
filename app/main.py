"""
Parameter Registry API - FastAPI REST service for the Parameter Registry.

Endpoints:
- GET /owners - List all owners
- GET /parameters - List all parameters (with optional owner filter)
- GET /parameters/{owner}/{name} - Get parameter details
- GET /resolve/{owner}/{name}:{selector} - Resolve a package query
- GET /resolve/{owner}/{name}:{selector}/{filetypes} - Resolve with file type filter
- GET /dependencies/{owner}/{name}:{selector} - Get dependency tree
"""

import os
import re
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone
from contextlib import asynccontextmanager

import psycopg2
import load_parameters as load_params_module
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Database connection pool
db_pool = None


def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432'),
        dbname=os.environ.get('POSTGRES_DB', 'mydb'),
        user=os.environ.get('POSTGRES_USER', 'anfro'),
        password=os.environ.get('POSTGRES_PASSWORD', 'password'),
        cursor_factory=RealDictCursor
    )


REPLAY_PATH = Path(__file__).parent / 'replay.json'
_replaying = False  # suppresses log_replay while replaying


def log_replay(method: str, path: str, body: dict | None = None):
    """Append a replayable request record to replay.json."""
    if _replaying:
        return
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "method": method,
        "path": path,
        "body": body,
    }

    # Load existing entries (treat missing or empty file as empty list)
    try:
        raw = REPLAY_PATH.read_text()
        entries = json.loads(raw) if raw.strip() else []
    except (FileNotFoundError, json.JSONDecodeError):
        entries = []

    entries.append(entry)
    REPLAY_PATH.write_text(json.dumps(entries, indent=2))


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="Parameter Registry API",
    description="REST API for the Parameter Registry - a versioned package management system",
    version="1.0.0",
    lifespan=lifespan
)

templates = Jinja2Templates(directory='htmldirectory')
app.mount("/static", StaticFiles(directory="static", html=True), name="static")


# Enable CORS for the interactive HTML
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for responses
class Owner(BaseModel):
    id: int
    username: str


class ParameterSummary(BaseModel):
    id: int
    owner: str
    name: str
    description: Optional[str]
    versions: List[int]
    has_dev: bool


class FileInfo(BaseModel):
    file_type: str
    file_version: int
    path: str
    content: str


class ResolvedPackage(BaseModel):
    owner: str
    parameter: str
    selector: str
    version: Optional[int]
    is_dev: bool
    files: List[FileInfo]


class DependencyNode(BaseModel):
    depth: int
    owner: str
    parameter: str
    version: Optional[int]
    is_dev: bool


class ParameterVersion(BaseModel):
    version: Optional[int]
    is_dev: bool
    file_mappings: dict


class FileVersionUpdate(BaseModel):
    file_type: str
    content: str
    change_note: Optional[str] = None


class FileVersionBatch(BaseModel):
    files: List[FileVersionUpdate]


class OwnerCreate(BaseModel):
    username: str


class ForkRequest(BaseModel):
    target_owner: str


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('interactive.html', {'request': request})

@app.post("/load")
async def load_parameters():
    print("Loading parameters...")
    load_params_module.load_parameters(Path(__file__).parent / 'Parameters')
    return {"status": "ok"}

# Health check
@app.get("/health")
async def health_check():
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        conn.close()
        return {"status": "healthy"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# Owners
@app.get("/owners", response_model=List[Owner])
async def list_owners():
    """List all owners in the registry."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, username FROM owners ORDER BY username")
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/owners/{username}", response_model=Owner)
async def get_owner(username: str):
    """Get owner by username."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username FROM owners WHERE username = %s",
                (username,)
            )
            owner = cur.fetchone()
            if not owner:
                raise HTTPException(status_code=404, detail=f"Owner '{username}' not found")
            return owner
    finally:
        conn.close()


@app.post("/owners", response_model=Owner)
async def create_owner(body: OwnerCreate):
    """Create a new owner."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO owners (username) VALUES (%s) RETURNING id, username",
                (body.username,)
            )
            owner = cur.fetchone()
            conn.commit()
            return owner
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=409, detail=f"Owner '{body.username}' already exists")
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Parameters
@app.get("/parameters", response_model=List[ParameterSummary])
async def list_parameters(owner: Optional[str] = Query(None, description="Filter by owner")):
    """List all parameters, optionally filtered by owner."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            if owner:
                cur.execute("""
                    SELECT
                        p.id,
                        o.username as owner,
                        p.name,
                        p.description,
                        COALESCE(
                            ARRAY_AGG(pv.version ORDER BY pv.version)
                            FILTER (WHERE pv.is_dev = FALSE AND pv.version IS NOT NULL),
                            ARRAY[]::INTEGER[]
                        ) as versions,
                        BOOL_OR(pv.is_dev) as has_dev
                    FROM parameters p
                    JOIN owners o ON o.id = p.owner_id
                    LEFT JOIN parameter_versions pv ON pv.parameter_id = p.id
                    WHERE o.username = %s
                    GROUP BY p.id, o.username, p.name, p.description
                    ORDER BY p.name
                """, (owner,))
            else:
                cur.execute("""
                    SELECT
                        p.id,
                        o.username as owner,
                        p.name,
                        p.description,
                        COALESCE(
                            ARRAY_AGG(pv.version ORDER BY pv.version)
                            FILTER (WHERE pv.is_dev = FALSE AND pv.version IS NOT NULL),
                            ARRAY[]::INTEGER[]
                        ) as versions,
                        BOOL_OR(pv.is_dev) as has_dev
                    FROM parameters p
                    JOIN owners o ON o.id = p.owner_id
                    LEFT JOIN parameter_versions pv ON pv.parameter_id = p.id
                    GROUP BY p.id, o.username, p.name, p.description
                    ORDER BY o.username, p.name
                """)
            return cur.fetchall()
    finally:
        conn.close()


@app.get("/parameters/{owner}/{name}")
async def get_parameter(owner: str, name: str):
    """Get detailed information about a parameter."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Get parameter info
            cur.execute("""
                SELECT p.id, o.username as owner, p.name, p.description
                FROM parameters p
                JOIN owners o ON o.id = p.owner_id
                WHERE o.username = %s AND p.name = %s
            """, (owner, name))
            param = cur.fetchone()

            if not param:
                raise HTTPException(status_code=404, detail=f"Parameter '{owner}/{name}' not found")

            # Get versions
            cur.execute("""
                SELECT pv.id, pv.version, pv.is_dev
                FROM parameter_versions pv
                WHERE pv.parameter_id = %s
                ORDER BY pv.is_dev, pv.version
            """, (param['id'],))
            versions = cur.fetchall()

            # Get file mappings for each version
            versions_with_files = []
            for v in versions:
                cur.execute("""
                    SELECT ft.name as file_type, pvf.file_version
                    FROM parameter_version_files pvf
                    JOIN file_types ft ON ft.id = pvf.file_type_id
                    WHERE pvf.parameter_version_id = %s
                """, (v['id'],))
                files = {row['file_type']: row['file_version'] for row in cur.fetchall()}
                versions_with_files.append({
                    'version': v['version'],
                    'is_dev': v['is_dev'],
                    'file_mappings': files
                })

            return {
                **param,
                'versions': versions_with_files
            }
    finally:
        conn.close()


# File Versioning
@app.post("/parameters/{owner}/{name}/file-versions")
async def create_file_versions(owner: str, name: str, body: FileVersionBatch):
    """
    Create new file versions for a parameter. Updates the dev mapping.
    Accepts one or more file types in a single request.

    Body example:
        { "files": [
            { "file_type": "js", "content": "...", "change_note": "rewrote click handler" },
            { "file_type": "py", "content": "..." }
        ]}
    """
    if not body.files:
        raise HTTPException(status_code=400, detail="No files provided")

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Resolve parameter
            cur.execute("""
                SELECT p.id FROM parameters p
                JOIN owners o ON o.id = p.owner_id
                WHERE o.username = %s AND p.name = %s
            """, (owner, name))
            param = cur.fetchone()
            if not param:
                raise HTTPException(status_code=404, detail=f"Parameter '{owner}/{name}' not found")
            parameter_id = param['id']

            # Ensure a dev parameter_version exists; create one if not
            cur.execute("""
                SELECT id FROM parameter_versions
                WHERE parameter_id = %s AND is_dev = TRUE
            """, (parameter_id,))
            dev_version = cur.fetchone()
            if not dev_version:
                cur.execute("""
                    INSERT INTO parameter_versions (parameter_id, is_dev)
                    VALUES (%s, TRUE)
                    RETURNING id
                """, (parameter_id,))
                dev_version = cur.fetchone()
            dev_version_id = dev_version['id']

            created = []
            for file in body.files:
                # Resolve file type
                cur.execute("SELECT id FROM file_types WHERE name = %s", (file.file_type,))
                ft = cur.fetchone()
                if not ft:
                    raise HTTPException(status_code=400, detail=f"Unknown file type: '{file.file_type}'")
                file_type_id = ft['id']

                # Get the current highest version and its path for this (parameter, file_type)
                cur.execute("""
                    SELECT version, path FROM files
                    WHERE parameter_id = %s AND file_type_id = %s
                    ORDER BY version DESC LIMIT 1
                """, (parameter_id, file_type_id))
                current = cur.fetchone()

                if current:
                    new_version = current['version'] + 1
                    path = current['path']
                else:
                    new_version = 1
                    path = file.file_type

                # Insert the new file version
                cur.execute("""
                    INSERT INTO files (parameter_id, file_type_id, version, path, content, change_note)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (parameter_id, file_type_id, new_version, path, file.content, file.change_note))

                # Point the dev mapping at the new version (insert or update)
                cur.execute("""
                    INSERT INTO parameter_version_files (parameter_version_id, file_type_id, file_version)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (parameter_version_id, file_type_id)
                    DO UPDATE SET file_version = EXCLUDED.file_version
                """, (dev_version_id, file_type_id, new_version))

                created.append({
                    "file_type": file.file_type,
                    "new_version": new_version,
                    "path": path,
                    "change_note": file.change_note
                })

            conn.commit()

            log_replay("POST", f"/parameters/{owner}/{name}/file-versions", body=body.model_dump())

            return {
                "parameter": f"{owner}/{name}",
                "created": created
            }
    except HTTPException:
        raise
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Publish
@app.post("/parameters/{owner}/{name}/publish")
async def publish_version(owner: str, name: str):
    """
    Publish the current dev state as the next stable version.
    Snapshots the merged dev+latest file map and freezes dependencies.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT p.id FROM parameters p
                JOIN owners o ON o.id = p.owner_id
                WHERE o.username = %s AND p.name = %s
            """, (owner, name))
            param = cur.fetchone()
            if not param:
                raise HTTPException(status_code=404, detail=f"Parameter '{owner}/{name}' not found")

            cur.execute("SELECT publish_parameter(%s) AS new_version", (param['id'],))
            new_version = cur.fetchone()['new_version']

            conn.commit()

            log_replay("POST", f"/parameters/{owner}/{name}/publish")

            return {
                "parameter": f"{owner}/{name}",
                "published_version": new_version
            }
    except HTTPException:
        raise
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Fork
@app.post("/parameters/{owner}/{name}/fork")
async def fork_parameter(owner: str, name: str, body: ForkRequest):
    """
    Fork a parameter to a different owner.
    Copies the latest state (dev if available, otherwise latest stable)
    as v1 in the target owner's namespace.
    """
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Resolve source parameter
            cur.execute("""
                SELECT p.id, p.description FROM parameters p
                JOIN owners o ON o.id = p.owner_id
                WHERE o.username = %s AND p.name = %s
            """, (owner, name))
            source = cur.fetchone()
            if not source:
                raise HTTPException(status_code=404, detail=f"Parameter '{owner}/{name}' not found")
            source_param_id = source['id']

            # Resolve target owner
            cur.execute("SELECT id FROM owners WHERE username = %s", (body.target_owner,))
            target_owner_row = cur.fetchone()
            if not target_owner_row:
                raise HTTPException(status_code=404, detail=f"Owner '{body.target_owner}' not found")
            target_owner_id = target_owner_row['id']

            # Check target parameter doesn't already exist
            cur.execute("""
                SELECT id FROM parameters WHERE owner_id = %s AND name = %s
            """, (target_owner_id, name))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail=f"Parameter '{body.target_owner}/{name}' already exists")

            # Get the latest file state: prefer dev, fall back to latest stable
            cur.execute("""
                SELECT pvf.file_type_id, pvf.file_version
                FROM parameter_version_files pvf
                JOIN parameter_versions pv ON pv.id = pvf.parameter_version_id
                WHERE pv.parameter_id = %s AND pv.is_dev = TRUE
            """, (source_param_id,))
            file_mappings = cur.fetchall()

            if not file_mappings:
                cur.execute("""
                    SELECT pvf.file_type_id, pvf.file_version
                    FROM parameter_version_files pvf
                    JOIN parameter_versions pv ON pv.id = pvf.parameter_version_id
                    WHERE pv.parameter_id = %s AND pv.is_dev = FALSE
                    AND pv.version = (
                        SELECT MAX(version) FROM parameter_versions
                        WHERE parameter_id = %s AND is_dev = FALSE
                    )
                """, (source_param_id, source_param_id))
                file_mappings = cur.fetchall()

            if not file_mappings:
                raise HTTPException(status_code=400, detail="Source parameter has no files to fork")

            # Create new parameter
            cur.execute("""
                INSERT INTO parameters (owner_id, name, description)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (target_owner_id, name, source['description']))
            new_param_id = cur.fetchone()['id']

            # Copy files as version 1 and build mapping list
            copied_files = []
            for fm in file_mappings:
                cur.execute("""
                    SELECT path, content FROM files
                    WHERE parameter_id = %s AND file_type_id = %s AND version = %s
                """, (source_param_id, fm['file_type_id'], fm['file_version']))
                file_row = cur.fetchone()

                cur.execute("""
                    INSERT INTO files (parameter_id, file_type_id, version, path, content)
                    VALUES (%s, %s, 1, %s, %s)
                """, (new_param_id, fm['file_type_id'], file_row['path'], file_row['content']))

                copied_files.append(fm['file_type_id'])

            # Create stable v1
            cur.execute("""
                INSERT INTO parameter_versions (parameter_id, version, is_dev)
                VALUES (%s, 1, FALSE)
                RETURNING id
            """, (new_param_id,))
            v1_id = cur.fetchone()['id']

            # Link v1 to the copied files (all at version 1)
            for file_type_id in copied_files:
                cur.execute("""
                    INSERT INTO parameter_version_files (parameter_version_id, file_type_id, file_version)
                    VALUES (%s, %s, 1)
                """, (v1_id, file_type_id))

            conn.commit()

            log_replay("POST", f"/parameters/{owner}/{name}/fork", body=body.model_dump())

            return {
                "source": f"{owner}/{name}",
                "forked_to": f"{body.target_owner}/{name}",
                "files_copied": len(copied_files)
            }
    except HTTPException:
        raise
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Replay
async def replay_entries(entries: list[dict] | None = None) -> list[dict]:
    """
    Replay recorded requests by calling the original handlers directly.
    Pass a specific list of entries, or None to replay everything in replay.json.
    Returns a result dict per entry with status 'ok' or 'error'.
    """
    global _replaying

    if entries is None:
        try:
            raw = REPLAY_PATH.read_text()
            entries = json.loads(raw) if raw.strip() else []
        except (FileNotFoundError, json.JSONDecodeError):
            entries = []

    _replaying = True
    results = []
    try:
        for entry in entries:
            path = entry["path"]
            try:
                # /parameters/{owner}/{name}/file-versions
                m = re.match(r'^/parameters/([^/]+)/([^/]+)/file-versions$', path)
                if m:
                    owner, name = m.groups()
                    body = FileVersionBatch(**entry["body"])
                    result = await create_file_versions(owner, name, body)
                    results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "ok", "result": result})
                    continue

                # /parameters/{owner}/{name}/publish
                m = re.match(r'^/parameters/([^/]+)/([^/]+)/publish$', path)
                if m:
                    owner, name = m.groups()
                    result = await publish_version(owner, name)
                    results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "ok", "result": result})
                    continue

                # /parameters/{owner}/{name}/fork
                m = re.match(r'^/parameters/([^/]+)/([^/]+)/fork$', path)
                if m:
                    owner, name = m.groups()
                    body = ForkRequest(**entry["body"])
                    result = await fork_parameter(owner, name, body)
                    results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "ok", "result": result})
                    continue

                results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "error", "error": f"Unrecognized path: {path}"})

            except HTTPException as e:
                results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "error", "error": f"{e.status_code}: {e.detail}"})
            except Exception as e:
                results.append({"path": path, "timestamp": entry.get("timestamp"), "status": "error", "error": str(e)})
    finally:
        _replaying = False

    return results


@app.post("/replay")
async def replay():
    """Replay all recorded requests from replay.json in order."""
    results = await replay_entries()
    succeeded = sum(1 for r in results if r["status"] == "ok")
    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": results
    }


# Package Resolution
def parse_package_query(query: str) -> tuple:
    """
    Parse package notation: owner/parameter:selector[filetypes]
    Returns (owner, parameter, selector, filetypes)
    """
    # Pattern: owner/parameter:selector[filetypes]
    pattern = r'^([^/]+)/([^:]+)(?::([^[]+))?(?:\[([^\]]+)\])?$'
    match = re.match(pattern, query)

    if not match:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid package notation: {query}. Expected: owner/parameter:selector[filetypes]"
        )

    owner, parameter, selector, filetypes = match.groups()
    selector = selector or 'latest'
    filetypes = filetypes.split(',') if filetypes and filetypes != '*' else None

    return owner, parameter, selector, filetypes


@app.get("/resolve/{query:path}")
async def resolve_package(query: str):
    """
    Resolve a package query and return the files.

    Query format: owner/parameter:selector[filetypes]

    Examples:
    - evezor/Floe:latest
    - evezor/Floe:1
    - evezor/Floe:dev
    - evezor/Floe:latest[js,py]
    """
    owner, parameter, selector, filetypes = parse_package_query(query)

    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Use the resolve_package function from the database
            if filetypes:
                cur.execute(
                    "SELECT * FROM resolve_package(%s, %s, %s, %s)",
                    (owner, parameter, selector, filetypes)
                )
            else:
                cur.execute(
                    "SELECT * FROM resolve_package(%s, %s, %s)",
                    (owner, parameter, selector)
                )

            rows = cur.fetchall()

            if not rows:
                raise HTTPException(
                    status_code=404,
                    detail=f"No files found for {owner}/{parameter}:{selector}"
                )

            # Get version info
            cur.execute("""
                SELECT pv.version, pv.is_dev
                FROM parameter_versions pv
                JOIN parameters p ON p.id = pv.parameter_id
                JOIN owners o ON o.id = p.owner_id
                WHERE o.username = %s AND p.name = %s
                AND (
                    (pv.is_dev = TRUE AND %s = 'dev')
                    OR (pv.is_dev = FALSE AND %s = 'latest' AND pv.version = (
                        SELECT MAX(version) FROM parameter_versions
                        WHERE parameter_id = p.id AND is_dev = FALSE
                    ))
                    OR (pv.is_dev = FALSE AND pv.version = %s::INTEGER)
                )
            """, (owner, parameter, selector, selector,
                  selector if selector not in ('dev', 'latest') else '0'))
            version_info = cur.fetchone()

            return {
                'owner': owner,
                'parameter': parameter,
                'selector': selector,
                'version': version_info['version'] if version_info else None,
                'is_dev': version_info['is_dev'] if version_info else False,
                'files': [
                    {
                        'file_type': row['file_type'],
                        'file_version': row['file_version'],
                        'path': row['path'],
                        'content': row['content']
                    }
                    for row in rows
                ]
            }
    except psycopg2.Error as e:
        if 'not found' in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# Dependencies
@app.get("/dependencies/{owner}/{name}")
async def get_dependencies(
    owner: str,
    name: str,
    selector: str = Query('latest', description="Version selector: latest, dev, or integer")
):
    """Get the dependency tree for a parameter version."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM resolve_dependency_tree(%s, %s, %s)",
                (owner, name, selector)
            )
            rows = cur.fetchall()

            return {
                'root': f"{owner}/{name}:{selector}",
                'dependencies': [
                    {
                        'depth': row['depth'],
                        'owner': row['owner'],
                        'parameter': row['parameter'],
                        'version': row['version'],
                        'is_dev': row['is_dev']
                    }
                    for row in rows
                ]
            }
    except psycopg2.Error as e:
        if 'not found' in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# File Types
@app.get("/file-types")
async def list_file_types():
    """List all registered file types."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM file_types ORDER BY name")
            return cur.fetchall()
    finally:
        conn.close()


# Stats
@app.get("/stats")
async def get_stats():
    """Get registry statistics."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            stats = {}

            cur.execute("SELECT COUNT(*) as count FROM owners")
            stats['owners'] = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM parameters")
            stats['parameters'] = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM parameter_versions WHERE is_dev = FALSE")
            stats['stable_versions'] = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM parameter_versions WHERE is_dev = TRUE")
            stats['dev_versions'] = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM files")
            stats['files'] = cur.fetchone()['count']

            cur.execute("SELECT COUNT(*) as count FROM parameter_version_dependencies")
            stats['dependencies'] = cur.fetchone()['count']

            return stats
    finally:
        conn.close()


