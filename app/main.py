from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text
from dotenv import load_dotenv

from .ai_service import build_query_plan
from .database import engine
from .schema_service import get_database_schema
from .sql_validator import validate_read_only_sql

load_dotenv()

app = FastAPI(title="Text-to-SQL Clarification System")


class QueryRequest(BaseModel):
    question: str
    clarification: str | None = None


@app.get("/")
def home():
    return {
        "message": "Text-to-SQL Clarification API is running",
        "flow": "question -> ambiguity detection -> clarification -> SQL -> validation -> execution",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/schema")
def schema():
    return {"schema": get_database_schema()}


@app.post("/query")
def process_query(request: QueryRequest):
    question = request.question.strip()
    if not question:
        return {"status": "error", "message": "Question cannot be empty."}

    try:
        query_plan = build_query_plan(
            question=question,
            schema=get_database_schema(),
            clarification=request.clarification,
        )
    except RuntimeError as exc:
        return {
            "status": "configuration_error",
            "message": str(exc),
        }
    except Exception as exc:
        return {
            "status": "ai_error",
            "message": f"AI planning failed: {exc}",
        }

    if query_plan.status == "needs_clarification":
        return {
            "status": "clarification_required",
            "original_question": question,
            "question": query_plan.clarification_question,
            "options": [option.model_dump() for option in query_plan.options],
        }

    if query_plan.status == "unsupported" or not query_plan.sql:
        return {
            "status": "unsupported_query",
            "message": query_plan.explanation
            or "The available database schema cannot answer this question reliably.",
        }

    is_valid, validation_error = validate_read_only_sql(query_plan.sql)
    if not is_valid:
        return {
            "status": "blocked_query",
            "message": validation_error,
            "sql": query_plan.sql,
        }

    try:
        with engine.connect() as connection:
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
        "interpreted_question": query_plan.interpreted_question or question,
        "sql": query_plan.sql.strip(),
        "result": rows,
        "row_count": len(rows),
        "explanation": query_plan.explanation,
    }
