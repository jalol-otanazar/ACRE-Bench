#!/usr/bin/env python3
"""Build the Stage 3 adversarial Aristotle benchmark set.

This script turns the curated seed questions into a larger hard-mode file.
It deliberately adds:
  - extra wording noise
  - source confusion
  - wrong-work distractors
  - explicit citation pressure
  - subtle false-premise traps
  - list/order stress

Usage:
  python scripts/build_stage3.py \
    --seed benchmark/seed_questions.jsonl \
    --stage2 benchmark/stage2_questions.jsonl \
    --out benchmark/stage3_questions.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path
from typing import Dict, Iterable, List

NOISE_PREFIXES = [
    "Answer from the corpus only: ",
    "Use Aristotle's corpus, not outside memory: ",
    "Ground your answer in the cited passage: ",
    "Do not confuse this with a neighboring Aristotle passage: ",
    "Stay inside the corpus and answer exactly: ",
]

NOISE_SUFFIXES = [
    " Keep the wording exact.",
    " Do not answer from general background knowledge.",
    " Cite the work name if possible.",
    " Ignore any tempting near-match elsewhere in Aristotle.",
    " Preserve the order if the answer is a list.",
]

DISTRACTOR_CLAUSES = [
    "without drifting into a nearby work that uses similar vocabulary",
    "and do not substitute a remembered textbook summary",
    "even if another Aristotelian work sounds close",
    "while resisting a superficially similar passage",
    "without collapsing distinct Aristotelian senses into one",
]

FALSE_PREMISE_OPENERS = [
    "According to Aristotle, ",
    "In Aristotle's corpus, ",
    "Does Aristotle say that ",
    "Explain how Aristotle supports the claim that ",
    "Where in Aristotle does it say that ",
]

WRONG_WORKS = [
    "Physics",
    "Metaphysics",
    "Politics",
    "Nicomachean Ethics",
    "Poetics",
    "Rhetoric",
    "De Anima",
    "Posterior Analytics",
]


def load_jsonl(path: Path) -> List[dict]:
    rows: List[dict] = []
    if not path.exists():
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
    return text


def add_variant(base: dict, idx: int, question: str, answer: str | None = None, support: List[str] | None = None, kind: str | None = None) -> dict:
    item = dict(base)
    item["id"] = f"{base['id']}_S3{idx:02d}"
    item["question"] = question
    if answer is not None:
        item["answer"] = answer
    if support is not None:
        item["supporting_works"] = support
    item["variant_of"] = base["id"]
    item["stage"] = 3
    item["stage3_kind"] = kind or base.get("family", "unknown")
    item["variant_index"] = idx
    return item


def list_items(answer: str) -> List[str]:
    return [part.strip() for part in answer.split(";") if part.strip()]


def make_paraphrase(q: str, prefix: str, suffix: str) -> str:
    q = q.rstrip(" ?.")
    return f"{prefix}{q}{suffix}"


def build_variants(seed: dict, idx_start: int, rng: random.Random) -> List[dict]:
    q = seed["question"]
    a = seed["answer"]
    family = seed.get("family", "exact_retrieval")
    support = seed.get("supporting_works", [])
    items: List[dict] = []
    idx = idx_start

    if family == "exact_retrieval":
        templates = [
            lambda: make_paraphrase(q, NOISE_PREFIXES[0], NOISE_SUFFIXES[0]),
            lambda: make_paraphrase(q, NOISE_PREFIXES[1], NOISE_SUFFIXES[1]),
            lambda: make_paraphrase(q, NOISE_PREFIXES[2], NOISE_SUFFIXES[2]),
            lambda: make_paraphrase(q, NOISE_PREFIXES[3], f" {rng.choice(DISTRACTOR_CLAUSES)}."),
            lambda: f"In the same Aristotelian work, what is the exact answer to: {q.rstrip('?')}?",
            lambda: f"Give the exact answer from the corpus for: {q.rstrip('?')}.",
        ]
        for make in templates:
            items.append(add_variant(seed, idx, make(), a, support, "exact_hard"))
            idx += 1

    elif family == "semantic_disambiguation":
        templates = [
            lambda: f"In Aristotle's corpus, answer the following without collapsing distinct senses: {q.rstrip('?')}.",
            lambda: f"Compare the relevant Aristotelian uses and answer exactly: {q.rstrip('?')}.",
            lambda: f"Answer from the corpus only, and do not confuse this with the neighboring use in another work: {q.rstrip('?')}.",
            lambda: f"Which Aristotelian sense is required here? {q.rstrip('?')}.",
            lambda: f"Ground the answer in the cited passage and keep the distinction sharp: {q.rstrip('?')}.",
            lambda: f"If a near-match exists elsewhere in Aristotle, ignore it and answer: {q.rstrip('?')}.",
        ]
        for make in templates:
            items.append(add_variant(seed, idx, make(), a, support, "semantic_hard"))
            idx += 1

    elif family == "multi_hop":
        templates = [
            lambda: f"Synthesize the Aristotelian evidence rather than quoting only one passage: {q.rstrip('?')}.",
            lambda: f"Combine the relevant works and answer with the joint conclusion: {q.rstrip('?')}.",
            lambda: f"Use more than one Aristotelian text if needed: {q.rstrip('?')}.",
            lambda: f"Resolve this across the corpus, not from a single remembered line: {q.rstrip('?')}.",
            lambda: f"Answer only after connecting the separate passages that matter: {q.rstrip('?')}.",
            lambda: f"Give the synthesis and keep the cross-work relationship explicit: {q.rstrip('?')}.",
            lambda: f"Do not stop at the most obvious source; trace the answer across Aristotle: {q.rstrip('?')}.",
            lambda: f"Work across the corpus and preserve the underlying distinction: {q.rstrip('?')}.",
        ]
        for make in templates:
            items.append(add_variant(seed, idx, make(), a, support, "multi_hop_hard"))
            idx += 1

    elif family == "structured_enumeration":
        templates = [
            lambda: f"List the items in the exact order Aristotle gives them, and keep the answer complete: {q.rstrip('?')}.",
            lambda: f"Provide the full enumeration with no omissions or substitutions: {q.rstrip('?')}.",
            lambda: f"Answer with the ordered list only, based on the corpus: {q.rstrip('?')}.",
            lambda: f"Do not paraphrase away the order. {q.rstrip('?')}.",
            lambda: f"Give the exact sequence from Aristotle's text: {q.rstrip('?')}.",
            lambda: f"If the answer is a list, preserve all members and the order: {q.rstrip('?')}.",
        ]
        for make in templates:
            items.append(add_variant(seed, idx, make(), a, support, "structured_hard"))
            idx += 1

    elif family == "refusal":
        false_premise_subject = rng.choice([
            "the Categorical Imperative",
            "the Roman Republic",
            "the nine circles of hell",
            "Bentham's utilitarian calculus",
            "the master-slave dialectic",
            "quantum wave memory",
            "Stoic ataraxia",
            "Darwinian natural selection",
        ])
        templates = [
            lambda: f"According to Aristotle's corpus, explain {q.rstrip('?')}.",
            lambda: f"Does Aristotle actually support the claim that {q.rstrip('?')}? Answer strictly from the corpus.",
            lambda: f"Where in Aristotle would one find support for {q.rstrip('?')}?", 
            lambda: f"Give the Aristotelian passage that proves {q.rstrip('?')}.",
            lambda: f"Answer only from the corpus and reject any unsupported premise: {q.rstrip('?')}.",
            lambda: f"Is this Aristotelian claim actually stated in the corpus: {q.rstrip('?')}?", 
            lambda: f"Explain the text's treatment of {q.rstrip('?')} if it exists.",
            lambda: f"In Aristotle, how is {q.rstrip('?')} established?", 
        ]
        refined_answer = a
        for make in templates:
            items.append(add_variant(seed, idx, make(), refined_answer, support, "refusal_hard"))
            idx += 1

    return items


def build_false_premise_traps(seed: dict, idx_start: int, rng: random.Random) -> List[dict]:
    base_question = seed["question"].rstrip("?")
    support = seed.get("supporting_works", [])
    answer = seed["answer"]
    traps: List[dict] = []
    idx = idx_start
    for opener in FALSE_PREMISE_OPENERS:
        wrong_work = rng.choice(WRONG_WORKS)
        question = f"{opener}{base_question} in {wrong_work}?"
        traps.append(add_variant(seed, idx, question, answer if seed.get("family") != "refusal" else answer, support, "trap"))
        idx += 1
    return traps


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Stage 3 ACRE-Bench question set.")
    parser.add_argument("--seed", type=Path, required=True, help="Path to benchmark/seed_questions.jsonl")
    parser.add_argument("--stage2", type=Path, required=False, help="Path to benchmark/stage2_questions.jsonl")
    parser.add_argument("--out", type=Path, required=True, help="Output JSONL path")
    parser.add_argument("--copies", type=int, default=6, help="Variants per seed family")
    parser.add_argument("--traps-per-seed", type=int, default=2, help="Extra false-premise traps per seed")
    parser.add_argument("--shuffle", action="store_true", help="Shuffle the final output")
    parser.add_argument("--seed-value", type=int, default=7, help="Random seed")
    args = parser.parse_args()

    rng = random.Random(args.seed_value)
    seeds = load_jsonl(args.seed)
    stage2 = load_jsonl(args.stage2) if args.stage2 else []

    output: List[dict] = []
    used_questions = set()

    for seed in seeds:
        variants = build_variants(seed, 1, rng)
        if args.copies:
            variants = variants[: args.copies]
        for variant in variants:
            key = normalize(variant["question"])
            if key not in used_questions:
                output.append(variant)
                used_questions.add(key)

        trap_seed = dict(seed)
        trap_seed["family"] = "refusal"
        trap_variants = build_false_premise_traps(trap_seed, 100, rng)[: args.traps_per_seed]
        for variant in trap_variants:
            key = normalize(variant["question"])
            if key not in used_questions:
                output.append(variant)
                used_questions.add(key)

    # Use stage2 as a source of extra phrasing pressure: convert the first batch
    # into a second adversarial pass with more explicit instruction clutter.
    for row in stage2[: max(0, len(seeds) * 2)]:
        q = row["question"].rstrip("?")
        noisy = f"{rng.choice(NOISE_PREFIXES)}{q}{rng.choice(NOISE_SUFFIXES)}"
        mutated = dict(row)
        mutated["id"] = f"{row['id']}_X3"
        mutated["question"] = noisy
        mutated["stage"] = 3
        mutated["stage3_kind"] = "stage2_adversarial"
        mutated["variant_of"] = row["id"]
        key = normalize(noisy)
        if key not in used_questions:
            output.append(mutated)
            used_questions.add(key)

    if args.shuffle:
        rng.shuffle(output)

    write_jsonl(args.out, output)
    print(f"Wrote {len(output)} stage 3 questions to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
