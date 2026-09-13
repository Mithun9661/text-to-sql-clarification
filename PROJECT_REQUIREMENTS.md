# Project Requirements — Text-to-SQL with Clarification

This file is the source of truth for the project. Future implementation should stay aligned with these requirements.

## Core Problem
Companies store data in relational databases such as customers, orders, payments and related business tables. Non-technical users should be able to ask questions in plain English and receive answers without writing SQL manually.

A normal Text-to-SQL system is not enough because business questions can be ambiguous. The system must not confidently guess the user's intent when multiple valid interpretations exist.

## Required Behaviour
1. Accept a natural-language business question in English.
2. Understand the connected database schema.
3. Detect whether the question is clear or ambiguous.
4. If the question is clear, generate SQL directly.
5. If the question is ambiguous, DO NOT generate final SQL yet.
6. Ask a concise clarification question with useful choices.
7. After the user clarifies the intended meaning, generate the final SQL.
8. Validate the generated SQL before execution.
9. Execute only safe read-only queries against the database.
10. Return both the database result and a simple natural-language answer.

## Main Example
User asks:

`Show me last month's best customer.`

The system should recognize that `best customer` is ambiguous. Possible interpretations include:
- customer with the highest total revenue/spend
- customer with the highest number of orders
- another available business metric if the schema supports it

The system must ask the user which meaning they want. Only after the clarification should SQL be generated and executed.

## Evaluation Requirement
The project should report performance in two modes:
- Text-to-SQL without clarification
- Text-to-SQL with clarification

Testing should especially include ambiguous questions and show how clarification reduces wrong SQL/answers.

Useful evaluation fields:
- total test questions
- clear vs ambiguous questions
- ambiguity-detection accuracy
- SQL execution accuracy
- final answer accuracy without clarification
- final answer accuracy with clarification

## Required Concepts
- Basic SQL
- Prompt engineering
- Structured LLM output
- Database/schema understanding
- Clarification handling

## Planned Stack
- Python
- FastAPI backend
- SQLAlchemy for database access
- SQLite for the zero-cost demo; architecture should allow PostgreSQL/MySQL later
- Pydantic structured models
- Gemini or OpenAI-compatible LLM integration
- Simple frontend after the core AI/backend flow is correct

## Cost Goal
The development/demo version should be possible with zero or minimal cost by using a local database and an available free-tier model/API where possible.

## Safety Rules
- LLM-generated SQL must not be executed blindly.
- Only SELECT/read-only queries are allowed in the MVP.
- Block INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE and other destructive statements.
- Apply result limits where appropriate.
- Never expose API keys in GitHub.

## Required End-to-End Flow

`User question -> schema context -> ambiguity detection -> clarification if needed -> final intent -> SQL generation -> SQL validation -> database execution -> natural-language answer`

## Scope Rule
The project's main differentiator is the clarification layer. Features that do not strengthen the above flow are secondary and should not replace or distract from the core requirement.
