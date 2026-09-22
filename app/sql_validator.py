"""Conservative guardrail for generated read-only SQL.

This is defense in depth, not a replacement for a database read-only user.
"""
import re

FORBIDDEN = re.compile(
    r"\b(?:insert|update|delete|drop|alter|truncate|replace|create|attach|detach|"
    r"pragma|vacuum|reindex|grant|revoke|execute|exec|call|copy|merge|"
    r"into|outfile|load_file|pg_sleep|dblink|set_config|pg_read_file|"
    r"pg_ls_dir|lo_import|lo_export|sleep|benchmark)\b",
    re.IGNORECASE,
)


def validate_read_only_sql(sql: str) -> tuple[bool, str | None]:
    if not isinstance(sql, str) or not sql.strip():
        return False, "SQL is empty."
    if len(sql) > 20000:
        return False, "SQL exceeds the maximum allowed length."

    # Remove comments and literals for keyword checks, but reject comments outright
    # to avoid dialect-specific parser bypasses and hidden instructions.
    if re.search(r"--|/\*|\*/|#", sql):
        return False, "SQL comments are not allowed."
    cleaned = sql.strip()
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].rstrip()
    if ";" in cleaned:
        return False, "Multiple SQL statements are not allowed."
    if not re.match(r"^(?:select|with)\b", cleaned, re.IGNORECASE):
        return False, "Only SELECT queries are allowed."

    # Mask quoted literals and identifiers so ordinary customer values do not
    # trigger false positives; doubled SQL quotes are supported.
    masked = re.sub(r"'(?:''|[^'])*'", "''", cleaned)
    masked = re.sub(r'"(?:""|[^"])*"', '""', masked)
    if FORBIDDEN.search(masked):
        return False, "Unsafe SQL operation or function detected."
    if re.search(r"\b(?:for\s+update|for\s+share|lock\s+in\s+share\s+mode)\b", masked, re.IGNORECASE):
        return False, "Locking queries are not allowed."
    return True, None
