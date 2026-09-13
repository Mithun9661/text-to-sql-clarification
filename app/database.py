from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./company.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# In-memory registry for user-connected company databases.
# Credentials are never written to GitHub or returned by the API.
_CONNECTIONS: dict[str, Engine] = {"demo": engine}
_CONNECTION_LABELS: dict[str, str] = {"demo": "Demo Company Database"}

SUPPORTED_DIALECTS = {"sqlite", "postgresql", "mysql"}


def _engine_for_url(database_url: str) -> Engine:
    url = make_url(database_url.strip())
    dialect = url.get_backend_name()

    if dialect not in SUPPORTED_DIALECTS:
        raise ValueError(
            "Unsupported database. Use PostgreSQL, MySQL, or SQLite."
        )

    # Pick pure-Python/bundled drivers so common company connection URLs work directly.
    if dialect == "postgresql" and "+" not in url.drivername:
        url = url.set(drivername="postgresql+psycopg")
    elif dialect == "mysql" and "+" not in url.drivername:
        url = url.set(drivername="mysql+pymysql")

    kwargs = {"pool_pre_ping": True}
    if dialect == "sqlite":
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_engine(url, **kwargs)


def register_database(database_url: str, label: str | None = None) -> dict[str, str]:
    if not database_url or not database_url.strip():
        raise ValueError("Database URL is required.")

    new_engine = _engine_for_url(database_url)

    # Verify connectivity before storing the engine.
    with new_engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    connection_id = uuid4().hex
    _CONNECTIONS[connection_id] = new_engine
    _CONNECTION_LABELS[connection_id] = (label or "Company Database").strip()

    return {
        "connection_id": connection_id,
        "label": _CONNECTION_LABELS[connection_id],
        "dialect": new_engine.dialect.name,
    }


def get_engine(connection_id: str | None = None) -> Engine:
    key = connection_id or "demo"
    selected = _CONNECTIONS.get(key)
    if not selected:
        raise KeyError("Database connection not found. Please reconnect the database.")
    return selected


def get_connection_info(connection_id: str | None = None) -> dict[str, str]:
    key = connection_id or "demo"
    selected = get_engine(key)
    return {
        "connection_id": key,
        "label": _CONNECTION_LABELS.get(key, "Company Database"),
        "dialect": selected.dialect.name,
    }


def disconnect_database(connection_id: str) -> None:
    if not connection_id or connection_id == "demo":
        return

    selected = _CONNECTIONS.pop(connection_id, None)
    _CONNECTION_LABELS.pop(connection_id, None)
    if selected is not None:
        selected.dispose()
