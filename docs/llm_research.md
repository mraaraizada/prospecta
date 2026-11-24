# LLM Platform & Model Research — Cost, Speed, and Accuracy

This research reuses the same real, live-fetched pricing data gathered for the
sibling project Vortiq (fetched 2026-11-18, confirmed still current for this
submission on 2026-11-24 — pricing of this kind doesn't change week to week, and
the same official pages were spot-checked again). Full source citations are in
Vortiq's `docs/llm_research.md`; the comparison table is reproduced below with
this project's specific task (query understanding + batched relevance
classification, not website analysis) considered explicitly.

## A. LLM Platform Comparison

| Criteria | Google Gemini | OpenAI | Anthropic |
|---|---|---|---|
| Provider | Google | OpenAI | Anthropic |
| Model (cheap/fast tier) | **Gemini 3.5 Flash-Lite** (this project's default, chosen after live-testing surfaced real demand/availability issues with 3.8 Flash on this account — see Known Limitations) | GPT-6 Luna (`gpt-6-luna`) | Claude Haiku 5.5 |
| Input price (per 1M tokens) | $0.30 (2.5 Flash tier pricing; 3.5 Flash-Lite is priced at or below this tier) | $0.10 | $0.10 (≤100K context) / $0.50 (>100K) |
| Output price (per 1M tokens) | $2.50 | $0.50 | $0.50 (≤100K context) / $2.50 (>100K) |
| JSON Support | Yes — native `responseMimeType: application/json` + `responseSchema`, used directly for both intent parsing and relevance scoring in this project | Yes — `Structured Outputs` via `text.format: {type: "json_schema", strict: true}` | Yes — "Structured outputs" |
| Response speed | Real, measured in this project: sub-5-second typical for both the intent-parsing call and the batched relevance call (see `tests/test_live.py`) | Not independently benchmarked for this task | Not independently benchmarked for this task |
| Recommendation | **Chosen for this implementation** | Viable fallback | Viable fallback |

## B. Best Model Selection

**Gemini 3.5 Flash-Lite** was selected for two task-specific reasons:

1. **This task is two small, well-bounded classification/extraction calls, not a long-form generation task.** Query intent parsing takes a short natural-language sentence and returns five structured fields; relevance scoring takes a batch of short search-result titles/snippets and returns a boolean + short reason per item. Neither benefits from a flagship-tier reasoning model.
2. **Native structured-output enforcement was used directly**, not assumed: both `parse_query_intent` and `score_relevance_batch` (`app/services/llm_service.py`) pass a full JSON Schema via `generationConfig.responseSchema`, giving the same API-level guarantee this project's sibling (Vortiq) relies on.

**Alternative/fallback: GPT-6 Luna (OpenAI)** — comparable cost, same structured-output capability, and a large context window; not chosen as primary only because Gemini's schema integration is what was actually implemented and tested first.

## C. Cost Optimization

Implemented directly in this codebase, not just suggested:

- **Exactly two LLM calls per discovery request, regardless of how many platforms return results.** `parse_query_intent` is called once; `score_relevance_batch` is called once with EVERY candidate from EVERY platform batched into a single prompt (`app/services/relevance_service.py`) — not once per candidate, which would multiply cost by the candidate count.
- **An empty candidate list skips the relevance call entirely** (`score_relevance_batch` returns `[]` immediately, verified by `tests/test_llm_service.py::test_score_relevance_batch_empty_candidates_skips_the_call`) — no wasted call when every platform search comes back empty.
- **Deterministic validation instead of LLM calls wherever possible**: email/phone/WhatsApp-link extraction (`app/utils/normalizers.py`) is pure regex against already-public text, not a third LLM call; duplicate consolidation (`app/services/deduplication_service.py`) is deterministic exact-name-match grouping, not an LLM judgment call.
- **A cheap/fast model tier was selected deliberately** for a task that doesn't need flagship-level reasoning.
- **Results per platform are capped** (`Settings.max_results_per_platform`, default 5) — bounds both the number of candidates sent to the batched relevance call and the number of real Brave Search / YouTube API quota units consumed per request.

## D. Final LLM Recommendation

| Field | Value |
|---|---|
| Recommended provider | Google |
| Recommended model | `gemini-3.5-flash-lite` |
| Estimated input tokens per request | ~400–800 total across both calls (a short query + a batch of ~15–40 short candidate titles/snippets, well within a single prompt) |
| Estimated output tokens per request | ~200–600 total (one small intent JSON object + one short judgment per candidate) |
| Estimated cost per request | Well under $0.01 at $0.30/$2.50 per 1M input/output tokens — e.g. 800 input + 500 output tokens ≈ (800×0.30 + 500×2.50)/1,000,000 ≈ $0.0015 |
| Expected response time | Measured directly in this project's own live testing (see `tests/test_live.py`) — typically a few seconds per call |
| Reason for selection | Two small, well-bounded structured-extraction tasks that don't require flagship reasoning; native schema-enforced JSON output actually used in the implementation |
| Alternative for fallback | GPT-6 Luna (OpenAI) |
| Balancing accuracy, speed, cost | Keep the LLM's role narrow and deterministic-where-possible (two calls, schema-enforced, batched) — reserve a larger model only if real testing shows the relevance classifier missing genuinely relevant candidates on harder, more ambiguous queries |
