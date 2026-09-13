# Text-to-SQL with Clarification

A practical AI project that converts natural-language questions into SQL, but asks a clarification question first when the user request is ambiguous.

## Example

User: `Show me last month's best customer.`

Instead of guessing, the system asks whether `best` means:
- highest revenue
- highest number of orders

After the user clarifies, the system generates and executes SQL.

## Tech Stack

- Python
- FastAPI
- SQLite / SQLAlchemy
- Pydantic
- Gemini/OpenAI integration planned

## Project Flow

Natural language question -> ambiguity detection -> clarification -> SQL generation -> validation -> execution -> result

## Run locally

```bash
pip install -r requirements.txt
python seed.py
uvicorn app.main:app --reload
```

Open: `http://127.0.0.1:8000/docs`

## Current Status

Phase 1: working rule-based MVP.
Next: LLM-based ambiguity detection and schema-aware SQL generation.
