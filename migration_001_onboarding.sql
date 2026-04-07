-- ─────────────────────────────────────────────────────────────────────────────
-- migration_001_onboarding.sql
-- Run ONCE against smart_movie_db to add onboarding + preferences columns.
-- Safe to re-run: uses IF NOT EXISTS / IF EXISTS guards throughout.
-- ─────────────────────────────────────────────────────────────────────────────

USE smart_movie_db;

-- 1. Add is_first_login flag
--    1 = show onboarding,  0 = skip to dashboard
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS is_first_login TINYINT(1) NOT NULL DEFAULT 1
    COMMENT '1 = show onboarding page, 0 = skip to dashboard';

-- 2. Add preferences JSON blob (ML model input store)
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS preferences JSON DEFAULT NULL
    COMMENT 'Stores onboarding ML preference dict as JSON';

-- 3. Any EXISTING users who were already active before this migration:
--    uncomment the next line to mark them as already-onboarded
--    (comment it out if you want every existing user to also see onboarding)
-- UPDATE users SET is_first_login = 0 WHERE is_first_login = 1;

-- ─────────────────────────────────────────────────────────────────────────────
-- VERIFICATION — run these queries manually to confirm everything is set up:
-- ─────────────────────────────────────────────────────────────────────────────

-- Check column definitions
DESCRIBE users;

-- Check data
SELECT
    user_id,
    full_name,
    email,
    is_first_login,
    IF(preferences IS NULL, 'No prefs yet', 'Has prefs') AS prefs_status,
    LEFT(IFNULL(preferences, ''), 80)                     AS prefs_preview
FROM users
ORDER BY user_id;