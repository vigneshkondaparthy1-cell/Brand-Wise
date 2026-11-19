-- Compatibility repair: this repository snapshot omits migrations 002 and
-- 003, and migration 004 has already run on the hosted database.
CREATE TABLE IF NOT EXISTS login_failures (
    ip TEXT NOT NULL,
    attempted_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS login_failures_ip_idx ON login_failures (ip, attempted_at);

CREATE TABLE IF NOT EXISTS companies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_username TEXT NOT NULL,
    created_at BIGINT NOT NULL
);
CREATE TABLE IF NOT EXISTS company_memberships (
    company_id TEXT NOT NULL,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    joined_at BIGINT NOT NULL,
    PRIMARY KEY (company_id, username)
);
CREATE INDEX IF NOT EXISTS company_memberships_username_idx ON company_memberships (username);
CREATE TABLE IF NOT EXISTS company_invitations (
    code_hash BYTEA PRIMARY KEY,
    company_id TEXT NOT NULL,
    email TEXT NOT NULL,
    role TEXT NOT NULL,
    expires BIGINT NOT NULL,
    created_by TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS company_invitations_email_idx ON company_invitations (lower(email));
