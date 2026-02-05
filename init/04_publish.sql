BEGIN;

-- =========================================================
-- Publish: snapshot dev → next stable version
-- =========================================================
-- Merges the dev file map over latest (same logic the resolver
-- uses when you query :dev), freezes that into a new stable
-- parameter_version, and copies + freezes any dependencies.
-- Returns the new version number.
-- =========================================================
CREATE OR REPLACE FUNCTION publish_parameter(
    p_parameter_id INTEGER
)
RETURNS INTEGER AS $$
DECLARE
    dev_pvid    INTEGER;
    latest_pvid INTEGER;
    new_version INTEGER;
    new_pvid    INTEGER;
BEGIN
    -- 1. A dev version must exist
    SELECT id INTO dev_pvid
    FROM parameter_versions
    WHERE parameter_id = p_parameter_id AND is_dev = TRUE;

    IF dev_pvid IS NULL THEN
        RAISE EXCEPTION 'No dev version exists for parameter %', p_parameter_id;
    END IF;

    -- 2. Next stable version number
    SELECT COALESCE(MAX(version), 0) + 1 INTO new_version
    FROM parameter_versions
    WHERE parameter_id = p_parameter_id AND is_dev = FALSE;

    -- 3. Current latest stable (NULL if this will be v1)
    SELECT id INTO latest_pvid
    FROM parameter_versions
    WHERE parameter_id = p_parameter_id AND is_dev = FALSE
    ORDER BY version DESC
    LIMIT 1;

    -- 4. Create the new stable version row
    INSERT INTO parameter_versions (parameter_id, version, is_dev)
    VALUES (p_parameter_id, new_version, FALSE)
    RETURNING id INTO new_pvid;

    -- 5. Snapshot merged file map: dev wins, latest fills gaps
    INSERT INTO parameter_version_files (parameter_version_id, file_type_id, file_version)
    SELECT new_pvid, file_type_id, file_version FROM (
        SELECT file_type_id, file_version
        FROM parameter_version_files
        WHERE parameter_version_id = dev_pvid

        UNION ALL

        SELECT file_type_id, file_version
        FROM parameter_version_files
        WHERE parameter_version_id = latest_pvid
          AND latest_pvid IS NOT NULL
          AND file_type_id NOT IN (
              SELECT file_type_id FROM parameter_version_files
              WHERE parameter_version_id = dev_pvid
          )
    ) merged;

    -- 6. Freeze dependencies from dev: resolve any :latest refs
    --    to the actual version number at this moment in time
    INSERT INTO parameter_version_dependencies
        (parameter_version_id, depends_on_parameter_id,
         depends_on_version, depends_on_is_dev, original_selector)
    SELECT
        new_pvid,
        d.depends_on_parameter_id,
        CASE
            WHEN d.depends_on_is_dev THEN NULL
            ELSE (SELECT MAX(pv.version)
                  FROM parameter_versions pv
                  WHERE pv.parameter_id = d.depends_on_parameter_id
                    AND pv.is_dev = FALSE)
        END,
        d.depends_on_is_dev,
        d.original_selector
    FROM parameter_version_dependencies d
    WHERE d.parameter_version_id = dev_pvid;

    RETURN new_version;
END;
$$ LANGUAGE plpgsql;

COMMIT;
