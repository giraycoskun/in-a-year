-- Run with:
-- psql -U postgres -d postgres -f scripts/create_database.sql
--
-- Default app credentials in this script:
--   user: inayear
--   pass: inayear
-- Change the password after first run in production.

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'inayear'
    ) THEN
        CREATE ROLE inayear
            LOGIN
            PASSWORD 'inayear'
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION;
    END IF;
END
$$;

SELECT 'CREATE DATABASE inayear OWNER inayear'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'inayear'
)\gexec

ALTER DATABASE inayear OWNER TO inayear;
GRANT CONNECT ON DATABASE inayear TO inayear;

\connect inayear

GRANT USAGE, CREATE ON SCHEMA public TO inayear;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO inayear;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO inayear;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO inayear;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO inayear;
