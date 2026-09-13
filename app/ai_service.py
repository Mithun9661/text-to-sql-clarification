import os
from datetime import date
from typing import Literal

from google import genai
from google.genai import types
from pydantic import BaseModel, Field


class ClarificationOption(BaseModel):
    id: str = Field(description="Stable machine-readable option id")
    label: str = Field(description="Short user-facing option label")


class QueryPlan(BaseModel):
    status: Literal["needs_clarification", "ready", "unsupported"]
    clarification_question: str | None = None
    options: list[ClarificationOption] = Field(default_factory=list)
    interpreted_question: str | None = None
    sql: str | None = None
    explanation: str | None = None


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=api_key)


def build_query_plan(
    question: str,
    schema: str,
    clarification: str | None = None,
) -> QueryPlan:
    today = date.today().isoformat()

    prompt = f"""
You are the reasoning layer of a clarification-aware Text-to-SQL system.

TODAY: {today}
DATABASE DIALECT: SQLite

DATABASE SCHEMA:
{schema}

USER QUESTION:
{question}

USER CLARIFICATION:
{clarification or "None"}

Your job:
1. Determine whether the question is precise enough to generate ONE correct SQL query.
2. If an important business term is ambiguous, do NOT guess. Return status='needs_clarification'.
3. Ask one concise clarification question and provide 2-4 concrete options.
4. If the user supplied a clarification, combine it with the original question before generating SQL.
5. Resolve relative dates such as 'today', 'last month', and 'this year' using TODAY.
6. Use only tables and columns that exist in the supplied schema.
7. Generate only a single read-only SELECT query (WITH/CTE is allowed).
8. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, or multiple statements.
9. Do not invent unavailable business concepts. If the schema cannot answer the request, return status='unsupported'.
10. Add LIMIT 100 for result-list queries unless the query is an aggregate or already naturally returns one/few rows.

Examples of ambiguity:
- 'best customer' may mean highest revenue, most orders, or another measurable metric.
- 'top product' may mean revenue or units sold.
- 'active customer' may have multiple definitions.

A question is NOT ambiguous merely because it is natural language. Ask only when different reasonable interpretations would materially change the SQL/result.
"""

    client = _get_client()
    response = client.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=QueryPlan,
            temperature=0.1,
        ),
    )

    return QueryPlan.model_validate_json(response.text)
