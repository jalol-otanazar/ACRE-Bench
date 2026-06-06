#!/usr/bin/env python3
"""Evaluate ACRE-Bench predictions.

Prediction format: JSON Lines
{
  "id": "A1",
  "answer": "...",
  "citations": ["Poetics"]
}
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

REFUSAL_MARKERS = [
    "not stated",
    "not in the corpus",
    "cannot determine",
    "unsupported",
    "no evidence",
    "not provided",
    "does not say",
    "nowhere",
    "false",
    "anachronistic",
]


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def citation_hit(gold: dict, pred: dict) -> float:
    gold_docs = gold.get("supporting_works") or []
    pred_citations = pred.get("citations") or []
    if isinstance(pred_citations, str):
        pred_citations = [pred_citations]

    if not gold_docs:
        return 1.0 if not pred_citations else 0.0

    gold_norm = {normalize(doc) for doc in gold_docs}
    for citation in pred_citations:
        if normalize(str(citation)) in gold_norm:
            return 1.0
    return 0.0


def answer_score(gold: dict, pred_answer: str) -> float:
    answer_type = gold.get("answer_type", "short")
    gold_answer = gold.get("answer", "")
    pred_norm = normalize(pred_answer or "")
    gold_norm = normalize(gold_answer or "")

    if answer_type == "refusal":
        if any(marker in pred_norm for marker in REFUSAL_MARKERS):
            return 1.0
        if pred_norm and pred_norm != gold_norm and len(pred_norm.split()) <= 20:
            return 0.5
        return 0.0

    if answer_type == "list":
        gold_items = [normalize(part) for part in gold_answer.split(";") if part.strip()]
        if not gold_items:
            return 0.0
        return 1.0 if all(item in pred_norm for item in gold_items) else 0.0

    if not pred_norm or not gold_norm:
        return 0.0
    if pred_norm == gold_norm:
        return 1.0
    if gold_norm in pred_norm or pred_norm in gold_norm:
        return 1.0
    return 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate ACRE-Bench predictions.")
    parser.add_argument("--gold", type=Path, required=True, help="Path to benchmark/seed_questions.jsonl")
    parser.add_argument("--predictions", type=Path, required=True, help="Path to model predictions JSONL")
    args = parser.parse_args()

    gold_rows = load_jsonl(args.gold)
    pred_rows = load_jsonl(args.predictions)
    preds: Dict[str, dict] = {row["id"]: row for row in pred_rows if "id" in row}

    per_family_answer = defaultdict(float)
    per_family_citation = defaultdict(float)
    per_family_count = defaultdict(int)

    answer_total = 0.0
    citation_total = 0.0
    missing = []

    for gold in gold_rows:
        qid = gold["id"]
        family = gold.get("family", "unknown")
        pred = preds.get(qid, {})
        if qid not in preds:
            missing.append(qid)

        a = answer_score(gold, pred.get("answer", ""))
        c = citation_hit(gold, pred)
        answer_total += a
        citation_total += c
        per_family_answer[family] += a
        per_family_citation[family] += c
        per_family_count[family] += 1

    total = len(gold_rows) or 1
    answer_acc = answer_total / total
    citation_acc = citation_total / total
    overall = 0.85 * answer_acc + 0.15 * citation_acc

    print(json.dumps(
        {
            "total_questions": total,
            "answer_accuracy": round(answer_acc, 4),
            "citation_hit_rate": round(citation_acc, 4),
            "overall_score": round(overall, 4),
            "missing_predictions": missing,
        },
        indent=2,
    ))

    print("\nFamily breakdown:")
    for family in sorted(per_family_count):
        count = per_family_count[family]
        a = per_family_answer[family] / count if count else 0.0
        c = per_family_citation[family] / count if count else 0.0
        score = 0.85 * a + 0.15 * c
        print(f"- {family}: answer={a:.3f}, citation={c:.3f}, score={score:.3f} ({count} items)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
