"""History API: company history requires admin key; demo history is shared."""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from .security import authorize_connection
from .history_store import list_queries, clear_queries

router = APIRouter(prefix="/history", tags=["history"])

class ClearHistory(BaseModel):
    connection_id: str = "demo"

@router.get("")
def get_history(connection_id: str = "demo", x_api_key: str | None = Header(default=None)):
    authorize_connection(connection_id, x_api_key)
    try:
        return {"status": "success", "items": list_queries(connection_id)}
    except Exception:
        raise HTTPException(503, "History storage is unavailable.")

@router.post("/clear")
def delete_history(request: ClearHistory, x_api_key: str | None = Header(default=None)):
    authorize_connection(request.connection_id, x_api_key)
    try:
        clear_queries(request.connection_id)
        return {"status": "success"}
    except Exception:
        raise HTTPException(503, "History storage is unavailable.")
