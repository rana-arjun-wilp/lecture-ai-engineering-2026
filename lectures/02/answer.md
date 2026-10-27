# Lecture 2: Solution

## Exercise

**Model and settings** (from `result.json` config):
- Model: `Qwen/Qwen3.5-0.8B` (Apache-2.0), revision fixed for reproducibility
- Method: LoRA (no quantization) — model fits on T4 without quantization
- Settings: `lora_r=16`, `lora_alpha=32`, `lr=2e-4`, `num_train_epochs=20`, `seed=42`
- Trainable parameters: 6,389,760 / 758,782,784 total = **0.84%**
- Training time: **244 seconds** on T4 GPU (40 steps, 20 epochs)

**Ran training myself**: Yes (`executed_training_myself: true`)

> All three runs (Exercise, Basic homework, Advanced homework) were executed on T4 GPU in Google Colab.

---

### Before vs. After Training

| Metric | Before Training | After Training |
|--------|----------------|----------------|
| format_rate | 9.5% (2/21) | **100%** (21/21) |
| content_rate | 0.0% (0/21) | **90.5%** (19/21) |
| both_rate | 0.0% | **90.5%** |
| eval time | 20.7s | 41.4s |

**Before training**: Almost all 21 outputs were missing the `needs_review` key (`missing_key` error). Only 2 questions produced valid JSON — both had `needs_review: false` as a string value so content still failed. The model understood what to answer but ignored the required format.

**After training**: Format compliance jumped to 100%. The model returned exact FAQ text almost verbatim for grounded questions, with correct `needs_review: false`. Content accuracy reached 90.5% (19/21 correct).

---

### Regressions

None — no questions that passed before training failed after. (`regressed: []`)

---

### Remaining Failures After Training (2 questions)

**Q: 成績はいつ出ますか (When will grades be released?)** — `needs_review` should be `true` (not in FAQ), but the model answered with the submission *deadline* date (`9 月 30 日 23:59`) and `needs_review: false`. This is the **"assert using a different FAQ item"** failure type — the model matched the word "deadline" from the question to the deadline FAQ entry and answered as fact.

**Q: オフィスアワーは事前予約が必要ですか (Do office hours require advance booking?)** — `needs_review` should be `true` (not in FAQ), but the model returned office hours schedule (`火曜 17:00〜18:00`) with `needs_review: false`. Same failure type — matched "office hours" to the office hours FAQ entry and answered as fact instead of flagging for review.

Both failures are the same type: **ungrounded question answered as fact by matching a similar FAQ item**.

---

### Knowledge Questions (Section 6)

