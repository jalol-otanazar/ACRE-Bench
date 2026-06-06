# Stage 2 Expansion

Stage 2 turns the curated Aristotle seed set into a larger benchmark that is harder to solve by memory alone.

## What stage 2 is for

The seed set is useful for checking whether the benchmark is well-formed. Stage 2 is where the benchmark starts to look like a real retrieval evaluation:

- more paraphrase variation
- more instruction drift
- more ranking pressure
- more repeated wording across questions
- more refusal traps phrased in different ways

## Current stage 2 file

- `benchmark/stage2_questions.jsonl`

This file contains deterministic variants of the 50 seed questions.

## Why stage 2 matters

A system that answers the seed set may still fail when:

- the wording changes
- the question becomes longer
- the model must ignore extra phrasing
- a false premise is hidden inside a more natural sentence
- the retriever must rank the right passage above near-duplicates

Stage 2 is meant to expose those failures before the benchmark grows into a much larger evaluation corpus.

## Intended next growth step

Stage 3 should add:

- more obscure Aristotelian passages
- near-duplicate distractors from the same work
- chapter-specific negatives
- translation-sensitive variants
- additional multi-hop questions across distant books

## Rule of thumb

If a model can solve the seed file but loses points on stage 2, the benchmark is doing its job.
