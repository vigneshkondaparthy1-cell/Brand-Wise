CREATE TABLE IF NOT EXISTS accounts (
    username TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    organization TEXT NOT NULL,
    work TEXT NOT NULL,
    responsibilities TEXT NOT NULL,
    salt BYTEA NOT NULL,
    password_hash BYTEA NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS accounts_username_lower_uidx ON accounts (lower(username));
CREATE UNIQUE INDEX IF NOT EXISTS accounts_email_lower_uidx ON accounts (lower(email));

CREATE TABLE IF NOT EXISTS sessions (
    token BYTEA PRIMARY KEY,
    username TEXT NOT NULL,
    expires BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS sessions_username_idx ON sessions (username);
CREATE INDEX IF NOT EXISTS sessions_expires_idx ON sessions (expires);

CREATE TABLE IF NOT EXISTS email_verifications (
    email TEXT PRIMARY KEY,
    code_hash BYTEA NOT NULL,
    salt BYTEA NOT NULL,
    expires BIGINT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    verified_until BIGINT NOT NULL DEFAULT 0,
    last_sent BIGINT NOT NULL,
    send_window BIGINT NOT NULL,
    sends_in_window INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS password_resets (
    email TEXT PRIMARY KEY,
    code_hash BYTEA NOT NULL,
    salt BYTEA NOT NULL,
    expires BIGINT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    last_sent BIGINT NOT NULL,
    send_window BIGINT NOT NULL,
    sends_in_window INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS app_data (
    key TEXT PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