| Question | In FAQ? | Before Training | After Training |
|----------|---------|----------------|----------------|
| この講座の最終課題の締切はいつですか (Final assignment deadline) | No | format_error | **asserted** (returned submission deadline as fact) |
| 担当教員の名前は何ですか (Instructor's name) | No | format_error | **needs_review** ✓ |
| 次回の講義のテーマは何ですか (Next lecture topic) | No | format_error | **needs_review** ✓ |
| 課題の提出期限はいつですか (Assignment deadline — control) | Yes | format_error | **asserted** ✓ (correct for this one) |

**Key insight**: Before training, all 4 were `format_error` — the model couldn't produce valid JSON at all. After training, 2 of 3 out-of-FAQ questions correctly returned `needs_review: true`. However, "final assignment deadline" was incorrectly asserted as fact — the model confused it with the submission deadline already in the FAQ. Training did not reliably teach the model to distinguish between "I know this from the FAQ" vs "I'm guessing from similar content."

---

### What Training Changed vs. What It Did Not

**Changed:**
- Format compliance: 9.5% → 100%. LoRA very effectively taught the output format (`{"answer": ..., "needs_review": ...}`) in just 244 seconds.
- Answers for grounded questions now quote FAQ text almost verbatim and are consistently correct.

**Did not change:**
- Judgment about unknown questions is not guaranteed. 2/6 ungrounded questions were still asserted as fact by matching similar FAQ items. The model learned the *pattern* of answering from the FAQ but not the *boundary* of when the FAQ actually supports the answer.
- This matches the core lesson: fine-tuning can teach format and style reliably, but it cannot guarantee correct knowledge-grounding behavior.

---

### Advanced: 4-bit Quantization (Section 8)

Loaded the same model in 4-bit (NF4) without training and compared against the 32-bit pre-training baseline:

| Setting | Weight memory | format_rate | content_rate |
|---------|--------------|-------------|--------------|
| 32-bit (before training) | 3.01 GB | 9.5% | 0.0% |
| 4-bit (no training) | **0.76 GB** | 66.7% | 33.3% |

The 4-bit model used only 25% of the memory. Interestingly, format compliance improved without any training (66.7% vs 9.5%), suggesting quantization changed the model's behavior in unpredictable ways. One notable failure: `needs_review` was returned as the string `"false"` instead of boolean `false` — causing a `wrong_type` format error. Results had no consistent direction of improvement.

---

## Homework

**Levels completed**: Basic and Advanced

---

### Basic Homework — Changed `lora_r` from 16 to 8

**What was changed**: `lora_r` reduced from 16 to 8 in CONFIG (fewer trainable parameters). All other settings kept identical. New Colab session used (Runtime → Restart) to avoid interference from previous run. Results saved as `result_r8.json`.

| Metric | lora_r=16 (original) | lora_r=8 (Basic homework) |
|--------|---------------------|--------------------------|
| format_rate before | 9.5% | 9.5% |
| format_rate after | **100%** | **100%** |
| content_rate before | 0.0% | 0.0% |
| content_rate after | **90.5%** (19/21) | **85.7%** (18/21) |
| Training time | 244s | 20.5s (before eval) / 42.1s (after eval) |
| Regressions | 0 | 0 |

**Observation**: Halving `lora_r` from 16 to 8 had a small but real impact — content accuracy dropped slightly from 90.5% to 85.7% (1 additional failure). Format compliance remained perfect at 100% for both. This suggests that for this small FAQ dataset, `lora_r=16` is already near-optimal and reducing rank costs a small amount of content accuracy while saving ~half the trainable parameters.

---

### Advanced Homework — Trained on Course Glossary instead of FAQ

**What was done**: Used `scripts/make_sft_dataset.py` to generate Q&A data from `data/glossary.json` (58 terms × 2 question templates = 116 records). Trained the same model with this data instead of the fictional FAQ. Results saved as `result_glossary.json`.

The evaluation still used the original FAQ-based test set (21 questions) to allow direct comparison. This deliberately tests whether glossary-trained knowledge transfers to FAQ-style answering.

| Metric | FAQ training (exercise) | Glossary training (Advanced) |
|--------|------------------------|------------------------------|
| format_rate before | 9.5% | 9.5% |
| format_rate after | **100%** | **4.8%** (1/21) |
| content_rate before | 0.0% | 0.0% |
| content_rate after | **90.5%** | **0.0%** |
| Training time | 244s | ~similar |
| Regressions | 0 | 0 |

**Key finding**: Training on the glossary data nearly **destroyed** the model's ability to answer FAQ questions in the correct format. format_rate dropped from 100% (FAQ-trained) to just 4.8% — worse than before any training. The model learned to output free-text definitions in the style of the glossary (e.g. `"AIE2026の火曜講座は..."`) instead of JSON, and completely abandoned the `{"answer": ..., "needs_review": ...}` format.

**Knowledge questions after glossary training**: All 4 returned `format_error` — the model had overwritten its FAQ-answering behavior with glossary-definition behavior.

**This directly demonstrates the core lesson of fine-tuning vs retrieval**:

Fine-tuning **fits** when:
- Output format and style are consistent across all training data
- The training domain closely matches the evaluation domain
- Knowledge is stable and doesn't need frequent updates

Fine-tuning **does not fit** when:
- Training data and evaluation tasks have different output formats — the model overwrites one style with another
- You need to cover multiple knowledge domains simultaneously without catastrophic forgetting
- The knowledge changes frequently — a retrieval system (RAG) querying the glossary at inference time would handle new terms without retraining, while the fine-tuned model would require a full new training run for each update

**Comparison — fine-tuning vs glossary search**:
- Fine-tuning on glossary: fast inference, no external lookup needed, but format degrades badly when the training data structure differs from the evaluation task; also becomes stale as the glossary grows
- Searching the glossary at inference time (RAG): always up-to-date, no format conflict, but requires a retrieval component and adds latency
