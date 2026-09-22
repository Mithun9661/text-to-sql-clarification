"""Query history. Set HISTORY_DATABASE_URL to persistent PostgreSQL on Render."""
import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text, DateTime, select, insert, delete

metadata = MetaData()
history = Table("query_history", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("question", Text, nullable=False),
    Column("clarification", Text),
    Column("sql_text", Text, nullable=False),
    Column("answer", Text, nullable=False),
    Column("connection_id", String(64), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
)
_engine = None


def history_engine():
    global _engine
    if _engine is None:
        url = os.getenv("HISTORY_DATABASE_URL", "sqlite:///./history.db")
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        _engine = create_engine(url, pool_pre_ping=True)
        metadata.create_all(_engine)
    return _engine


def save_query(question: str, clarification: str | None, sql: str, answer: str, connection_id: str) -> None:
    with history_engine().begin() as conn:
        conn.execute(insert(history).values(question=question, clarification=clarification, sql_text=sql, answer=answer, connection_id=connection_id, created_at=datetime.now(timezone.utc)))


def list_queries(connection_id: str, limit: int = 50) -> list[dict]:
    with history_engine().connect() as conn:
        rows = conn.execute(select(history).where(history.c.connection_id == connection_id).order_by(history.c.id.desc()).limit(min(max(limit, 1), 100))).mappings().all()
        return [{**dict(row), "created_at":row["created_at"].isoformat()} for row in rows]


def clear_queries(connection_id: str) -> None:
    with history_engine().begin() as conn:
        conn.execute(delete(history).where(history.c.connection_id == connection_id))
