-- deployment/init_db.sql
-- SQL commands to set up the PostgreSQL database and user with minimal privileges.
-- This script should be run by a PostgreSQL superuser (e.g., 'postgres').

-- 1. Create a dedicated database user
--    Replace 'YOUR_GENERATED_PASSWORD' with the actual strong password you obtained.
DO
$do$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'learning_user') THEN
      CREATE USER learning_user WITH PASSWORD '1469';
   ELSE
      ALTER USER learning_user WITH PASSWORD '1469'; -- Update password if user already exists
   END IF;
END
$do$;

-- 2. Create the database, owned by the new user
--    If the database already exists, this command will be skipped.
SELECT 'CREATE DATABASE learning_platform_db OWNER learning_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'learning_platform_db')\gexec

-- 3. Grant minimal privileges to the database user on the database
--    This ensures the user can connect and operate within their schema, but not modify system tables.
GRANT CONNECT ON DATABASE learning_platform_db TO learning_user;

-- Grant usage on the public schema to the new user if they need to create tables there
GRANT USAGE ON SCHEMA public TO learning_user;
ALTER DEFAULT PRIVILEGES FOR USER learning_user IN SCHEMA public GRANT ALL ON TABLES TO learning_user;
ALTER DEFAULT PRIVILEGES FOR USER learning_user IN SCHEMA public GRANT ALL ON SEQUENCES TO learning_user;
ALTER DEFAULT PRIVILEGES FOR USER learning_user IN SCHEMA public GRANT ALL ON FUNCTIONS TO learning_user;

-- Note: In a real production setup, you might create a dedicated schema for your application's tables
-- and grant privileges only on that schema. For simplicity in this initial setup, we are using public. 