ALTER TABLE sessions ADD COLUMN IF NOT EXISTS active_company_id TEXT;

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
