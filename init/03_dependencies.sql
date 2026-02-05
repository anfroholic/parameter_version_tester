BEGIN;

-- =========================================================
-- Dependencies between Parameter versions
-- =========================================================

-- Stores the dependency declarations for each parameter version
-- When a version is published, :latest dependencies are resolved and frozen
CREATE TABLE parameter_version_dependencies (
    id SERIAL PRIMARY KEY,
    parameter_version_id INTEGER NOT NULL
        REFERENCES parameter_versions(id) ON DELETE CASCADE,

    -- The dependency target (frozen at publish time)
    depends_on_parameter_id INTEGER NOT NULL
        REFERENCES parameters(id) ON DELETE RESTRICT,
    depends_on_version INTEGER,  -- NULL means :dev was specified
    depends_on_is_dev BOOLEAN NOT NULL DEFAULT FALSE,

    -- Original selector for reference (e.g., 'latest', 'dev', '3')
    original_selector TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate dependencies
    UNIQUE (parameter_version_id, depends_on_parameter_id),

    -- Ensure consistency: dev has NULL version, stable has version
    CHECK (
        (depends_on_is_dev = TRUE AND depends_on_version IS NULL) OR
        (depends_on_is_dev = FALSE AND depends_on_version IS NOT NULL)
    )
);

CREATE INDEX idx_pvd_version
    ON parameter_version_dependencies(parameter_version_id);

CREATE INDEX idx_pvd_depends_on
    ON parameter_version_dependencies(depends_on_parameter_id);


-- =========================================================
-- Resolve dependencies for a parameter version
-- =========================================================
CREATE OR REPLACE FUNCTION resolve_dependencies(
    p_parameter_version_id INTEGER
)
RETURNS TABLE (
    dependency_owner TEXT,
    dependency_parameter TEXT,
    dependency_version INTEGER,
    dependency_is_dev BOOLEAN,
    original_selector TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        o.username,
        p.name,
        pvd.depends_on_version,
        pvd.depends_on_is_dev,
        pvd.original_selector
    FROM parameter_version_dependencies pvd
    JOIN parameters p ON p.id = pvd.depends_on_parameter_id
    JOIN owners o ON o.id = p.owner_id
    WHERE pvd.parameter_version_id = p_parameter_version_id;
END;
$$ LANGUAGE plpgsql STABLE;


-- =========================================================
-- Recursive dependency resolver (full tree)
-- =========================================================
CREATE OR REPLACE FUNCTION resolve_dependency_tree(
    p_owner TEXT,
    p_parameter TEXT,
    p_selector TEXT
)
RETURNS TABLE (
    depth INTEGER,
    owner TEXT,
    parameter TEXT,
    version INTEGER,
    is_dev BOOLEAN
) AS $$
DECLARE
    pid INTEGER;
    pvid INTEGER;
BEGIN
    pid := resolve_parameter(p_owner, p_parameter);
    pvid := resolve_parameter_version(pid, p_selector);

    RETURN QUERY
    WITH RECURSIVE dep_tree AS (
        -- Base case: the root parameter
        SELECT
            0 AS depth,
            p_owner AS owner,
            p_parameter AS parameter,
            pv.version,
            pv.is_dev,
            pvid AS param_version_id
        FROM parameter_versions pv
        WHERE pv.id = pvid

        UNION ALL

        -- Recursive case: dependencies
        SELECT
            dt.depth + 1,
            o.username,
            p.name,
            pvd.depends_on_version,
            pvd.depends_on_is_dev,
            CASE
                WHEN pvd.depends_on_is_dev THEN
                    (SELECT pv2.id FROM parameter_versions pv2
                     WHERE pv2.parameter_id = pvd.depends_on_parameter_id AND pv2.is_dev = TRUE)
                ELSE
                    (SELECT pv2.id FROM parameter_versions pv2
                     WHERE pv2.parameter_id = pvd.depends_on_parameter_id
                       AND pv2.version = pvd.depends_on_version AND pv2.is_dev = FALSE)
            END
        FROM dep_tree dt
        JOIN parameter_version_dependencies pvd
            ON pvd.parameter_version_id = dt.param_version_id
        JOIN parameters p ON p.id = pvd.depends_on_parameter_id
        JOIN owners o ON o.id = p.owner_id
        WHERE dt.depth < 50  -- Prevent infinite recursion
    )
    SELECT DISTINCT
        dep_tree.depth,
        dep_tree.owner,
        dep_tree.parameter,
        dep_tree.version,
        dep_tree.is_dev
    FROM dep_tree
    ORDER BY dep_tree.depth, dep_tree.owner, dep_tree.parameter;
END;
$$ LANGUAGE plpgsql STABLE;


-- =========================================================
-- Prevent cyclic dependencies
-- =========================================================
CREATE OR REPLACE FUNCTION check_cyclic_dependency()
RETURNS TRIGGER AS $$
DECLARE
    cycle_exists BOOLEAN;
BEGIN
    -- Check if adding this dependency would create a cycle
    WITH RECURSIVE dep_chain AS (
        -- Start from the dependency target
        SELECT
            NEW.depends_on_parameter_id AS param_id,
            ARRAY[NEW.parameter_version_id] AS visited

        UNION ALL

        SELECT
            pvd.depends_on_parameter_id,
            dc.visited || pv.id
        FROM dep_chain dc
        JOIN parameter_versions pv ON pv.parameter_id = dc.param_id
        JOIN parameter_version_dependencies pvd ON pvd.parameter_version_id = pv.id
        WHERE NOT (pv.id = ANY(dc.visited))
          AND array_length(dc.visited, 1) < 50
    )
    SELECT EXISTS (
        SELECT 1
        FROM dep_chain dc
        JOIN parameter_versions pv ON pv.parameter_id = dc.param_id
        WHERE pv.id = NEW.parameter_version_id
    ) INTO cycle_exists;

    IF cycle_exists THEN
        RAISE EXCEPTION 'Cyclic dependency detected';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_check_cyclic_dependency
BEFORE INSERT ON parameter_version_dependencies
FOR EACH ROW
EXECUTE FUNCTION check_cyclic_dependency();


COMMIT;
