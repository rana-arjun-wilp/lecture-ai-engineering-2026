# Lecture 5: Solution

## Exercise

**Model**: `gemini-3.5-flash-lite`
**Comparison question**: "In Lecture 2, what does LoRA freeze and what does it train? What does QLoRA add?"
**Materials scope**: Full text covers all 9 documents (438 pages); Vector/Tree/Graph cover Lectures 1–3 main (214 pages)

---

### Results — Single-page question (LoRA/QLoRA)

| Method | Correct / Citations | Time (s) | Input / Output tokens | Requests | Est. cost (USD) |
|--------|-------------------|----------|-----------------------|----------|-----------------|
| Full text | Correct / Lec.2 p.51–52 | 6.42 | 117,023 / 284 | 1 | $0.035817 |
| Vector search | Correct / Lec.2 p.51, 52 | 8.55 | 3,025 / 190 | 2 | $0.001382 |
| Tree | Correct / Lec.2 p.51, 52 | 21.01 | 13,694 / 419 | 6 | $0.005156 |
| Graph | Correct / Lec.2 p.51, 52 | 8.78 | 5,769 / 211 | 2 | $0.002258 |

---

### Results — Multi-page question

Question: "What is the difference between context compaction and cross-session memory? Do all daily notes become long-term memory?"

| Method | Correct / Citations | Time (s) | Input / Output tokens | Requests | Est. cost (USD) |
|--------|-------------------|----------|-----------------------|----------|-----------------|
| Vector search | Correct / Lec.3 p.40 | 12.17 | 6,608 / 377 | 3 | $0.002925 |

The agent issued two separate `search_materials` calls. Both retrieved the right page (lec03-main-p040).

---

### Results — Not-in-materials question

Question: "What is the average response time and accuracy of the RAG system we built in this course?"

| Method | Result | Time (s) | Input / Output tokens | Cost (USD) |
|--------|--------|----------|-----------------------|------------|
| Vector search | Correctly said "not in materials" | 7.51 | 7,869 / 183 | $0.002818 |

Searched twice, found only loosely related pages, correctly refused to fabricate specific metrics.

---

### Raw retrieval check (STEP 2)

`uv run python -m app.retrieval "LoRA QLoRA difference"` — Result 1: `lec02-main-p052` (PDF p.52) — the exact supporting page, found on the first hit.

---

### Trace observations

**Vector search**: 1 `search_materials` call → 5 pages returned, p.52 as top hit. Requests=2. Fastest overall for single-page questions.

**Tree**: 6 `browse_tree` calls — root → lec02-main → section lec02-main-s045 → candidate list → fetched p.051 and p.052 full text. Expensive (21s, 6 requests) but completely transparent TOC path.

**Graph**: 1 `search_graph` call → seeds: p.052, expanded: p.051 via adjacent page edge. Requests=2. Slightly more input tokens than vector (5,769 vs 3,025) but covers neighboring pages automatically.

---

### Insufficient retrieval / unused evidence

- **Tree** fetched p.051 (PEFT context) alongside p.052 (LoRA/QLoRA), but the answer only cited p.52. Broader context was retrieved but partially unused.
- **Full text**: 117,023 tokens vs 3,025 for vector — 26× more input tokens for the same answer quality.

---

### Preferred method and reasoning

- **Single-page factual questions**: Vector search — fastest (8.5s), cheapest ($0.001), same accuracy.
- **Cross-chapter questions**: Graph (with re-ranking from homework) — expands to adjacent pages without extra queries.
- **Debugging/exploratory**: Tree — the TOC trace shows exactly which path was taken.

**Comparison limit**: Only one run per method. Rate limiting (503 errors) interrupted graph runs. Full text used wider scope than other methods — not a fully controlled comparison.

---

### Key observations

