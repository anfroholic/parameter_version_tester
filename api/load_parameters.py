#!/usr/bin/env python3
"""
Parameter Loader - Populates the database from the Parameters folder.

This script reads the Parameters folder structure and populates the PostgreSQL
database with owners, parameters, files, and versions.

Usage:
    python load_parameters.py [--parameters-dir PATH] [--owner OWNER]
"""

import os
import sys
import base64
import argparse
import psycopg2
from pathlib import Path
from typing import Dict, List, Tuple

# Load .env file if present
from dotenv import load_dotenv
load_dotenv()


# File type mappings
FILE_TYPE_MAP = {
    '.js': 'js',
    '.py': 'py',
    '.md': 'md',
    '.json': 'json',
    '.txt': 'txt',
    '.html': 'html',
}

# Binary file types (stored as base64)
BINARY_TYPES = {'.png', '.ico'}

# Special files that are not stored as regular file types
SPECIAL_FILES = {'dependencies.txt'}


def get_db_connection():
    """Create database connection using environment variables."""
    host = os.environ.get('POSTGRES_HOST', 'db')
    port = os.environ.get('POSTGRES_PORT', '5432')
    dbname = os.environ.get('POSTGRES_DB', 'mydb')
    user = os.environ.get('POSTGRES_USER', 'anfro')
    password = os.environ.get('POSTGRES_PASSWORD', 'password')

    print(f"Connecting to: host={host}, port={port}, dbname={dbname}, user={user}")

    return psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )


def ensure_owner(conn, username: str) -> int:
    """Ensure owner exists and return ID."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO owners (username) VALUES (%s) "
            "ON CONFLICT (username) DO UPDATE SET username = EXCLUDED.username "
            "RETURNING id",
            (username,)
        )
        return cur.fetchone()[0]


def ensure_file_type(conn, type_name: str) -> int:
    """Ensure file type exists and return ID."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO file_types (name) VALUES (%s) "
            "ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name "
            "RETURNING id",
            (type_name,)
        )
        return cur.fetchone()[0]


def get_file_types(conn) -> Dict[str, int]:
    """Get all file types as a dict of name -> id."""
    with conn.cursor() as cur:
        cur.execute("SELECT name, id FROM file_types")
        return {row[0]: row[1] for row in cur.fetchall()}


def create_parameter(conn, owner_id: int, name: str, description: str = None) -> int:
    """Create a parameter and return its ID."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO parameters (owner_id, name, description) VALUES (%s, %s, %s) "
            "ON CONFLICT (owner_id, name) DO UPDATE SET description = EXCLUDED.description "
            "RETURNING id",
            (owner_id, name, description)
        )
        return cur.fetchone()[0]


def create_file(conn, parameter_id: int, file_type_id: int, version: int, path: str, content: str) -> int:
    """Create a file entry and return its ID."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO files (parameter_id, file_type_id, version, path, content) "
            "VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (parameter_id, file_type_id, version) DO UPDATE "
            "SET path = EXCLUDED.path, content = EXCLUDED.content "
            "RETURNING id",
            (parameter_id, file_type_id, version, path, content)
        )
        return cur.fetchone()[0]


def create_parameter_version(conn, parameter_id: int, version: int = None, is_dev: bool = False) -> int:
    """Create a parameter version and return its ID."""
    with conn.cursor() as cur:
        if is_dev:
            # Check if dev version exists
            cur.execute(
                "SELECT id FROM parameter_versions WHERE parameter_id = %s AND is_dev = TRUE",
                (parameter_id,)
            )
            existing = cur.fetchone()
            if existing:
                return existing[0]

            cur.execute(
                "INSERT INTO parameter_versions (parameter_id, version, is_dev) "
                "VALUES (%s, NULL, TRUE) RETURNING id",
                (parameter_id,)
            )
        else:
            cur.execute(
                "INSERT INTO parameter_versions (parameter_id, version, is_dev) "
                "VALUES (%s, %s, FALSE) "
                "ON CONFLICT DO NOTHING "
                "RETURNING id",
                (parameter_id, version)
            )
            result = cur.fetchone()
            if result:
                return result[0]

            # If ON CONFLICT occurred, fetch existing
            cur.execute(
                "SELECT id FROM parameter_versions "
                "WHERE parameter_id = %s AND version = %s AND is_dev = FALSE",
                (parameter_id, version)
            )
        return cur.fetchone()[0]


