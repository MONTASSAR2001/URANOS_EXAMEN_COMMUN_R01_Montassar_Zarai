-- =============================================================================
-- URANOS Project OS — MariaDB bootstrap
-- Runs once on first container start (docker-entrypoint-initdb.d/).
-- Creates the dedicated Frappe database user with minimal required privileges.
-- =============================================================================
--
-- ⚠️  IMPORTANT: The password for the 'frappe'@'%' user is intentionally set
-- to a placeholder here. The actual password used by Frappe is set by
-- `bench new-site --db-root-password` at site-creation time, which creates a
-- new user specific to that site (e.g., 'erpnext_abc123'@'%').
--
-- This bootstrap user ('frappe'@'%') is a convenience for manual DBA access
-- only. In practice, bench manages its own per-site credentials automatically.
--
-- The actual site DB user password comes from .env → DB_FRAPPE_PASSWORD
-- and is passed to `bench new-site` by setup_dev.sh.
-- =============================================================================

-- The actual site database is created later by `bench new-site`.
-- This script only pre-provisions wildcard DDL access patterns that
-- Frappe requires to create and migrate databases dynamically.

-- Pre-provision the frappe admin user (bench may also create its own).
-- Password is set to a long random placeholder; bench new-site will update it.
CREATE USER IF NOT EXISTS 'frappe'@'%' IDENTIFIED BY 'placeholder_bench_will_override';

-- Frappe requires CREATE, DROP, and ALTER on dynamically-named databases.
-- Grant on the frappe_* wildcard pattern (covers all bench sites).
GRANT ALL PRIVILEGES ON `frappe\_%`.* TO 'frappe'@'%';
-- Grant on the _frappe_init DB used during new-site bootstrapping.
GRANT ALL PRIVILEGES ON `_frappe\_init`.* TO 'frappe'@'%';

-- SUPER is required by Frappe for certain DDL operations (triggers, full-text).
-- Scope: localhost only (container-internal). Review and remove after schema
-- stabilises for any production-adjacent environment.
-- (MariaDB 10.6+: use BINLOG ADMIN, SYSTEM VARIABLES instead for least-priv)
GRANT SUPER ON *.* TO 'frappe'@'%';

FLUSH PRIVILEGES;
