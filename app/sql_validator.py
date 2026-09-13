import re


BLOCKED_KEYWORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "replace",
    "create",
    "attach",
    "detach",
    "pragma",
    "vacuum",
    "reindex",
}


def validate_read_only_sql(sql: str) -> tuple[bool, str | None]:
    if not sql or not sql.strip():
        return False, "SQL is empty."

    cleaned = sql.strip().rstrip(";").strip()

    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed."

    normalized = re.sub(r"\s+", " ", cleaned.lower())

    if not (normalized.startswith("select ") or normalized.startswith("with ")):
        return False, "Only SELECT queries are allowed."

    words = set(re.findall(r"\b[a-z_]+\b", normalized))
    blocked = sorted(words.intersection(BLOCKED_KEYWORDS))
    if blocked:
        return False, f"Blocked SQL keyword detected: {blocked[0]}"

    return True, None
