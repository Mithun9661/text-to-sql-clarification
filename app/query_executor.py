"""Database-enforced read-only query execution with bounded results and deadlines."""
import os
import time
from sqlalchemy import text
from sqlalchemy.engine import Engine


def execute_read_only(engine: Engine, sql: str, max_rows: int = 200) -> tuple[list[dict], bool]:
    timeout_ms = max(100, min(int(os.getenv("QUERY_TIMEOUT_MS", "5000")), 30000))
    dialect = engine.dialect.name
    with engine.connect() as connection:
        if dialect == "postgresql":
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        elif dialect == "sqlite":
            # SQLite progress handler interrupts long-running VM execution.
            raw = connection.connection.driver_connection
            deadline = time.monotonic() + timeout_ms / 1000
            raw.set_progress_handler(lambda: int(time.monotonic() > deadline), 1000)
            raw.execute("PRAGMA query_only = ON")
        elif dialect == "mysql":
            # MySQL optimizer hint is applied only to SELECT statements; a read-only DB user is mandatory.
            stripped = sql.lstrip()
            if stripped[:6].lower() == "select":
                sql = stripped[:6] + f" /*+ MAX_EXECUTION_TIME({timeout_ms}) */" + stripped[6:]
        try:
            result = connection.execution_options(stream_results=True).execute(text(sql))
            try:
                fetched = result.fetchmany(max_rows + 1)
                return [dict(row._mapping) for row in fetched[:max_rows]], len(fetched) > max_rows
            finally:
                result.close()
        finally:
            if dialect == "sqlite":
                # Always restore pooled connections, including on SQL errors/timeouts.
                raw.set_progress_handler(None, 0)
                raw.execute("PRAGMA query_only = OFF")