def link_version_to_file(conn, parameter_version_id: int, file_type_id: int, file_version: int):
    """Link a parameter version to a file version."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO parameter_version_files (parameter_version_id, file_type_id, file_version) "
            "VALUES (%s, %s, %s) "
            "ON CONFLICT (parameter_version_id, file_type_id) DO UPDATE "
            "SET file_version = EXCLUDED.file_version",
            (parameter_version_id, file_type_id, file_version)
        )


def read_file_content(file_path: Path) -> str:
    """Read file content, encoding binary files as base64."""
    ext = file_path.suffix.lower()
    if ext in BINARY_TYPES:
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    else:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Fallback to binary
            with open(file_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')


def parse_dependencies(content: str) -> List[str]:
    """Parse dependencies.txt content into a list of dependency names."""
    deps = []
    for line in content.strip().split('\n'):
        line = line.strip()
        if line and not line.startswith('#'):
            deps.append(line)
    return deps


def collect_files(param_dir: Path) -> Dict[str, Tuple[str, str]]:
    """
    Collect files from a parameter directory (root level only, no subdirs).
    Returns dict of file_type -> (filename, content)
    Only one file per type is stored.
    """
    files_by_type: Dict[str, Tuple[str, str]] = {}

    # Only look at files in the root of the parameter directory (no subdirs)
    for file_path in param_dir.iterdir():
        if not file_path.is_file():
            continue

        filename = file_path.name

        # Skip special files
        if filename in SPECIAL_FILES:
            continue

        ext = file_path.suffix.lower()
        if ext in FILE_TYPE_MAP:
            file_type = FILE_TYPE_MAP[ext]
            content = read_file_content(file_path)
            files_by_type[file_type] = (filename, content)

    return files_by_type


def create_dependency(conn, parameter_version_id: int, depends_on_parameter_id: int,
                     depends_on_version: int, depends_on_is_dev: bool, original_selector: str):
    """Create a dependency link between parameter versions."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO parameter_version_dependencies
            (parameter_version_id, depends_on_parameter_id, depends_on_version,
             depends_on_is_dev, original_selector)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (parameter_version_id, depends_on_parameter_id) DO UPDATE
            SET depends_on_version = EXCLUDED.depends_on_version,
                depends_on_is_dev = EXCLUDED.depends_on_is_dev,
                original_selector = EXCLUDED.original_selector
            """,
            (parameter_version_id, depends_on_parameter_id, depends_on_version,
             depends_on_is_dev, original_selector)
        )


def load_parameters(parameters_dir: Path, default_owner: str = 'evezor'):
    """Load all parameters from the given directory."""
    conn = get_db_connection()
    conn.autocommit = False

    try:
        # Ensure owner exists
        owner_id = ensure_owner(conn, default_owner)
        print(f"Using owner '{default_owner}' (id={owner_id})")

        # Get file types
        file_types = get_file_types(conn)

        # Track created parameters for dependency resolution
        param_name_to_id: Dict[str, int] = {}
        param_name_to_version_id: Dict[str, int] = {}
        param_dependencies: Dict[str, List[str]] = {}

        # First pass: Create all parameters and files
        for param_dir in sorted(parameters_dir.iterdir()):
            if not param_dir.is_dir():
                continue

            param_name = param_dir.name
            print(f"\nProcessing parameter: {param_name}")

            # Create parameter
            parameter_id = create_parameter(conn, owner_id, param_name)
            param_name_to_id[param_name] = parameter_id

            # Collect files
            files_by_type = collect_files(param_dir)

            # Create parameter version 1
            version_id = create_parameter_version(conn, parameter_id, version=1, is_dev=False)
            param_name_to_version_id[param_name] = version_id

            # Create files and link them
            for file_type, (filename, content) in files_by_type.items():
                if file_type not in file_types:
                    file_type_id = ensure_file_type(conn, file_type)
                    file_types[file_type] = file_type_id
                else:
                    file_type_id = file_types[file_type]

                # Create the file entry
                create_file(conn, parameter_id, file_type_id, 1, filename, content)

                # Link version to file
                link_version_to_file(conn, version_id, file_type_id, 1)
                print(f"  - Added {file_type}: {filename}")

            # Read dependencies
            deps_file = param_dir / 'dependencies.txt'
            if deps_file.exists():
                deps_content = deps_file.read_text(encoding='utf-8')
                deps = parse_dependencies(deps_content)
                if deps:
                    param_dependencies[param_name] = deps
                    print(f"  - Dependencies: {deps}")

        # Second pass: Create dependency links
        print("\n\nCreating dependency links...")
        for param_name, deps in param_dependencies.items():
            version_id = param_name_to_version_id.get(param_name)
            if not version_id:
                continue

            for dep_name in deps:
                # Parse dependency notation (could be owner/param:selector)
                # For now, assume same owner and :latest selector
                dep_param_name = dep_name.split('/')[-1].split(':')[0]

                if dep_param_name in param_name_to_id:
                    dep_param_id = param_name_to_id[dep_param_name]
                    # Link as version 1 (since we imported everything as v1)
                    create_dependency(
                        conn, version_id, dep_param_id,
                        depends_on_version=1,
                        depends_on_is_dev=False,
                        original_selector='1'
                    )
                    print(f"  {param_name} -> {dep_param_name}")
                else:
                    print(f"  WARNING: {param_name} depends on unknown parameter: {dep_param_name}")

        conn.commit()
        print("\n\nDone! All parameters loaded successfully.")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Load parameters into the database')
    parser.add_argument(
        '--parameters-dir',
        type=Path,
        default=Path(__file__).parent / 'Parameters',
        help='Path to the Parameters directory'
    )
    parser.add_argument(
        '--owner',
        type=str,
        default='evezor',
        help='Default owner for all parameters'
    )

    args = parser.parse_args()

    if not args.parameters_dir.exists():
        print(f"Error: Parameters directory not found: {args.parameters_dir}")
        sys.exit(1)

    load_parameters(args.parameters_dir, args.owner)


if __name__ == '__main__':
    main()
