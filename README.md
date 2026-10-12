# Replayable support-ops pipeline (starter)

## Setup

Create a Python environment:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Place the assignment's `tickets.json` and `kb_articles.json` in the project root. Copy `.env.example` to `.env` and replace the API key with your own. Never commit `.env` or `runs/` (they contain sensitive ticket text and model prompts).

## Run

```powershell
python main.py --tickets tickets.json --kb kb_articles.json --output runs/run_001
```

The output directory contains all stage artifacts under the filenames required by the assignment, plus `01_tickets_loaded.json`, `validation_results.json`, `final_results.json`, `stage_events.jsonl`, `llm_calls.jsonl`, and `manifest.json`.

## Test deterministic stages

```powershell
python -m pytest -q
```

## Architecture

- Ingestion: deterministic validation, no re-keying tickets.
- Preprocessing: clean English text; translate non-English hinted tickets (one LLM call each).
- Classification: **one batch Stage 1 LLM call** over all preprocessed tickets.
- Retrieval: self-contained deterministic TF-IDF cosine search over actual article fields, top two.
- Priority: exact specified scoring formula, descending sort, stable ticket-ID tie break, top five.
- Routing: **one batch Stage 2 LLM call**, validated queues and safety labels, deterministic safety floor.
- Drafts: **one batch Stage 3 LLM call** for only the top five, verified citations, unsent and subject to review.

## Known limitations

This is a runnable starter rather than a fully production-hardened replay engine. Input language hints are treated as trustworthy for English; a wrong `en` hint can bypass translation. For exact offline replays, extend the LLM client to load logged model responses rather than contacting the provider. The LLM logs include prompts and full replies; keep these restricted and redact sensitive data if needed. Simple schema and citation validation cannot reliably detect all hallucinations or unsafe claims: actual human approval is required. A model formatting error fails safely and leaves previous stage artifacts intact. Requires an active API key and model access.
