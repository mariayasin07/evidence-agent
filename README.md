# Evidence Research Agent

A lean Python + Streamlit research agent. Enter any topic; the agent plans, searches (DuckDuckGo + OpenAlex + Crossref), evaluates sources, verifies each claim's quote against its source, checks for conflicts, and writes a cited report with an Evidence Map. Export to PDF or DOCX.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # optional
```

## LLM configuration

One provider interface is used by every agent. Choose it in **Settings → AI / Model**.

**Ollama (local)**
1. Install Ollama and pull a model, e.g. `ollama pull llama3.1`.
2. Host URL defaults to `http://localhost:11434` (or set `OLLAMA_HOST`).
3. Click **Check connection / refresh models** (reads `/api/tags`) and select a model.

**Cloud API**
1. Pick OpenAI, Anthropic, Google Gemini, OpenRouter, Groq, or Custom (any OpenAI-compatible base URL).
2. Enter the API key in Settings (kept in the browser session only) or set `LLM_API_KEY` in `.env`.
3. Click **Check connection / refresh models** and select a model. If discovery fails you can type a model name.

Optional: set `CONTACT_EMAIL` in `.env` for OpenAlex/Crossref polite-pool access.

## Run

```bash
streamlit run app.py
```

Data is stored locally: settings and history in `.data/`, generated exports in `exports/`.

## Deployment

**Streamlit Community Cloud:** push to GitHub, create an app pointing at `app.py`, and add secrets as environment variables (`LLM_API_KEY`, optionally `LLM_BASE_URL`, `CONTACT_EMAIL`). Ollama must be reachable from the host, so use a Cloud API provider there.

**Docker / VM:** install requirements, then run `streamlit run app.py --server.port 8501 --server.address 0.0.0.0` behind a reverse proxy. Set `OLLAMA_HOST` to a reachable Ollama server if using Ollama. Note that `.data/` should be on persistent storage to keep Research History.

## Structure

```text
app.py            Streamlit UI (New Research, History, Settings, Export)
agents/           planner, researcher, evaluator, verifier, conflicts, reporter, orchestrator
services/         llm.py (provider interface), export.py (PDF/DOCX)
tools/            web_search (DuckDuckGo), openalex, crossref
models/           data schemas
utils/            config, history, text helpers, theme
exports/          generated files
```
