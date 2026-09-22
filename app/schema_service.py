from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def get_schema_tables(engine: Engine) -> list[dict]:
    """Return JSON-safe table, column and foreign-key metadata for the UI."""
    inspector = inspect(engine)
    tables = []
    for name in inspector.get_table_names():
        columns = [
            {
                "name": column["name"],
                "type": str(column["type"]),
                "nullable": bool(column.get("nullable", True)),
                "primary_key": bool(column.get("primary_key")),
            }
            for column in inspector.get_columns(name)
        ]
        foreign_keys = [
            {
                "columns": key.get("constrained_columns", []),
                "referred_table": key.get("referred_table"),
                "referred_columns": key.get("referred_columns", []),
            }
            for key in inspector.get_foreign_keys(name)
        ]
        tables.append({"name": name, "columns": columns, "foreign_keys": foreign_keys})
    return tables


def get_database_schema(engine: Engine) -> str:
    """Compact schema description for AI prompts, derived from the same UI metadata."""
    lines = []
    for table in get_schema_tables(engine):
        parts = []
        for column in table["columns"]:
            part = f'{column["name"]} {column["type"]}'
            if not column["nullable"]:
                part += " NOT NULL"
            if column["primary_key"]:
                part += " PRIMARY KEY"
            parts.append(part)
        lines.append(f'TABLE {table["name"]} ({", ".join(parts)})')
        for key in table["foreign_keys"]:
            source = ", ".join(key["columns"])
            target = ", ".join(key["referred_columns"])
            lines.append(f'FOREIGN KEY {table["name"]}.{source} -> {key["referred_table"]}.{target}')
    return "\n".join(lines) if lines else "No user tables were found in this database."
