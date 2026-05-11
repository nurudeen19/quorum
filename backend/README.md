# Backend

REST API for generating pre-meeting intelligence briefs. Handles user authentication, agent-based research orchestration, and conversation persistence.

## Quick Start

**Prerequisites:** Python 3.10+, PostgreSQL (or SQLite for dev)

```bash
cd backend
uv sync --extra transformer-cpu
# uv sync --extra transformer-gpu # selects the gpu variant of transformers required for prmpt guard

```

Copy `.env.example` → `.env` and fill in the blanks (see Environment Variables below).

```bash
uv run scripts/migrate_db.py
uv run uvicorn app.main:app --reload
```

API is now at `http://127.0.0.1:8000` • Interactive docs at `/docs`

## Environment Variables

| Variable | Purpose | Required | Example |
|----------|---------|----------|---------|
| `DATABASE_URL` | PostgreSQL or SQLite connection | ✓ | `postgresql+asyncpg://user:pass@localhost/quorum_db` |
| `JWT_SECRET` | Secret key for signing tokens | ✓ | (long random string) |
| `OPENAI_API_KEY` | OpenAI API access | — | `sk-...` |
| `GROQ_API_KEY` | Groq API access | — | (if using Groq) |
| `LANGSMITH_API_KEY` | LangSmith tracing | — | (if tracing enabled) |
| `LANGSMITH_TRACING_ENABLED` | Turn on agent tracing | — | `true` |
| `FRONTEND_APP_BASE_URL` | Frontend URL for emails | — | `http://localhost:5173` |

See `.env.example` for all options.

## Common Commands

| Command | Purpose |
|---------|---------|
| `uvicorn app.main:app --reload` | Start dev server with hot-reload |
| `python scripts/migrate_db.py` | Run pending database migrations |
| `pytest -q` | Run all tests |
| `pytest tests/test_auth.py -v` | Run specific test file |

## Project Structure

```
app/
  agents/           ← AI agent prompts and logic
  api/endpoints/    ← HTTP routes
  models/           ← Database ORM models
  schema/           ← Pydantic validation schemas
  services/         ← Business logic (auth, chat, etc.)
  core/             ← Bootstrap, config, database setup
  graph/            ← Agent orchestration pipeline
migrations/         ← Database migration files
scripts/            ← Utility scripts (DB, exports, etc.)
tests/              ← Unit and integration tests
```

## What's Going On

**Authentication**: JWT tokens protect the API. Users sign up/log in, then create briefing requests and track their history.

**Pre-Meeting Briefing Flow**: When a user submits basic info (names, companies, meeting goal), the pipeline runs:
1. **Guardrails** — Quick validation: is the input safe and specific enough?
2. **Planner** — Decides what research questions to answer based on the meeting context
3. **Research** — Finds public information about the people and organizations using web search and other tools
4. **Synthesizer** — Writes a concise, readable pre-meeting memo from the research
5. **Reviewer** — Final pass for accuracy and completeness

The user sees progress updates in real-time as each step completes. See [Architecture](../docs/architecture.md) for the full flow.

**Database**: SQLAlchemy ORM with async/await. Stores user accounts, briefing requests, conversation history. Migrations managed by Alembic.

**Observability**: Agent interactions are traced in LangSmith (optional) for debugging and seeing what the system researched.

## Troubleshooting

**Database connection fails**
- Check `DATABASE_URL` is correct in `.env`
- For PostgreSQL, verify the database exists and credentials are right

**Tracing isn't appearing in LangSmith**
- Set `LANGSMITH_TRACING_ENABLED=true` in `.env`
- Verify `LANGSMITH_API_KEY` is set
- Check application logs for errors during startup

**Migrations error**
- Run `python scripts/migrate_db.py` to see what's pending
- If stuck, delete the database and restart (dev only)

**Agent responses don't match expected format**
- Agent outputs must match schemas in `app/schema/agents.py`
- If you modify an agent prompt, test that it still conforms to the schema
- Run `pytest` to validate against test data

## Next Steps

- **First time?** Read [Architecture](../docs/architecture.md) to understand the design
- **Modifying agents?** Edit prompts in `app/agents/` and test against schemas in `app/schema/`
- **Adding endpoints?** Create route files in `app/api/endpoints/`
- **Database changes?** Use Alembic: `alembic revision --autogenerate -m "description"`



