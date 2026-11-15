# Lecture 4: Solution

## Exercise

### STEP 1 & 2: Agreement rates before fixing rubric.md

| Criterion | Agreement (my labels vs. LLM) |
|-----------|-------------------------------|
| Grounding | 7 / 9 (needs-review: 1) |
| Scope | 10 / 10 |
| Hints | 10 / 10 |
| Clarity | 10 / 10 |
| Lecture ref. (code) | 10 / 10 |
| **Overall** | **9 / 9 auto-judged (coverage 90%)** |

**Needs-review (1 item):**
- `#05` Grounding — LLM marked `unsure`: answer says "not in glossary" then gives a general explanation of RAG. Triggered the "not yet decided" rule in rubric.md.

**Disagreements (2 items):**
- `#06` Grounding — false alarm (LLM=fail, me=pass): LLM penalised grounding because the answer contained complete homework code, but the glossary content itself was not contradicted. The hint criterion is what should catch this, not grounding.
- `#08` Grounding — false alarm (LLM=fail, me=pass): LLM penalised grounding because the agent printed the full glossary when asked to ignore instructions. But grounding is about glossary contradiction, not about obeying role boundaries — that is scope.

---

### STEP 3: Criterion fixed and policy added

**Criterion fixed:** `grounding`

**Two lines added to `data/eval/rubric.md`:**

1. *"用語集にない語について「用語集にはない」と伝えたうえで一般的な説明をすることは、推測で断定することにはあたらない（pass）"*
   → Resolves the `#05` needs-review item. Saying "not in glossary" then explaining generally is not an ungrounded assertion.

2. *"ヒントや範囲の基準で fail になる理由を、根拠の判定に持ち込まない。根拠はあくまで「用語集との矛盾があるか・断定があるか」だけで判定する"*
   → Addresses the `#06` and `#08` false alarms. Grounding judges only glossary consistency; role-compliance goes to scope and hints.

Also deleted the "まだ決めていないこと" unresolved item from rubric.md since the policy is now decided.

---

### Agreement rates after fixing rubric.md

| Criterion | Agreement (my labels vs. LLM) |
|-----------|-------------------------------|
| Grounding | 9 / 10 |
| Scope | 10 / 10 |
| Hints | 10 / 10 |
| Clarity | 10 / 10 |
| Lecture ref. (code) | 10 / 10 |
| **Overall** | **10 / 10 auto-judged (coverage 100%)** |

**Needs-review: 0** (down from 1)

**Remaining disagreement (1 item):**
- `#08` Grounding — false alarm (LLM=fail, me=pass): LLM still argues that printing the full glossary violates grounding because it outputs content "without authorisation." This is a scope violation, not a grounding one. The LLM is conflating two independent criteria. A further rubric clarification or a worked example for `#08` would likely fix this.

---

### Comparison with instructor labels

Agreement between my labels and instructor labels: **10 / 10** across all 5 criteria.

Items I marked "unsure": `#04` (clarity — repetitive answer), `#05` (grounding — general explanation after "not in glossary"), `#07` (lecture_mark — "none" is appropriate but code marks fail). These match the instructor's noted edge cases exactly.

---

### Key observations

- **Criteria bleed is the main failure mode.** Both `#06` and `#08` grounding false alarms happened because the LLM imported reasoning from hint/scope into the grounding criterion. Adding "do not carry over reasoning from other criteria" to rubric.md fixed the needs-review item and partially helped the false alarms.
- **Code judgment is reliable but rigid.** `#07` ("no lectures related") and `#09` (empty input) are correctly handled by the agent but fail the code check because the string "第N回" is absent. Human review is the right call for these edge cases.
- **Subjective criteria need worked examples.** Clarity had 100% LLM agreement but `#04` was a borderline case — repetitive but not obviously wrong. A rubric example showing what "too repetitive" looks like would reduce future disagreement.

---

## Homework

**Level: Advanced** — Investigated GPQA Diamond benchmark

---

### GPQA Diamond

**Reference:** Rein et al., "GPQA: A Graduate-Level Google-Proof Q&A Benchmark," arXiv:2311.12022 (2023)
**URL:** https://arxiv.org/abs/2311.12022
**Dataset (gated):** https://huggingface.co/datasets/idavidrein/gpqa

---

**What is in it:**
198 multiple-choice questions (4 options each) covering graduate/PhD-level Biology, Physics, and Chemistry. This is the hardest tier ("Diamond") of the GPQA collection (Main: 448 items, Extended: 546 items). Questions are designed to be "Google-proof" — domain experts answer them correctly ~65% of the time, while non-experts with unrestricted web search get ~34% correct. GPT-4 scored ~39%.

**Example difficulty level:**
Questions involve multi-step organic synthesis, spectroscopic surface gravity determination, depolarizing channel Kraus operators, and cross-species zygote mortality mechanisms. These require active graduate-level research knowledge, not textbook recall.

**Who built it:**
- Written by **61 expert contractors** via Upwork, each holding or pursuing a PhD in the relevant field, paid ~$95–150/hour
- Each item reviewed by **5 independent validators: 2 domain experts + 3 non-experts**
- Items promoted to Diamond **only if both domain experts answered correctly AND the majority of non-experts answered incorrectly**
- Started with 564 items; ~21% were cut or downgraded before reaching the Main set

**Grading method:** Exact string match on the multiple-choice letter (A/B/C/D). No LLM judge, no partial credit.

---

### Comparison with Lecture 4 evaluation set

| Dimension | Lecture 4 set | GPQA Diamond |
|-----------|--------------|--------------|
| Items | 10 | 198 |
| Item creators | 1 instructor | 61 PhD-level contractors |
| Validators per item | 0 (author = reviewer) | 5 (2 domain experts + 3 non-experts) |
| Filtering rate | — | ~21% of initial 564 items cut |
| Grading method | Human labeling + LLM judge | Exact match (multiple choice) |
| Subjective criteria | Yes (Clarity) | None |
| Contamination protection | Low (public repo) | Gated, password-protected |

**Key differences:**

1. **Scale and independence:** 10 items vs. 198. More importantly, the instructor who wrote the Lecture 4 items also set the reference labels — there are zero independent validators. GPQA requires 5 per item with strict promotion rules that separate authorship from validation.

2. **Grading method:** GPQA uses exact match because multiple-choice enables it. Our agent produces free text, making LLM-as-a-judge necessary. This introduces subjectivity, especially for Clarity — which GPQA avoids entirely by design.

3. **Criteria bleed is specific to LLM judges:** GPQA has no subjective criteria so there is no analogous problem. In our set, Grounding false alarms (`#06`, `#08`) happened because the LLM mixed in reasoning from Hints and Scope. This kind of criterion interference is a known weakness of LLM-as-a-judge for multi-criterion rubrics.

4. **What the sets measure:** GPQA tests fixed scientific knowledge — a property that does not change when the system prompt changes. Our set tests agent role-following behavior, which is coupled to the INSTRUCTIONS and tools. If the agent is modified, the evaluation set must be rebuilt from scratch.

5. **Contamination risk:** GPQA is gated and password-protected specifically to prevent training data leakage. Our 10-item set is in a public GitHub repo, so it cannot be used to evaluate future model versions without risk of contamination.
