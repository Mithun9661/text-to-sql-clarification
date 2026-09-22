"""Protect access to company databases; demo remains public."""
import hmac
import os
from fastapi import Header, HTTPException


def require_admin(x_api_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("ADMIN_API_KEY", "")
    if not expected or not x_api_key or not hmac.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=403, detail="Company database access requires a configured API key.")


def authorize_connection(connection_id: str | None, x_api_key: str | None) -> None:
    if connection_id and connection_id != "demo":
        require_admin(x_api_key)
