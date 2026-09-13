import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from .ai_service import build_query_plan
from .answer_service import format_answer
from .database import (
    disconnect_database,
    get_connection_info,
    get_engine,
    register_database,
)
from .schema_service import get_database_schema
from .sql_validator import validate_read_only_sql

load_dotenv()

app = FastAPI(title="Universal Text-to-SQL Clarification System")

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class DatabaseConnectRequest(BaseModel):
    database_url: str
    label: str | None = None


class DisconnectRequest(BaseModel):
    connection_id: str


class QueryRequest(BaseModel):
    question: str
    clarification: str | None = None
    connection_id: str | None = None


@app.get("/")
def home():
    return {
        "message": "Universal Text-to-SQL Clarification API is running",
        "supported_databases": ["PostgreSQL", "MySQL", "SQLite"],
        "flow": "connect database -> schema discovery -> ambiguity detection -> clarification -> SQL -> validation -> execution -> answer",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/connect")
def connect_database(request: DatabaseConnectRequest):
    try:
        info = register_database(request.database_url, request.label)
        selected_engine = get_engine(info["connection_id"])
        schema = get_database_schema(selected_engine)
        table_count = schema.count("TABLE ")
        return {
            "status": "connected",
            **info,
            "table_count": table_count,
            "schema": schema,
        }
    except Exception as exc:
        return {
            "status": "connection_error",
            "message": f"Could not connect to database: {exc}",
        }


@app.post("/disconnect")
def disconnect(request: DisconnectRequest):
    disconnect_database(request.connection_id)
    return {"status": "disconnected"}


@app.get("/schema")
def schema(connection_id: str | None = None):
    try:
        selected_engine = get_engine(connection_id)
        return {
            "connection": get_connection_info(connection_id),
            "schema": get_database_schema(selected_engine),
        }
    except KeyError as exc:
        return {"status": "connection_error", "message": str(exc)}


@app.post("/query")
def process_query(request: QueryRequest):
    question = request.question.strip()
    if not question:
        return {"status": "error", "message": "Question cannot be empty."}

    try:
        selected_engine = get_engine(request.connection_id)
        connection_info = get_connection_info(request.connection_id)
        database_schema = get_database_schema(selected_engine)
    except KeyError as exc:
        return {"status": "connection_error", "message": str(exc)}
    except Exception as exc:
        return {"status": "schema_error", "message": f"Could not read database schema: {exc}"}

    try:
        query_plan = build_query_plan(
            question=question,
            schema=database_schema,
            dialect=connection_info["dialect"],
            clarification=request.clarification,
        )
    except RuntimeError as exc:
        return {"status": "configuration_error", "message": str(exc)}
    except Exception as exc:
        return {"status": "ai_error", "message": f"AI planning failed: {exc}"}

    if query_plan.status == "needs_clarification":
        return {
            "status": "clarification_required",
            "original_question": question,
            "question": query_plan.clarification_question,
            "options": [option.model_dump() for option in query_plan.options],
            "connection": connection_info,
        }

    if query_plan.status == "unsupported" or not query_plan.sql:
        return {
            "status": "unsupported_query",
            "message": query_plan.explanation
            or "The selected database schema cannot answer this question reliably.",
        }

    is_valid, validation_error = validate_read_only_sql(query_plan.sql)
    if not is_valid:
        return {
            "status": "blocked_query",
            "message": validation_error,
            "sql": query_plan.sql,
        }

    try:
        with selected_engine.connect() as connection:
            result = connection.execute(text(query_plan.sql))
            rows = [dict(row._mapping) for row in result]
    except Exception as exc:
        return {
            "status": "execution_error",
            "message": str(exc),
            "sql": query_plan.sql,
        }

    return {
        "status": "success",
        "connection": connection_info,
        "interpreted_question": query_plan.interpreted_question or question,
        "answer": format_answer(rows),
        "sql": query_plan.sql.strip(),
        "result": rows,
        "row_count": len(rows),
        "explanation": query_plan.explanation,
    }
