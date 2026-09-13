from typing import Any


def format_answer(rows: list[dict[str, Any]]) -> str:
    """Create a simple user-facing answer from SQL result rows."""
    if not rows:
        return "No matching data was found."

    if len(rows) == 1:
        row = rows[0]
        if len(row) == 1:
            key, value = next(iter(row.items()))
            return f"{key.replace('_', ' ').title()}: {value}"

        parts = [f"{key.replace('_', ' ')}: {value}" for key, value in row.items()]
        return ", ".join(parts)

    return f"Found {len(rows)} matching records."
