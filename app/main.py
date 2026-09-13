from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import text

from .clarification import detect_ambiguity
from .database import engine
from .sql_generator import generate_sql

app = FastAPI(title="Text-to-SQL Clarification System")


class QueryRequest(BaseModel):
    question: str
    clarification: str | None = None


@app.get("/")
def home():
    return {"message": "Text-to-SQL Clarification API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/query")
def process_query(request: QueryRequest):
    if not request.clarification:
        ambiguity = detect_ambiguity(request.question)
        if ambiguity["ambiguous"]:
            clarification = ambiguity["clarification"]
            return {
                "status": "clarification_required",
                "question": clarification["question"],
                "options": clarification["options"],
            }

    sql = generate_sql(request.question, request.clarification)

    if not sql:
        return {
            "status": "unsupported_query",
            "message": "This MVP does not support this question yet.",
        }

    try:
        with engine.connect() as connection:
            result = connection.execute(text(sql))
            rows = [dict(row._mapping) for row in result]

        return {
            "status": "success",
            "sql": sql.strip(),
            "result": rows,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}
