# ACRE-Bench Spec

## Goal

ACRE-Bench evaluates whether a RAG system can retrieve and ground answers from Aristotle’s corpus under conditions that resemble real failure modes in production.

It is designed around ten criticisms of weak benchmarks:

1. **Do not test only famous passages.**
   Include obscure, mid-tier, and highly confusable passages.

2. **Do not collapse retrieval and generation.**
   Score retrieval separately from answer quality.

3. **Do not rely only on one prompt or one phrasing.**
   Expand seed questions into many surface forms.

4. **Do not accept obvious false-premise traps only.**
   Mix obvious, plausible, and near-miss traps.

5. **Do not ignore ranking quality.**
   A correct chunk at rank 10 is not the same as rank 1.

6. **Do not assume one translation.**
   Track edition/translation metadata.

7. **Do not treat multi-hop as a synonym for “long answer.”**
   Require at least two evidence regions when the answer depends on synthesis.

8. **Do not allow noisy retrieval to go unmeasured.**
   Track the amount of irrelevant context returned.

9. **Do not make the benchmark tiny.**
   The seed set should expand into hundreds of items.

10. **Do not make the benchmark static.**
    The repo should support new seed families as the corpus grows.

## Corpus model

Use one canonical Aristotle corpus version or a mapped set of translations with explicit alignment metadata.

Recommended work groups:

- Logic: Categories, De Interpretatione, Prior Analytics, Posterior Analytics, Topics, Sophistical Refutations
- Nature: Physics, On the Heavens, On Generation and Corruption, Meteorologica
- Soul and psychology: De Anima, De Memoria, De Insomniis, On Sense and the Sensible
- Biology: History of Animals, Parts of Animals, Generation of Animals
- Ethics and politics: Nicomachean Ethics, Eudemian Ethics, Politics, Rhetoric, Poetics
- Metaphysics: Metaphysics

## Question families

### 1. Exact retrieval
Direct factual questions with one correct passage.

### 2. Semantic disambiguation
Questions that reuse a term across works and force the system to pick the right sense.

### 3. Multi-hop synthesis
Questions that require combining evidence from multiple works or separated passages.

### 4. Structured enumeration
Questions that require exact order, completeness, and no extra items.

### 5. Refusal and correction
Questions with false premises, anachronisms, or unsupported claims.

### 6. Adversarial distractors
Questions where the corpus contains near-matching passages that are not the right answer.

## Recommended scale

A robust benchmark should be built in stages:

- **Stage 1:** 50 curated seeds
- **Stage 2:** 200 to 400 generated variants
- **Stage 3:** 500 to 1000+ mixed items with adversarial negatives

## Scoring

Use a score that separates retrieval from generation.

Suggested components:

- **Recall@k** for retrieval
- **MRR** for ranking
- **Grounded answer accuracy**
- **Citation hit rate**
- **Refusal accuracy**
- **Noise penalty** for irrelevant retrieved tokens

A simple composite can be:

\[
0.30R + 0.20Rank + 0.25Grounding + 0.15Refusal + 0.10Noise
\]

where each subscore is normalized to 0-1.

## Output format

Each prediction should be one JSON object per line:

```json
{"id":"A1","answer":"Plot, Character, Diction, Thought, Spectacle, Song; Plot is the soul of tragedy.","citations":["Poetics"]}
```

## Evaluation guidance

- For list questions, require all required items.
- For refusal questions, require the system to reject the premise and not hallucinate a direct answer.
- For multi-hop questions, require support from at least two source regions or works.
- For citation checks, match by basename and normalized source label.
- For translation-specific work, cite the edition or translation in metadata.

## What makes this benchmark hard

- Aristotle repeats terms across different works.
- Many “simple” concepts change meaning by context.
- Several works contain lists that are easy to partially remember but hard to reproduce exactly.
- Some questions look answerable but are actually unsupported or false-premise traps.
