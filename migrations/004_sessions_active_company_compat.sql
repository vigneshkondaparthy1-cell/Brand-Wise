-- Repair hosted databases where an earlier migration was marked applied
-- without creating the session workspace column needed by authentication.
ALTER TABLE sessions ADD COLUMN IF NOT EXISTS active_company_id TEXT;
