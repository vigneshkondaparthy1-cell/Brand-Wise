"""Shared persistence helpers: Neon Postgres in hosted/configured environments.

When DATABASE_URL is absent, account persistence remains on SQLite and the
workspace data helpers remain on the existing local JSON files.
"""

from contextlib import closing
import json
import os
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parent
MIGRATIONS_DIR = ROOT / "migrations"
_migration_lock = threading.Lock()
_migrations_ready = False


class DatabaseUnavailable(RuntimeError):
    """Raised when configured PostgreSQL storage cannot be reached."""


def uses_postgres():
    if os.environ.get("NO_POSTGRES"):
        return False
    return bool(os.environ.get("DATABASE_URL", "").strip())


def _connect_raw(for_migration=False):
    if not uses_postgres():
        raise RuntimeError("DATABASE_URL is not configured.")
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise DatabaseUnavailable("PostgreSQL support is missing. Install the project requirements.") from exc
    try:
        connection_url = os.environ.get("DATABASE_URL_UNPOOLED", "").strip() if for_migration else ""
        connection_url = connection_url or os.environ["DATABASE_URL"].strip()
        return psycopg.connect(
            connection_url.strip("\"'"),
            row_factory=dict_row,
            connect_timeout=10,
            # The application URL uses Neon's transaction pooler.
            prepare_threshold=None,
        )
    except psycopg.Error as exc:
        raise DatabaseUnavailable("Could not connect to the configured PostgreSQL database.") from exc


class PostgresConnection:
    """Small adapter for the existing sqlite-style execute calls."""

    def __init__(self, connection):
        self._connection = connection

    def execute(self, statement, params=()):
        statement = statement.replace("BEGIN IMMEDIATE", "BEGIN")
        return self._connection.execute(statement.replace("?", "%s"), params)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    def __enter__(self):
        self._connection.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._connection.__exit__(exc_type, exc_value, traceback)


def connect():
    initialize()
    return PostgresConnection(_connect_raw())


def initialize():
    """Apply the checked-in, idempotent Postgres schema migration once per process."""
    global _migrations_ready
    if not uses_postgres() or _migrations_ready:
        return
    with _migration_lock:
        if _migrations_ready:
            return
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        if not migration_files:
            raise DatabaseUnavailable("No PostgreSQL schema migrations were found.")
        try:
            with closing(_connect_raw(for_migration=True)) as raw, raw:
                raw.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())")
                for migration in migration_files:
                    version = migration.name
                    applied = raw.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,)).fetchone()
                    if applied:
                        continue
                    raw.execute("SELECT pg_advisory_xact_lock(hashtext('brandwise-schema-migrations'))")
                    # Recheck under the lock in case another web worker initialized first.
                    applied = raw.execute("SELECT 1 FROM schema_migrations WHERE version = %s", (version,)).fetchone()
                    if not applied:
                        for statement in migration.read_text(encoding="utf-8").split(";"):
                            if statement.strip():
                                raw.execute(statement)
                        raw.execute("INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT DO NOTHING", (version,))
            _migrations_ready = True
        except DatabaseUnavailable:
            raise
        except Exception as exc:
            raise DatabaseUnavailable("Could not initialize the PostgreSQL schema.") from exc


def get_json(key, fallback, legacy_path=None):
    """Read a JSON document from Postgres, importing its local file once if needed."""
    initialize()
    try:
        from psycopg.types.json import Jsonb
        with closing(_connect_raw()) as raw, raw:
            row = raw.execute("SELECT value FROM app_data WHERE key = %s", (key,)).fetchone()
            if row:
                return row["value"]
            value = fallback
            if legacy_path is not None and legacy_path.exists():
                try:
                    value = json.loads(legacy_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    value = fallback
            raw.execute(
                "INSERT INTO app_data (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING",
                (key, Jsonb(value)),
            )
            row = raw.execute("SELECT value FROM app_data WHERE key = %s", (key,)).fetchone()
            return row["value"] if row else value
    except DatabaseUnavailable:
        raise
    except Exception as exc:
        raise DatabaseUnavailable("Could not read workspace data from PostgreSQL.") from exc


def save_json(key, value):
    initialize()
    try:
        from psycopg.types.json import Jsonb
        with closing(_connect_raw()) as raw, raw:
            raw.execute(
                "INSERT INTO app_data (key, value, updated_at) VALUES (%s, %s, now()) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = now()",
                (key, Jsonb(value)),
            )
        return True
    except DatabaseUnavailable:
        raise
    except Exception as exc:
        raise DatabaseUnavailable("Could not save workspace data to PostgreSQL.") from exc


def ping():
    if not uses_postgres():
        return {"engine": "sqlite-json", "connected": True}
    try:
        initialize()
        with closing(_connect_raw()) as raw:
            raw.execute("SELECT 1")
        return {"engine": "neon-postgres", "connected": True}
    except DatabaseUnavailable:
        return {"engine": "neon-postgres", "connected": False}
