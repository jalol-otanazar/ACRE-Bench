# Stage 6: Corpus Audit and Contamination Checks

Stage 6 is the validity layer of ACRE-Bench.

It is not another difficulty tier. It is a set of checks that make sure the benchmark is not being quietly invalidated by leakage, duplication, or corpus drift.

## What stage 6 checks

### 1. Duplicate and near-duplicate leakage

Detect whether the same question surface form, or nearly the same form, appears across stages.

### 2. Support overlap drift

Detect whether a question has been assigned to the wrong work family or changed supporting work unexpectedly.

### 3. Family balance drift

Check whether the benchmark has become skewed toward one family, such as exact retrieval or refusal.

### 4. Translation and edition sensitivity

Check whether the benchmark claims remain stable when the corpus is mapped to a different edition or translation.

### 5. Holdout contamination

Check whether the final held-out split reuses wording patterns that were already heavily exposed in earlier stages.

## Outputs

Stage 6 should produce audit artifacts such as:

- duplicate report
- family balance report
- support overlap report
- contamination risk summary

## Recommended use

Run stage 6 after generating stages 1 to 5.

If stage 6 reports serious contamination or over-concentration, revise the benchmark before using stage 4 as the final score.

## Why this matters

A benchmark can look strong while still being flawed if:

- the same prompts appear too often
- the held-out split is too similar to the training-like stages
- answer keys depend on one translation only
- the corpus assignment is inconsistent

Stage 6 exists to catch those problems before the benchmark is trusted.
