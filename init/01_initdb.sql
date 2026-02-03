BEGIN;

-- =========================================================
-- 0. Safety / hygiene
-- =========================================================
SET client_min_messages TO WARNING;
SET search_path TO public;

-- =========================================================
-- 1. Owners (namespaces)
-- =========================================================
CREATE TABLE owners (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- =========================================================
-- 2. Parameters
-- =========================================================
CREATE TABLE parameters (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (owner_id, name)
);

CREATE INDEX idx_parameters_owner
    ON parameters(owner_id);

-- =========================================================
-- 3. File types (js / py / md / future)
-- =========================================================
CREATE TABLE file_types (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

-- Seed common types
INSERT INTO file_types (name) VALUES
    ('js'),
    ('py'),
    ('md'),
    ('json'),
    ('txt'),
    ('html'),
    ('css'),
    ('csv'),
    ('png'),
    ('ico'),
    ('dependencies')
ON CONFLICT DO NOTHING;

-- =========================================================
-- 4. Files (independently versioned per type)
-- =========================================================
CREATE TABLE files (
    id SERIAL PRIMARY KEY,
    parameter_id INTEGER NOT NULL REFERENCES parameters(id) ON DELETE CASCADE,
    file_type_id INTEGER NOT NULL REFERENCES file_types(id),
    version INTEGER NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (parameter_id, file_type_id, version)
);

CREATE INDEX idx_files_lookup
    ON files(parameter_id, file_type_id, version);

-- =========================================================
-- 5. Parameter versions (major versions + dev)
-- =========================================================
CREATE TABLE parameter_versions (
    id SERIAL PRIMARY KEY,
    parameter_id INTEGER NOT NULL REFERENCES parameters(id) ON DELETE CASCADE,

    -- NULL for dev, integer for stable
    version INTEGER,
    is_dev BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CHECK (
        (is_dev = TRUE  AND version IS NULL) OR
        (is_dev = FALSE AND version IS NOT NULL)
    )
);

-- One dev version per parameter
CREATE UNIQUE INDEX idx_unique_dev_version
    ON parameter_versions(parameter_id)
    WHERE is_dev = TRUE;

-- Unique stable versions per parameter
CREATE UNIQUE INDEX idx_unique_stable_versions
    ON parameter_versions(parameter_id, version)
    WHERE is_dev = FALSE;


-- =========================================================
-- 6. Mapping: parameter version → file versions
-- =========================================================
CREATE TABLE parameter_version_files (
    id SERIAL PRIMARY KEY,
    parameter_version_id INTEGER NOT NULL
        REFERENCES parameter_versions(id) ON DELETE CASCADE,
    file_type_id INTEGER NOT NULL REFERENCES file_types(id),
    file_version INTEGER NOT NULL,

    UNIQUE (parameter_version_id, file_type_id)
);

CREATE INDEX idx_pvf_version
    ON parameter_version_files(parameter_version_id);

-- =========================================================
-- 7. Optional: Guardrails (recommended)
-- =========================================================

-- Prevent deleting files that are referenced by stable versions
CREATE OR REPLACE FUNCTION prevent_file_delete_if_used()
RETURNS TRIGGER AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM parameter_version_files pvf
        JOIN parameter_versions pv ON pv.id = pvf.parameter_version_id
        WHERE pv.is_dev = FALSE
          AND pvf.file_version = OLD.version
          AND pvf.file_type_id = OLD.file_type_id
          AND pv.parameter_id = OLD.parameter_id
    ) THEN
        RAISE EXCEPTION
            'Cannot delete file %.v% (in use by stable parameter version)',
            OLD.path, OLD.version;
    END IF;

    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_prevent_file_delete
BEFORE DELETE ON files
FOR EACH ROW
EXECUTE FUNCTION prevent_file_delete_if_used();

-- =========================================================
-- 8. Recommended extensions (safe, optional)
-- =========================================================
-- Uncomment if you want them
-- CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- future hashing
-- CREATE EXTENSION IF NOT EXISTS citext;     -- case-insensitive names

COMMIT;
