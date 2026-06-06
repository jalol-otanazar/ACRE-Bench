# Stage 4: Held-Out Final Evaluation

Stage 4 is the final blind test split for ACRE-Bench.

Its job is not to make the questions harder in the same way stage 3 did. Its job is to ensure that the benchmark can be used as a real evaluation protocol.

## What stage 4 means

Stage 4 is the part you use after model selection, prompt tuning, retriever tuning, and chunking experiments are already finished.

At this point, the benchmark should behave like a frozen exam set:

- no changes to wording for tuning purposes
- no reuse of stage 1 to 3 items in the tuning loop
- no manual peeking at answers during model development
- final score reported only on the held-out split

## Why a held-out split matters

A corpus benchmark becomes much less useful if the same items are used repeatedly to tune the system.

A strong system should be able to improve on the training-like stages and still hold up on a disjoint final split that was not used to guide prompt or retrieval changes.

## Stage 4 composition

The final split should be balanced across the same families used earlier:

- exact retrieval
- semantic disambiguation
- multi-hop synthesis
- structured enumeration
- refusal and unsupported premise rejection

Recommended size:

- **120 to 250 questions** for the final blind set

Recommended composition:

- 20% exact retrieval
- 20% semantic disambiguation
- 25% multi-hop synthesis
- 15% structured enumeration
- 20% refusal and unsupported-claim questions

## Holdout rule

Stage 4 questions should be generated from a separate selection policy than the tuning stages.

Good holdout rules:

- reserve certain seed variants only for stage 4
- exclude exact question phrasings used in stages 1 to 3
- prefer fresh paraphrases and alternate distractor patterns
- keep answer keys stable, but do not recycle the surface form

## Evaluation rule

Stage 4 should be scored with the same metrics as the earlier stages, but reported separately:

- retrieval recall
- ranking quality
- grounded answer accuracy
- refusal accuracy
- citation hit rate

## What makes stage 4 different from stage 3

Stage 3 is adversarial hard mode.

Stage 4 is the final exam.

That means stage 4 should be:

- frozen
- held out
- reproducible
- used only for final reporting

## Intended outputs

The stage 4 builder should produce:

- `benchmark/stage4_questions.jsonl`
- `benchmark/stage4_scores.json` or equivalent run output

## Success criterion

If a model performs well on stages 1 to 3 but drops sharply on stage 4, the earlier stages were probably not diverse enough or the model is overfitting to benchmark phrasing.
