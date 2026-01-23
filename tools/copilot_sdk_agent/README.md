# HP Motor – Copilot SDK Agent (Tools)

This directory contains developer tooling that uses the GitHub Copilot SDK to run agentic workflows.
It is intentionally isolated from the Streamlit runtime.

## What this is
- A developer agent runner under `tools/`
- Can run tasks like:
  - Audit registry & analysis objects
  - Validate contracts & required files
  - Produce docs and consistency reports

## What this is NOT
- Not imported by Streamlit `app.py`
- Not part of runtime dependencies (`requirements.txt`)

## Setup (local)
1) Install runtime deps (optional):
   - `pip install -r requirements.txt`

2) Install dev deps:
   - `pip install -r requirements-dev.txt`

3) Configure auth:
   - Follow Copilot SDK documentation / your environment requirements.
   - Do not hardcode tokens in code.
   - Prefer environment variables.

## Run
From repo root:

- Audit:
  - `python tools/copilot_sdk_agent/main.py audit`

- Validate files:
  - `python tools/copilot_sdk_agent/main.py validate`

- Show prompts:
  - `python tools/copilot_sdk_agent/main.py show-prompts`

## Notes
- If Copilot SDK is not available in your environment, the runner will degrade gracefully and show instructions.
- Keep all agent outputs in `reports/` (future step).