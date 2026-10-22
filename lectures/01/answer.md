# Lecture 1: Solution

## Exercise

**Question asked**: "What are the 3 levels of homework mentioned in the AIE2026 course?"

**Model response**:
- English version: The model honestly stated it doesn't have access to AIE2026 course materials and asked for more context (no hallucination)
- Japanese version: The model admitted it doesn't know, then provided 5 plausible classifications (difficulty levels, AI engagement levels, educational taxonomy) that sound reasonable but don't match the actual course definition

**Correct answer** (from `data/glossary.json`): 
- Basic (confirm lecture content)
- Implementation (write code yourself)
- Advanced (investigation and experimentation)

**Token counts**:
- English question: Input 20 / Output 94
- Japanese question: Input 21 / Output 527

**Key insight**: The model can confidently present plausible-sounding but incorrect information, demonstrating hallucination—a major concern when using LLMs without external knowledge bases.

---

## Homework

Completed all three levels.

### Basic Level: Ask the same question 3 times

**What was done**:
- Asked "What is LoRA?" three times using `gemini-3.5-flash-lite`
- Recorded output text and token counts for each run
- 1-second delay between runs

**Results**:
- Run 1: Input 6 / Output 673
- Run 2: Input 6 / Output 690
- Run 3: Input 6 / Output 722

**Observations**:
- The first 200 characters of output were identical across all three runs
- Output token count varied (673, 690, 722) despite identical prompt
- This shows that general knowledge questions have stable *structure* but variable *detail density*
- Temperature's default value makes responses follow the same general flow but with different levels of elaboration

---

### Implementation Level: Chat mode with conversation history

**What was done**:
- Implemented a chat mode that maintains conversation history
- Sent 2 back-and-forth exchanges:
  1. "What is LoRA?"
  2. "Can you give me a specific example?"
- Measured input/output tokens for each turn

**Results**:
- Turn 1: Input 6 / Output 732
- Turn 2: Input 748 / Output 725

**Key findings**:
- Input tokens jumped from 6 → 748 on turn 2 (previous output + full history)
- Gemini API is **stateless**: clients must resend the entire conversation history with each request
- A 3-5 turn conversation would consume ~3000+ input tokens, which impacts rate limits in the free tier
- Long conversations require message summarization or selective history retention

---

### Advanced Level: Multi-model benchmarking

**What was done**:
- Tested 2 models (`gemini-3.5-flash-lite` and `gemini-3.5-flash`)
- 2 different questions × 2 runs each = 8 total requests
- Measured response time and output tokens for each request
- Logged results to `lectures/01/bench_results.csv`

**Results**:
- **gemini-3.5-flash-lite**:
  - Average response time: 3.05 seconds
  - Average output tokens: 657
  - All 4 requests succeeded
  
- **gemini-3.5-flash** (full version):
  - Average response time: 11.23 seconds
  - Average output tokens: 828
  - All 4 requests succeeded

**Analysis**:
- `gemini-3.5-flash` is **3.7× slower** but produces 26% more tokens (higher quality)
- No rate-limit (429) or overload (503) errors encountered
- `gemini-3.5-flash-lite` is ideal for prototyping in free tier due to speed and stability
- Response time ≈ fixed overhead (~1s) + (output tokens ÷ throughput in tokens/sec)

---

## Deliverables

- **Modified**: `app/ask.py` - Added token count display
- **Modified**: `lectures/01/answer.md` - This file with exercise and homework results
- **New**: `lectures/01/bench_results.csv` - Benchmark data from advanced homework
