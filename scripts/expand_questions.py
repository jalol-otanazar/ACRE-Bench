#!/usr/bin/env python3
"""Expand ACRE-Bench seed questions into a larger evaluation file.

This script creates deterministic surface-form variants while preserving the
answer key and source metadata.

Example:
  python scripts/expand_questions.py --seed benchmark/seed_questions.jsonl --out benchmark/generated_questions.jsonl --copies 5
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List

PREFIXES = {
    "exact_retrieval": [
        "According to the corpus, {q}",
        "From Aristotle's corpus, {q}",
        "In the relevant Aristotelian passage, {q}",
        "Using the corpus only, {q}",
        "What does the corpus say when asked: {q}",
    ],
    "semantic_disambiguation": [
        "Across Aristotle's works, {q}",
        "In the corpus, {q}",
        "Compare the relevant Aristotelian uses: {q}",
        "Answer from the corpus only: {q}",
        "In Aristotle's terminology, {q}",
    ],
    "multi_hop": [
        "Synthesize the corpus evidence: {q}",
        "Combine the relevant Aristotelian passages: {q}",
        "Across multiple works, {q}",
        "Using more than one passage, {q}",
        "Work across the corpus to answer: {q}",
    ],
    "structured_enumeration": [
        "List precisely: {q}",
        "Give the complete ordered set for: {q}",
        "Answer with the full enumeration only: {q}",
        "Provide the exact list: {q}",
        "From the corpus, {q}",
    ],
    "refusal": [
        "According to Aristotle's corpus, {q}",
        "Does the corpus support the claim that {q}",
        "Answer strictly from the corpus: {q}",
        "Is it true that {q}",
        "Check the corpus carefully: {q}",
    ],
}

SUFFIXES = [
    "",
    " Keep the answer grounded in the corpus.",
    " Do not use outside knowledge.",
    " Cite the relevant work name.",
]


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: List[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def expand(seed: dict, copies: int, rng: random.Random) -> List[dict]:
    family = seed.get("family", "exact_retrieval")
    prefixes = PREFIXES.get(family, PREFIXES["exact_retrieval"])
    variants: List[dict] = []

    for i in range(copies):
        prefix = prefixes[i % len(prefixes)]
        suffix = SUFFIXES[i % len(SUFFIXES)]
        question = prefix.format(q=seed["question"])
        question = question.rstrip(" ?") + suffix
        variant = dict(seed)
        variant["id"] = f"{seed['id']}_v{i+1}"
        variant["question"] = question
        variant["variant_of"] = seed["id"]
        variant["variant_index"] = i + 1
        variants.append(variant)

    return variants


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand ACRE-Bench seed questions.")
    parser.add_argument("--seed", type=Path, required=True, help="Path to benchmark/seed_questions.jsonl")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    parser.add_argument("--copies", type=int, default=5, help="Number of variants per seed")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle output order")
    parser.add_argument("--seed-value", type=int, default=42, help="Random seed for shuffling")
    args = parser.parse_args()

    seeds = load_jsonl(args.seed)
    rng = random.Random(args.seed_value)
    expanded: List[dict] = []
    for seed in seeds:
        expanded.extend(expand(seed, args.copies, rng))

    if args.shuffle:
        rng.shuffle(expanded)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out, expanded)
    print(f"Wrote {len(expanded)} questions to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
