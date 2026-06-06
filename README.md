# ACRE-Bench

**Aristotelian Corpus Retrieval Evaluation**

ACRE-Bench is a corpus-focused benchmark for testing modern RAG systems on Aristotle’s works. It is designed to expose the failure modes that matter most in production:

- retrieval on famous passages only
- semantic drift across repeated terms
- near-duplicate distractors
- multi-hop synthesis across distant works
- list and order sensitivity
- hallucinated answers to false premises
- weak source attribution

The benchmark is built to scale from a few hundred items to well over a thousand by combining a curated seed set with deterministic question expansion.

## Repository layout

- `benchmark/spec.md` - benchmark design, scoring, and category definitions
- `benchmark/corpus_manifest.yaml` - canonical Aristotle works and retrieval targets
- `benchmark/seed_questions.jsonl` - hand-authored gold seeds
- `benchmark/stage2_questions.jsonl` - expanded seed variants for the first large stress pass
- `benchmark/stage2_spec.md` - notes for the stage 2 expansion phase
- `benchmark/stage3_spec.md` - hard-mode adversarial design for the full stress pass
- `benchmark/stage4_spec.md` - final held-out evaluation protocol
- `benchmark/stage5_spec.md` - retrieval vs generation diagnostics
- `benchmark/stage6_spec.md` - audit and contamination checks
- `benchmark/eval.py` - answer and citation scorer
- `scripts/expand_questions.py` - expands the seed set into a larger evaluation file
- `scripts/build_stage3.py` - builds the adversarial stage 3 question file
- `scripts/build_stage4.py` - builds the held-out final split
- `scripts/build_stage5.py` - builds the diagnostic split placeholders
- `scripts/build_stage6.py` - builds the audit reports

## Design principle

The benchmark is not a philosophy quiz. It is a stress test for retrieval systems.

That means it separates:

- retrieval success
- ranking quality
- grounded answering
- refusal behavior
- robustness to distractors

## Recommended sizes

- **Seed set:** 50 to 120 carefully curated questions
- **Stage 2:** 200 to 400 paraphrase-expanded questions
- **Stage 3:** 600 to 900 adversarial questions with harder traps and mixed instruction styles
- **Stage 4:** 120 to 250 held-out final questions
- **Stage 5:** diagnostic splits for retrieval and generation failure analysis
- **Stage 6:** audit reports for contamination and overlap checks
- **Adversarial negatives:** at least 20% of the final set
- **False-premise items:** at least 15% of the final set

## How to use

1. Put the Aristotle corpus you want to benchmark into your RAG index.
2. Expand the seed questions into a large evaluation file.
3. Run your system on the questions.
4. Score outputs with the evaluator.

The benchmark is translation-sensitive by design, so the corpus manifest should be aligned to one edition or explicitly mapped across editions.

## Why this matters

A strong RAG system should do more than answer famous facts. It should:

- find the right passage among many plausible ones
- resist grabbing the first similar-looking chunk
- stay grounded when the question is ambiguous
- reject false premises instead of improvising
- handle corpus-specific terminology consistently
