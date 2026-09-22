"""Evaluate ambiguity handling and answer accuracy against a labeled JSON dataset.

Run: python evaluation/evaluate.py evaluation/questions.json baseline.json clarification.json
Prediction files are JSON arrays of {id, needs_clarification, answer}; baseline may
choose an interpretation, while clarification predictions must reflect the selected
user intent. Answers are compared after whitespace/case normalization. No metrics
are invented when predictions are missing.
"""
import json
import sys
from pathlib import Path


def load(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list) or any(not isinstance(item, dict) or "id" not in item for item in data):
        raise ValueError(f"Expected a list of objects with ids: {path}")
    ids = [str(item["id"]) for item in data]
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate ids in {path}")
    return {str(item["id"]): item for item in data}


def normalized(value):
    return " ".join(str(value).casefold().split())


def evaluate(gold, predictions, name):
    missing = set(gold) - set(predictions)
    extra = set(predictions) - set(gold)
    if missing or extra:
        raise ValueError(f"{name}: missing ids={sorted(missing)}, extra ids={sorted(extra)}")
    total = len(gold)
    if not total:
        raise ValueError("Evaluation dataset cannot be empty")
    detection = sum(bool(predictions[key].get("needs_clarification")) == bool(item["ambiguous"]) for key, item in gold.items())
    answer = sum(normalized(predictions[key].get("answer", "")) == normalized(item["expected_answer"]) for key, item in gold.items())
    ambiguous = [key for key, item in gold.items() if item["ambiguous"]]
    ambiguous_correct = sum(normalized(predictions[key].get("answer", "")) == normalized(gold[key]["expected_answer"]) for key in ambiguous)
    return {"mode": name, "questions": total, "ambiguity_detection_accuracy": round(detection / total, 4), "answer_accuracy": round(answer / total, 4), "ambiguous_answer_accuracy": round(ambiguous_correct / len(ambiguous), 4) if ambiguous else None}


def main():
    if len(sys.argv) != 4:
        raise SystemExit("Usage: python evaluation/evaluate.py GOLD.json BASELINE.json CLARIFICATION.json")
    gold = load(sys.argv[1])
    for item in gold.values():
        if not isinstance(item.get("ambiguous"), bool) or "expected_answer" not in item:
            raise ValueError("Gold records require boolean ambiguous and expected_answer")
    baseline = evaluate(gold, load(sys.argv[2]), "baseline")
    clarified = evaluate(gold, load(sys.argv[3]), "clarification")
    print(json.dumps({"baseline": baseline, "clarification": clarified, "answer_accuracy_delta": round(clarified["answer_accuracy"] - baseline["answer_accuracy"], 4)}, indent=2))


if __name__ == "__main__":
    main()