1. Full text is correct but 26× more expensive — token cost justifies RAG even when full text works.
2. Tree is the most transparent but slowest — 6 model calls vs. 2 for vector/graph.
3. Graph automatically surfaces adjacent pages without multiple queries — structural advantage for multi-page questions.
4. "Not in materials" detection worked correctly on a question with no supporting page.

---

## Homework

**Level: Advanced** — Improved Graph retrieval with query-term re-ranking

---

### Problem with the original Graph

The original `search_graph` ranks expanded candidates by hop distance and term-node frequency. This means a structurally adjacent page with no mention of the queried terms can outrank a more relevant page from another section. For cross-chapter questions, structurally close pages in one chapter can crowd out relevant pages from another chapter.

### What was changed

**File**: `app/retrieval.py`

Added `_query_term_overlap(query, page)` — counts how many 2+-character query tokens appear in a page's title or content. Then re-ranked expanded candidates by:
1. Query-term overlap (descending)
2. Hop distance (ascending, for ties)

Seeds (direct vector search hits) were not re-ranked.

```python
def _query_term_overlap(query: str, page: dict) -> int:
    tokens = {t.lower() for t in re.split(r"[\s　，、。、\-/()]+", query) if len(t) >= 2}
    text = (page.get("title", "") + " " + page.get("content", "")).lower()
    return sum(1 for t in tokens if t in text)

# Re-rank expanded candidates before returning:
reranked = sorted(raw_expanded, key=lambda p: (-_query_term_overlap(query, p), p["hops"]))
```

### Target question

"What is the evaluation-and-improvement cycle, and how does it connect to agent tool use in Lecture 3?"
(Cross-chapter: Lecture 1 concepts + Lecture 3 tool mechanics)

**Supporting pages confirmed in advance:**
- `lec01-main-p035` — evaluation-and-improvement cycle definition
- `lec03-main-p012` — agent loop / tool use mechanics
- `lec03-main-p020` — goal-mode / measurable completion conditions

### Results

| Method | Evidence pages | Time (s) | Input / Output tokens | Requests | Cost (USD) |
|--------|---------------|----------|-----------------------|----------|------------|
| Basic RAG (vector) | lec03-main-p012, lec01-main-p035 | 14.96 | 6,131 / 710 | 3 | $0.003614 |
| Improved Graph | lec03-main-p012, lec03-main-p020, lec01 (2nd call) | 8.96 | 13,719 / 515 | 3 | $0.003758 |

**Basic RAG**: Agent issued 2 search calls. Retrieved lec03-main-p012 (agent loop) and lec01-main-p035 (evaluation cycle). Answer correctly covered both topics with citations from both lectures.

**Improved Graph**: First `search_graph` returned lec03-main-p012 as seed. Re-ranking surfaced lec03-main-p020 as top expanded candidate because it contains "評価" and "測る" from the query. Agent issued a second call and found lec01-main-p035. Final answer cited lec03-main-p020's measurability content — not cited in the basic RAG run.

### Improved example

Re-ranking promoted `lec03-main-p020` (measurable completion conditions) above structurally adjacent pages that only share a "next_page" edge. The model used this page to explain how goal-mode measurability connects to the evaluation cycle — a nuance the basic RAG answer missed.

### Remaining failures and limits

- **Higher input token cost**: 13,719 vs 6,131 for the cross-chapter question. For queries where extra pages add noise, this increases cost without improving accuracy.
- **Text-matching only**: The re-ranker favors pages that literally contain query words. For paraphrase-heavy queries, term overlap is low even for relevant pages. Embedding-based re-ranking would be more robust but requires an extra API call per candidate.
- **Still requires two graph calls** for cross-lecture questions — graph traversal stays within the seed page's lecture, so Lecture 1 and Lecture 3 content still need separate queries.

### Decision on adoption

Worth keeping for technical-term queries (LoRA, QLoRA, evaluation, agent loop) where term overlap is a reliable relevance signal. For general conversational queries it adds little. A `GRAPH_RERANK` config flag would let it be toggled per use case.
