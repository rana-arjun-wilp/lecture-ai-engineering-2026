# Lecture 3: Solution

## Exercise

**Difference between Lecture 1 (plain LLM) and the agent:**

| | Lecture 1: `app.ask` | Lecture 3: `app.agent` |
|---|---|---|
| Question: "3 levels of homework" | Admitted it didn't know (English) or hallucinated plausible but wrong answer (Japanese) | Searched the glossary, returned the correct definition: Basic / Implementation / Advanced |
| Source of answer | Model's training data only | Glossary looked up via `search_glossary` tool |
| LLM calls | 1 | 2 (one to decide tool call, one to form answer) |
| Answer ends with | Nothing | "Lecture N" citation |

---

**Tool calls seen with `--trace` (question: "What is the difference between LoRA and QLoRA?"):**

```
[tool call]   search_glossary({'query': 'LoRA'})
[tool call]   search_glossary({'query': 'QLoRA'})
[tool return] search_glossary -> [{"term": "LoRA", "lecture": 2, ...}]
[tool return] search_glossary -> [{"term": "QLoRA", "lecture": 2, ...}]
[usage] RunUsage(requests=2, tool_calls=2)
```

The model searched each term separately because the docstring says "Put only one term to look up in query".

---

**LLM calls per question:** `requests=2` — one call to decide which tools to use and with what arguments, one call to compose the final answer from the tool results.

---

**Tool added — `make_quiz`:**

Registered in `app/agent.py` with `agent.tool_plain(tools.make_quiz)`.

Docstring written in `app/tools.py`:
```
Pick one term from the given lecture and return a review question and its answer.

Use when asked for review questions, such as "Give me a review question for Lecture 2"
or "Quiz me on Lecture 1". Picks one term at random from the glossary for the given
lecture number and returns a question asking what the term means along with its answer.
```

Confirmed working with `--list-tools` (shows `make_quiz`) and `--trace`:
```
[tool call]   make_quiz({'lecture': 2})
[tool return] make_quiz -> {"question": "What does \"QLoRA\" mean?", "answer": "..."}
[usage] RunUsage(requests=2, tool_calls=1)
```

---

## Homework

**Levels completed:** Basic, Implementation, and Advanced

---

### Basic — Rewrote INSTRUCTIONS and compared `--trace` output

**What was changed:** Removed the line `"Always check the glossary with search_glossary before answering"` from `INSTRUCTIONS`.

**Result with original INSTRUCTIONS** (question: "What is LoRA?"):
```
[tool call]   search_glossary({'query': 'LoRA'})
requests=2, tool_calls=1
```

**Result with modified INSTRUCTIONS** (same question, `search_glossary` line removed):
```
[tool call]   search_glossary({'query': 'LoRA'})
requests=2, tool_calls=1
```

The model still searched the glossary even without the explicit instruction — because the tool's docstring says "Use this before answering about course-specific terms." This shows that **docstrings can be as important as INSTRUCTIONS** in guiding tool usage. The model reads both.

**Key observation:** INSTRUCTIONS set the agent's overall behavior; docstrings control when individual tools get called. Removing one line from INSTRUCTIONS didn't break tool use here because the docstring compensated.

---

### Implementation — `save_learning_log` tool with `requires_approval=True`

Added `save_learning_log(note: str)` to `app/tools.py` and registered it in `app/agent.py` with:

```python
agent.tool_plain(tools.save_learning_log, requires_approval=True)
agent = Agent(instructions=INSTRUCTIONS, output_type=[str, DeferredToolRequests])
```

The tool saves a timestamped `.txt` file to `learning_log/`. When called, execution pauses and returns `DeferredToolRequests` — the program asks the user for confirmation before proceeding.

**Docstring written:**
```
Save a learning note or record to the learning_log folder.

Use when the user explicitly asks to save, record, or log something they have learned.
Saves the note as a timestamped text file in learning_log/.
Requires user confirmation before saving because this writes to disk and is hard to undo.
```

**Key observation:** `requires_approval=True` is the Pydantic AI mechanism for human-in-the-loop. Irreversible operations (file writes, external API calls, emails) should always go through this gate. The agent is capable but the human decides whether to proceed.

---

### Advanced — Rebuilt with Google ADK

Created `adk_agent/glossary_agent/agent.py` reusing `INSTRUCTIONS` and the same three tools (`search_glossary`, `get_lecture_summary`, `make_quiz`) from `app/`:

```python
from google.adk.agents import Agent
from app import tools
from app.agent import INSTRUCTIONS

root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="glossary_agent",
    instruction=INSTRUCTIONS,
    tools=[tools.search_glossary, tools.get_lecture_summary, tools.make_quiz],
)
```

Run with:
```bash
PYTHONPATH=. uv run --with google-adk adk run adk_agent/glossary_agent
```

**Code comparison — Pydantic AI vs ADK:**

| Aspect | Pydantic AI (`app/agent.py`) | ADK (`adk_agent/`) |
|--------|------------------------------|---------------------|
| Agent class | `pydantic_ai.Agent` | `google.adk.agents.Agent` |
| Tool registration | `agent.tool_plain(fn)` | `tools=[fn, ...]` in constructor |
| INSTRUCTIONS | `Agent(instructions=...)` | `Agent(instruction=...)` (no s) |
| Output type | `output_type=[str, DeferredToolRequests]` | Not needed — ADK handles loop internally |
| Running | `agent.run_sync(question, model=...)` | `adk run adk_agent/glossary_agent` |
| Trace/debug | `--trace` flag + custom `print_trace()` | Built-in `adk web` UI |

**Key observation:** ADK's interface is more declarative — tools are passed as a list at construction time rather than registered one by one. ADK also provides a web UI (`adk web`) for visualizing tool calls without writing custom trace code. Pydantic AI gives more programmatic control and is easier to test with `TestModel`. Both reuse the same `INSTRUCTIONS` and tool functions without modification.
