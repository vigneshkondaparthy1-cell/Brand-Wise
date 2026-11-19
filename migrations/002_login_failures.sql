CREATE TABLE IF NOT EXISTS login_failures (
    ip TEXT NOT NULL,
    attempted_at BIGINT NOT NULL
);
CREATE INDEX IF NOT EXISTS login_failures_ip_idx ON login_failures (ip, attempted_at);
