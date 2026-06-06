#!/usr/bin/env python3
"""Build Stage 7 maintenance artifacts for ACRE-Bench.

Stage 7 is the long-term maintenance layer.
It creates:
- a locked regression suite
- a candidate pool for future hard additions
- release notes metadata for version tracking

Usage:
  python scripts/build_stage7.py \
    --seed benchmark/seed_questions.jsonl \
    --stage4 benchmark/stage4_questions.jsonl \
    --out-regression benchmark/stage7_regression.jsonl \
    --out-candidates benchmark/stage7_candidates.jsonl \
    --out-notes benchmark/stage7_release_notes.json
"""

from __future__ import annotations

import argparse
import json
import random
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

FAMILY_QUOTAS = {
    "exact_retrieval": 12,
    "semantic_disambiguation": 12,
    "multi_hop": 15,
    "structured_enumeration": 9,
    "refusal": 12,
}

VERSION = "v1.0"


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


def write_jsonl(path: Path, rows: List[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def build_regression_pool(seed_rows: List[dict], stage4_rows: List[dict], rng: random.Random) -> List[dict]:
    pool = []
    seen = set()

    # Prefer the final held-out set if available, then top up with seeds.
    source_rows = stage4_rows if stage4_rows else seed_rows
    for row in source_rows:
        qn = normalize(row.get("question", ""))
        if qn in seen:
            continue
        seen.add(qn)
        pool.append(row)

    if len(pool) < sum(FAMILY_QUOTAS.values()):
        for row in seed_rows:
            qn = normalize(row.get("question", ""))
            if qn in seen:
                continue
            seen.add(qn)
            pool.append(row)

    rng.shuffle(pool)
    return pool


def select_locked_suite(pool: List[dict], rng: random.Random) -> Tuple[List[dict], List[dict]]:
    by_family: Dict[str, List[dict]] = defaultdict(list)
    for row in pool:
        by_family[row.get("family", "unknown")].append(row)

    # Rank within each family by harder items first, then shorter questions, then id.
    for family, rows in by_family.items():
        rows.sort(key=lambda r: (
            -int(r.get("difficulty", 0)),
            len(r.get("question", "")),
            r.get("id", ""),
        ))

    locked: List[dict] = []
    used_q = set()

    for family, quota in FAMILY_QUOTAS.items():
        candidates = by_family.get(family, [])
        if not candidates:
            continue
        # Deterministic but not trivially ordered: mix in a light shuffle per family.
        rng.shuffle(candidates)
        candidates.sort(key=lambda r: (
            -int(r.get("difficulty", 0)),
            len(r.get("question", "")),
            r.get("id", ""),
        ))
        for row in candidates:
            if len([x for x in locked if x.get("family") == family]) >= quota:
                break
            qn = normalize(row.get("question", ""))
            if qn in used_q:
                continue
            item = dict(row)
            item["stage"] = 7
            item["locked"] = True
            item["benchmark_version"] = VERSION
            item["regression_family"] = family
            item["regression_id"] = f"R-{family[:3].upper()}-{len([x for x in locked if x.get('family') == family]) + 1:03d}"
            locked.append(item)
            used_q.add(qn)

    # Top up from any remaining items to reach a stable size around 60.
    target_size = sum(FAMILY_QUOTAS.values())
    if len(locked) < target_size:
        for row in pool:
            if len(locked) >= target_size:
                break
            qn = normalize(row.get("question", ""))
            if qn in used_q:
                continue
            item = dict(row)
            item["stage"] = 7
            item["locked"] = True
            item["benchmark_version"] = VERSION
            item["regression_family"] = row.get("family", "unknown")
            item["regression_id"] = f"R-MIX-{len(locked) + 1:03d}"
            locked.append(item)
            used_q.add(qn)

    candidates = [row for row in pool if normalize(row.get("question", "")) not in used_q]
    candidates.sort(key=lambda r: (-int(r.get("difficulty", 0)), r.get("family", ""), r.get("id", "")))

    return locked, candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Build ACRE-Bench Stage 7 maintenance artifacts.")
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--stage4", type=Path, default=None)
    parser.add_argument("--out-regression", type=Path, required=True)
    parser.add_argument("--out-candidates", type=Path, required=True)
    parser.add_argument("--out-notes", type=Path, required=True)
    parser.add_argument("--seed-value", type=int, default=21)
    args = parser.parse_args()

    rng = random.Random(args.seed_value)
    seed_rows = load_jsonl(args.seed)
    stage4_rows = load_jsonl(args.stage4) if args.stage4 else []

    pool = build_regression_pool(seed_rows, stage4_rows, rng)
    locked, candidates = select_locked_suite(pool, rng)

    write_jsonl(args.out_regression, locked)
    write_jsonl(args.out_candidates, candidates)

    notes = {
        "version": VERSION,
        "locked_regression_count": len(locked),
        "candidate_count": len(candidates),
        "family_quotas": FAMILY_QUOTAS,
        "source_priority": ["stage4", "seed"],
        "maintenance_policy": "Add new items only when recurring failures appear or corpus coverage changes.",
        "locked_suite_is_frozen": True,
    }
    write_json(args.out_notes, notes)

    print(json.dumps({
        "locked_regression_count": len(locked),
        "candidate_count": len(candidates),
        "version": VERSION,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
