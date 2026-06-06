#!/usr/bin/env python3
"""Build the Stage 4 held-out Aristotle evaluation split.

Stage 4 is the final blind test split. It should not reuse question wording
from stages 1-3 if the same surface form can be avoided.

This script is intentionally conservative:
- it prefers fresh paraphrases
- it keeps the answer key stable
- it filters duplicate surface forms across earlier stages
- it emits a compact final set for blind scoring

Usage:
  python scripts/build_stage4.py \
    --seed benchmark/seed_questions.jsonl \
    --stage2 benchmark/stage2_questions.jsonl \
    --stage3 benchmark/stage3_questions.jsonl \
    --out benchmark/stage4_questions.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, Iterable, List

INTRO_TEMPLATES = {
    "exact_retrieval": [
        "Using the frozen final split, answer: {q}",
        "For the held-out evaluation set, {q}",
        "In the blind stage 4 file, {q}",
        "From Aristotle only, with no outside knowledge: {q}",
    ],
    "semantic_disambiguation": [
        "For the final held-out split, resolve the Aristotelian sense in: {q}",
        "In the blind evaluation set, distinguish the relevant Aristotelian usage: {q}",
        "Using Aristotle's corpus only, answer this disambiguation item: {q}",
        "For stage 4, keep the Aristotelian distinction sharp: {q}",
    ],
    "multi_hop": [
        "In the final blind split, synthesize the relevant Aristotelian passages: {q}",
        "For stage 4, answer only after combining the needed works: {q}",
        "Across the held-out corpus, resolve: {q}",
        "Use the final split to connect the passages that matter: {q}",
    ],
    "structured_enumeration": [
        "In the held-out final split, provide the exact ordered list for: {q}",
        "For stage 4, list the items exactly and in order: {q}",
        "Using Aristotle only, give the complete enumeration: {q}",
        "In the blind test set, preserve the list order for: {q}",
    ],
    "refusal": [
        "In the final blind split, answer strictly from Aristotle's corpus: {q}",
        "For stage 4, reject any unsupported premise in: {q}",
        "Using only the corpus, evaluate this claim: {q}",
        "In the held-out set, refuse the false premise if needed: {q}",
    ],
}

SUFFIXES = [
    "",
    " Keep the answer exact.",
    " Do not use outside memory.",
    " Cite the work name if available.",
]

EXTRA_CLAUSES = [
    "and do not drift to a nearby passage",
    "while preserving list order if a list is required",
    "without collapsing distinct Aristotelian senses",
    "and do not answer from general philosophical memory",
    "while staying inside the held-out corpus",
]


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


def normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^a-z0-9 ]+", "", text)
    return text.strip()


def make_question(seed: dict, rng: random.Random, flavor_index: int) -> str:
    family = seed.get("family", "exact_retrieval")
    q = seed["question"].rstrip("?.")
    intro = INTRO_TEMPLATES.get(family, INTRO_TEMPLATES["exact_retrieval"])
    prefix = intro[flavor_index % len(intro)]
    suffix = SUFFIXES[flavor_index % len(SUFFIXES)]
    clause = EXTRA_CLAUSES[flavor_index % len(EXTRA_CLAUSES)]

    if family == "refusal":
        return f"{prefix.format(q=q)} {clause}{suffix}".strip()
    if family == "structured_enumeration":
        return f"{prefix.format(q=q)} {clause}{suffix}".strip()
    if family == "multi_hop":
        return f"{prefix.format(q=q)} {clause}{suffix}".strip()
    if family == "semantic_disambiguation":
        return f"{prefix.format(q=q)} {clause}{suffix}".strip()
    return f"{prefix.format(q=q)} {clause}{suffix}".strip()


def collect_seen_questions(stages: Iterable[List[dict]]) -> set[str]:
    seen: set[str] = set()
    for rows in stages:
        for row in rows:
            q = row.get("question")
            if q:
                seen.add(normalize(q))
    return seen


def build_stage4(seed_rows: List[dict], seen_questions: set[str], target_size: int, rng: random.Random) -> List[dict]:
    by_family: Dict[str, List[dict]] = {}
    for row in seed_rows:
        by_family.setdefault(row.get("family", "exact_retrieval"), []).append(row)

    family_order = [
        ("exact_retrieval", 0.20),
        ("semantic_disambiguation", 0.20),
        ("multi_hop", 0.25),
        ("structured_enumeration", 0.15),
        ("refusal", 0.20),
    ]

    output: List[dict] = []
    counters: Dict[str, int] = {fam: 0 for fam, _ in family_order}
    desired = {fam: max(1, round(target_size * share)) for fam, share in family_order}

    # Shuffle seeds within each family so the split is reproducible but not ordered by id.
    for fam in by_family:
        rng.shuffle(by_family[fam])

    # Keep generating until quotas are filled or we run out of fresh variants.
    progress = True
    flavor_index = 0
    while progress and len(output) < target_size:
        progress = False
        for family, _share in family_order:
            if len(output) >= target_size:
                break
            if counters[family] >= desired[family]:
                continue
            candidates = by_family.get(family, [])
            if not candidates:
                continue
            for seed in candidates:
                question = make_question(seed, rng, flavor_index)
                flavor_index += 1
                norm_q = normalize(question)
                if norm_q in seen_questions:
                    continue
                item = dict(seed)
                item["id"] = f"S4_{seed['id']}_{counters[family] + 1:03d}"
                item["question"] = question
                item["stage"] = 4
                item["stage4_kind"] = "heldout_final"
                item["variant_of"] = seed["id"]
                item["answer_type"] = seed.get("answer_type", "short")
                output.append(item)
                seen_questions.add(norm_q)
                counters[family] += 1
                progress = True
                break

    # If quotas were not met because of duplicate filtering, top up from any family.
    if len(output) < target_size:
        for family, rows in by_family.items():
            for seed in rows:
                if len(output) >= target_size:
                    break
                question = make_question(seed, rng, flavor_index)
                flavor_index += 1
                norm_q = normalize(question)
                if norm_q in seen_questions:
                    continue
                item = dict(seed)
                item["id"] = f"S4_{seed['id']}_{len(output) + 1:03d}"
                item["question"] = question
                item["stage"] = 4
                item["stage4_kind"] = "heldout_final"
                item["variant_of"] = seed["id"]
                item["answer_type"] = seed.get("answer_type", "short")
                output.append(item)
                seen_questions.add(norm_q)

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the ACRE-Bench stage 4 held-out set.")
    parser.add_argument("--seed", type=Path, required=True, help="Path to benchmark/seed_questions.jsonl")
    parser.add_argument("--stage2", type=Path, default=None, help="Path to benchmark/stage2_questions.jsonl")
    parser.add_argument("--stage3", type=Path, default=None, help="Path to benchmark/stage3_questions.jsonl")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    parser.add_argument("--target-size", type=int, default=160, help="Target size for the held-out split")
    parser.add_argument("--seed-value", type=int, default=13, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed_value)
    seed_rows = load_jsonl(args.seed)
    stage2_rows = load_jsonl(args.stage2) if args.stage2 else []
    stage3_rows = load_jsonl(args.stage3) if args.stage3 else []

    seen_questions = collect_seen_questions([seed_rows, stage2_rows, stage3_rows])
    stage4_rows = build_stage4(seed_rows, seen_questions, args.target_size, rng)

    write_jsonl(args.out, stage4_rows)
    print(f"Wrote {len(stage4_rows)} held-out stage 4 questions to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
