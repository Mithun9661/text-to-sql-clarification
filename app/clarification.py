from typing import Any


AMBIGUOUS_PHRASES: dict[str, dict[str, Any]] = {
    "best customer": {
        "question": "What do you mean by best customer?",
        "options": ["Highest revenue", "Highest number of orders"],
    },
    "top customer": {
        "question": "How should the top customer be calculated?",
        "options": ["Highest revenue", "Highest number of orders"],
    },
}


def detect_ambiguity(question: str) -> dict[str, Any]:
    normalized = question.lower().strip()

    for phrase, clarification in AMBIGUOUS_PHRASES.items():
        if phrase in normalized:
            return {
                "ambiguous": True,
                "clarification": clarification,
            }

    return {"ambiguous": False, "clarification": None}
