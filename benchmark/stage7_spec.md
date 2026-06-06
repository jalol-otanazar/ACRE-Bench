# Stage 7: Maintenance and Regression Layer

Stage 7 is the long-term maintenance layer for ACRE-Bench.

It exists so the benchmark can evolve without losing historical comparability.

## What stage 7 does

### 1. Locked regression suite
A small stable subset of questions that must not change without a deliberate version bump.

### 2. Versioned additions
New hard questions added when a model family exposes a recurring weakness.

### 3. Trend tracking
Track whether a model that improved on recent additions still preserves performance on the locked suite.

### 4. Benchmark hygiene
Keep the benchmark from drifting into a one-off dataset that is impossible to compare across versions.

## Recommended structure

- **Locked regression suite:** 40 to 80 questions
- **Maintenance additions:** 10 to 30 new questions per release
- **Release version:** v1, v2, v3, and so on

## What goes into the locked suite

The locked suite should contain a balanced sample of:

- exact retrieval
- semantic disambiguation
- multi-hop synthesis
- structured enumeration
- refusal and unsupported-claim rejection

It should also include a few representative hard cases from the later stages so that regressions are visible early.

## What goes into maintenance additions

Maintenance additions should be driven by real failure patterns, such as:

- repeated confusion between two works
- consistent list-order mistakes
- weak refusal behavior on near-miss prompts
- translation-sensitive answer drift
- retrieval failures on a particular family of passages

## Output files

Stage 7 should produce:

- `benchmark/stage7_regression.jsonl`
- `benchmark/stage7_release_notes.json`
- optionally, `benchmark/stage7_candidates.jsonl` for future additions

## Why stage 7 matters

Without a maintenance layer, a benchmark becomes stale.

Without a locked regression suite, a benchmark becomes incomparable.

Stage 7 keeps both problems under control.
