BEGIN;

-- ===============================
-- 1. Resolve parameter ID
-- ===============================
CREATE OR REPLACE FUNCTION resolve_parameter(
    p_owner TEXT,
    p_parameter TEXT
)
RETURNS INTEGER AS $$
DECLARE
    pid INTEGER;
BEGIN
    SELECT p.id
    INTO pid
    FROM parameters p
    JOIN owners o ON o.id = p.owner_id
    WHERE o.username = p_owner
      AND p.name = p_parameter;

    IF pid IS NULL THEN
        RAISE EXCEPTION 'Parameter %.% not found', p_owner, p_parameter;
    END IF;

    RETURN pid;
END;
$$ LANGUAGE plpgsql STABLE;


-- ===============================
-- 2. Resolve parameter version ID
-- selector = 'dev' | 'latest' | integer
-- ===============================
CREATE OR REPLACE FUNCTION resolve_parameter_version(
    p_parameter_id INTEGER,
    p_selector TEXT
)
RETURNS INTEGER AS $$
DECLARE
    pvid INTEGER;
BEGIN
    IF p_selector = 'dev' THEN
        SELECT id INTO pvid
        FROM parameter_versions
        WHERE parameter_id = p_parameter_id
          AND is_dev = TRUE;

    ELSIF p_selector = 'latest' THEN
        SELECT id INTO pvid
        FROM parameter_versions
        WHERE parameter_id = p_parameter_id
          AND is_dev = FALSE
        ORDER BY version DESC
        LIMIT 1;

    ELSE
        SELECT id INTO pvid
        FROM parameter_versions
        WHERE parameter_id = p_parameter_id
          AND is_dev = FALSE
          AND version = p_selector::INTEGER;
    END IF;

    IF pvid IS NULL THEN
        RAISE EXCEPTION 'Version % not found for parameter %',
            p_selector, p_parameter_id;
    END IF;

    RETURN pvid;
END;
$$ LANGUAGE plpgsql STABLE;


-- ===============================
-- 3. Resolve file mappings
-- ===============================
CREATE OR REPLACE FUNCTION resolve_version_file_map(
    p_parameter_version_id INTEGER
)
RETURNS TABLE (
    file_type TEXT,
    file_type_id INTEGER,
    file_version INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ft.name,
        ft.id,
        pvf.file_version
    FROM parameter_version_files pvf
    JOIN file_types ft ON ft.id = pvf.file_type_id
    WHERE pvf.parameter_version_id = p_parameter_version_id;
END;
$$ LANGUAGE plpgsql STABLE;


-- ===============================
-- 4. Resolve actual files
-- Optional file type filter
-- ===============================
CREATE OR REPLACE FUNCTION resolve_files(
    p_parameter_id INTEGER,
    p_parameter_version_id INTEGER,
    p_file_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    file_type TEXT,
    file_version INTEGER,
    path TEXT,
    content TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ft.name,
        pvf.file_version,
        f.path,
        f.content
    FROM parameter_version_files pvf
    JOIN file_types ft ON ft.id = pvf.file_type_id
    JOIN files f ON
        f.parameter_id = p_parameter_id
        AND f.file_type_id = ft.id
        AND f.version = pvf.file_version
    WHERE pvf.parameter_version_id = p_parameter_version_id
      AND (
          p_file_types IS NULL
          OR ft.name = ANY(p_file_types)
      );
END;
$$ LANGUAGE plpgsql STABLE;


-- ===============================
-- 5. Full resolver (single call)
-- ===============================
CREATE OR REPLACE FUNCTION resolve_package(
    p_owner TEXT,
    p_parameter TEXT,
    p_selector TEXT,
    p_file_types TEXT[] DEFAULT NULL
)
RETURNS TABLE (
    owner TEXT,
    parameter TEXT,
    selector TEXT,
    file_type TEXT,
    file_version INTEGER,
    path TEXT,
    content TEXT
) AS $$
DECLARE
    pid INTEGER;
    pvid INTEGER;
BEGIN
    pid := resolve_parameter(p_owner, p_parameter);
    pvid := resolve_parameter_version(pid, p_selector);

    RETURN QUERY
    SELECT
        p_owner,
        p_parameter,
        p_selector,
        r.file_type,
        r.file_version,
        r.path,
        r.content
    FROM resolve_files(pid, pvid, p_file_types) r;
END;
$$ LANGUAGE plpgsql STABLE;


COMMIT;
-- =========================================================