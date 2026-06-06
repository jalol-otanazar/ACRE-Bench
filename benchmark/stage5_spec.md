# Stage 5: Retrieval vs Generation Diagnostics

Stage 5 exists to answer a question the earlier stages cannot:

When a model fails, was it a retrieval failure or a generation failure?

## Goal

Separate the RAG pipeline into independent components.

Stage 1-4 measure end-to-end performance.
Stage 5 measures where the failure originates.

## Diagnostic Tracks

### Track A: Retrieval Only

Given a question, the system must return the correct passage, chunk, or source location.

Scoring:
- Recall@1
- Recall@5
- MRR
- nDCG

### Track B: Generation Only

The gold passage is provided.

The model must answer using only the supplied evidence.

Scoring:
- Answer accuracy
- Citation accuracy
- Refusal accuracy

### Track C: Evidence Selection

The system receives multiple candidate passages.
Only one (or a small subset) is correct.

Measure:
- Evidence ranking
- Distractor resistance
- Source confusion rate

### Track D: Counterfactual Evidence

The model is intentionally given misleading but plausible passages.

Measure:
- Grounding robustness
- Hallucination rate
- Unsupported inference rate

## Recommended Size

- Retrieval-only: 200-500 items
- Generation-only: 200-500 items
- Evidence selection: 100-300 items
- Counterfactual evidence: 100-300 items

## Why Stage 5 Matters

A model can fail because:

- retrieval missed the right passage
- reranking selected the wrong passage
- generation ignored retrieved evidence
- generation hallucinated despite correct evidence

Stage 5 identifies which component caused the failure.
