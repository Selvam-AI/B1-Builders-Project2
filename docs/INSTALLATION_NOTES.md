# Installation Notes

## Applications To Install

Available:

- Python 3.12.3
- Git 2.43.0
- SQLite CLI 3.50.6
- VS Code CLI 1.119.0
- Node.js 18.19.1
- npm 9.2.0

Optional for local LLM review summaries:

- Ollama, if `AI_RECOMMENDER_MODE=llm`
- Local model, currently `llama3`

Optional:

- SQLite Browser
- Modern browser

## Python Packages Installed

Installed into `.venv`:

- FastAPI / Uvicorn
- SQLAlchemy / SQLite support
- Pydantic / Pydantic Settings
- Authentication helpers
- LiteLLM
- Ollama as the optional local LLM provider
- OpenAI as an optional paid LLM provider
- YouTube API client
- pytest / httpx

## Optional Local LLM Setup

Optional safety-review provider:

- Ollama
- Model setting: `MODEL=ollama/llama3`
- Base URL: `BASE_URL=http://localhost:11434`

Install and prepare Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3
ollama serve
```

If `ollama serve` returns `bind: address already in use`, Ollama is usually already running on `127.0.0.1:11434`. Confirm with:

```bash
curl http://127.0.0.1:11434/api/tags
```

CPU-only mode is acceptable for optional summaries, but responses can be slow. The video curator and scheduling rules are deterministic and do not require Ollama.

If no LLM is available during a demo, use the mock/rule-based recommender fallback:

```bash
AI_RECOMMENDER_MODE=mock
AI_ALLOW_MOCK_FALLBACK=true
```

Enable diagnostic logging during development with:

```bash
DEBUG=true
```

When enabled, the backend prints `[FitHub AI]` recommendation decisions in the Uvicorn terminal, and the frontend prints matching browser-console diagnostics after reading `/api/status`.

## Frontend Packages

Installed through `src/frontend/package.json`:

- React / React DOM
- Vite / TypeScript
- lucide-react
- Vitest

Refresh frontend dependencies with:

```bash
cd src/frontend
npm install
```

## System Installation Commands

Optional:

```bash
sudo apt install -y sqlitebrowser
```

## Debug Notes

CrewAI was removed from the current implementation. LiteLLM remains pinned at `1.82.6` only for optional Ollama/OpenAI safety-review summaries.

The deterministic Video Curator is configured with:

```bash
VIDEO_CURATOR_ENABLED=true
VIDEO_CACHE_TARGET_PER_CATEGORY=5
VIDEO_CACHE_MAX_PLAY_COUNT=3
VIDEO_CURATOR_INTERVAL_HOURS=24
```

## Local Admin Account

The development seed flow creates one local admin account when `SEED_ADMIN=true`:

```text
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
```

This is for prototype evaluation only. For production-style deployment, set `SEED_ADMIN=false` and create admin users through a secure provisioning process.
