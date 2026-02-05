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
from pathlib import Path
from typing import List, Optional
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
    display_name: Optional[str]
    email: Optional[str]


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


@app.get('/', response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse('interactive.html', {'request': request})

@app.get("/load", response_class=HTMLResponse)
async def load_parameters(request: Request):
    print("Loading parameters...")
    load_params_module.load_parameters(Path(__file__).parent / 'Parameters')
    return templates.TemplateResponse('interactive.html', {'request': request})

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
            cur.execute("SELECT id, username, display_name, email FROM owners ORDER BY username")
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
                "SELECT id, username, display_name, email FROM owners WHERE username = %s",
                (username,)
            )
            owner = cur.fetchone()
            if not owner:
                raise HTTPException(status_code=404, detail=f"Owner '{username}' not found")
            return owner
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


