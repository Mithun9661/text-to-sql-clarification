from sqlalchemy import inspect

from .database import engine


def get_database_schema() -> str:
    """Return a compact schema description for the LLM."""
    inspector = inspect(engine)
    lines: list[str] = []

    for table_name in inspector.get_table_names():
        columns = inspector.get_columns(table_name)
        column_parts = []

        for column in columns:
            part = f"{column['name']} {column['type']}"
            if not column.get("nullable", True):
                part += " NOT NULL"
            column_parts.append(part)

        lines.append(f"TABLE {table_name} ({', '.join(column_parts)})")

        for foreign_key in inspector.get_foreign_keys(table_name):
            constrained = ", ".join(foreign_key.get("constrained_columns", []))
            referred_table = foreign_key.get("referred_table")
            referred = ", ".join(foreign_key.get("referred_columns", []))
            lines.append(
                f"FOREIGN KEY {table_name}.{constrained} -> {referred_table}.{referred}"
            )

    return "\n".join(lines)
