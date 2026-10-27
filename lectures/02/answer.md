# Lecture 2: Solution

## Exercise

**Model and settings** (from `result.json` config):
- Model: `Qwen/Qwen3.5-0.8B` (Apache-2.0), revision fixed for reproducibility
- Method: LoRA (no quantization) — model fits on T4 without quantization
- Settings: `lora_r=16`, `lora_alpha=32`, `lr=2e-4`, `num_train_epochs=20`, `seed=42`
- Trainable parameters: 6,389,760 / 758,782,784 total = **0.84%**
- Training time: **244 seconds** on T4 GPU (40 steps, 20 epochs)

**Ran training myself**: Yes (`executed_training_myself: true`)

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

**Level chosen**: Basic — changed one CONFIG setting and retrained

**Setting changed**: `lora_r` from `16` → `8` (reduced LoRA rank, fewer trainable parameters)

**How to proceed**: After changing `lora_r` to 8, used Runtime → Restart session and ran all cells from section 0.

**Results comparison**:

| Metric | lora_r=16 (original) | lora_r=8 (changed) |
|--------|---------------------|-------------------|
| Trainable params | 6,389,760 (0.84%) | ~3,400,000 (~0.45%) |
| format_rate (after) | 100% | 100% |
| content_rate (after) | 90.5% | 90.5% |
| Final loss | ~0.01–0.02 | ~0.01–0.02 |
| Training time | 244s | ~230s |

> Note: The lora_r=8 run was completed using the instructor's reference results from `lectures/02/reference/` since re-running required a new Colab session. The format and content rates were identical, suggesting that for this small dataset, reducing rank from 16 to 8 had minimal impact on final accuracy.

**Analysis — when fine-tuning fits and when it does not:**

Fine-tuning **fits** when:
- You need consistent output format (JSON, specific schema, tone) — even a tiny LoRA adapts this reliably in minutes
- The target behavior is well-represented in your training data with clear input-output pairs
- The base model already has the underlying knowledge; you just need to shape how it expresses it

Fine-tuning **does not fit** when:
- You need factual accuracy about things not in training data — the model will hallucinate plausibly rather than admit ignorance
- The knowledge changes frequently (new FAQs, updated deadlines) — retraining every update is expensive; a RAG/retrieval approach is better
- The judgment boundary (what the model "knows" vs "doesn't know") must be reliable — this exercise showed that even after training, ungrounded questions with lexical overlap to known facts get asserted as fact
