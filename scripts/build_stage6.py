#!/usr/bin/env python3
"""Build Stage 6 audit reports for ACRE-Bench.

Stage 6 is a validity and contamination audit, not a question-generation stage.

It produces JSON reports for:
- duplicate / near-duplicate leakage
- family balance
- supporting-work distribution
- holdout overlap risk

Usage:
  python scripts/build_stage6.py \
    --seed benchmark/seed_questions.jsonl \
    --stage2 benchmark/stage2_questions.jsonl \
    --stage3 benchmark/stage3_questions.jsonl \
    --stage4 benchmark/stage4_questions.jsonl \
    --outdir benchmark/stage6_reports
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path or not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def token_set(text: str) -> set[str]:
    return set(normalize(text).split())


def jaccard(a: str, b: str) -> float:
    sa = token_set(a)
    sb = token_set(b)
    if not sa and not sb:
        return 1.0
    if not sa or not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def report_duplicates(all_rows: List[dict]) -> List[dict]:
    grouped: Dict[str, List[dict]] = defaultdict(list)
    for row in all_rows:
        q = row.get("question", "")
        grouped[normalize(q)].append(row)

    dupes = []
    for norm_q, rows in grouped.items():
        if len(rows) > 1:
            dupes.append({
                "normalized_question": norm_q,
                "count": len(rows),
                "ids": [r.get("id") for r in rows],
                "families": [r.get("family") for r in rows],
            })
    dupes.sort(key=lambda x: (-x["count"], x["normalized_question"]))
    return dupes


def report_near_duplicates(all_rows: List[dict], threshold: float = 0.72) -> List[dict]:
    items = [(row.get("id"), row.get("question", ""), row.get("family")) for row in all_rows]
    near = []
    for i in range(len(items)):
        id_a, q_a, fam_a = items[i]
        for j in range(i + 1, len(items)):
            id_b, q_b, fam_b = items[j]
            score = jaccard(q_a, q_b)
            if threshold <= score < 1.0:
                near.append({
                    "id_a": id_a,
                    "id_b": id_b,
                    "family_a": fam_a,
                    "family_b": fam_b,
                    "jaccard": round(score, 3),
                    "question_a": q_a,
                    "question_b": q_b,
                })
    near.sort(key=lambda x: (-x["jaccard"], x["id_a"], x["id_b"]))
    return near[:5000]


def report_family_balance(all_rows: List[dict]) -> dict:
    family_counts = Counter(row.get("family", "unknown") for row in all_rows)
    total = sum(family_counts.values()) or 1
    return {
        "total_questions": total,
        "family_counts": dict(family_counts),
        "family_share": {fam: round(cnt / total, 4) for fam, cnt in family_counts.items()},
    }


def report_support_distribution(all_rows: List[dict]) -> dict:
    work_counts = Counter()
    multi_support = 0
    for row in all_rows:
        works = row.get("supporting_works") or []
        if len(works) > 1:
            multi_support += 1
        for work in works:
            work_counts[work] += 1
    total = sum(work_counts.values()) or 1
    return {
        "supporting_work_counts": dict(work_counts),
        "supporting_work_share": {w: round(c / total, 4) for w, c in work_counts.items()},
        "multi_support_questions": multi_support,
    }


def report_holdout_overlap(stage4_rows: List[dict], earlier_rows: List[dict]) -> dict:
    earlier_norm = {normalize(row.get("question", "")) for row in earlier_rows}
    exact_overlap = []
    near_overlap = []
    for row in stage4_rows:
        q = row.get("question", "")
        nq = normalize(q)
        if nq in earlier_norm:
            exact_overlap.append(row.get("id"))
        else:
            best = 0.0
            for prev in earlier_rows:
                score = jaccard(q, prev.get("question", ""))
                if score > best:
                    best = score
            if best >= 0.75:
                near_overlap.append({"id": row.get("id"), "best_jaccard": round(best, 3)})
    return {
        "exact_overlap_ids": exact_overlap,
        "near_overlap": near_overlap[:500],
        "exact_overlap_count": len(exact_overlap),
        "near_overlap_count": len(near_overlap),
    }


def dump(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ACRE-Bench Stage 6 audit reports.")
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--stage2", type=Path, required=False)
    parser.add_argument("--stage3", type=Path, required=False)
    parser.add_argument("--stage4", type=Path, required=False)
    parser.add_argument("--outdir", type=Path, required=True)
    args = parser.parse_args()

    seed_rows = load_jsonl(args.seed)
    stage2_rows = load_jsonl(args.stage2) if args.stage2 else []
    stage3_rows = load_jsonl(args.stage3) if args.stage3 else []
    stage4_rows = load_jsonl(args.stage4) if args.stage4 else []

    all_rows = seed_rows + stage2_rows + stage3_rows

    duplicates = report_duplicates(all_rows)
    near_duplicates = report_near_duplicates(all_rows)
    family_balance = report_family_balance(all_rows + stage4_rows)
    support_distribution = report_support_distribution(all_rows + stage4_rows)
    holdout_overlap = report_holdout_overlap(stage4_rows, all_rows)

    dump(args.outdir / "duplicate_report.json", duplicates)
    dump(args.outdir / "near_duplicate_report.json", near_duplicates)
    dump(args.outdir / "family_balance_report.json", family_balance)
    dump(args.outdir / "support_distribution_report.json", support_distribution)
    dump(args.outdir / "holdout_overlap_report.json", holdout_overlap)

    summary = {
        "duplicate_groups": len(duplicates),
        "near_duplicate_pairs": len(near_duplicates),
        "family_balance_total": family_balance["total_questions"],
        "stage4_exact_overlap": holdout_overlap["exact_overlap_count"],
        "stage4_near_overlap": holdout_overlap["near_overlap_count"],
    }
    dump(args.outdir / "stage6_summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
