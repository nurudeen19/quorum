# Quorum

**Pre-meeting intelligence for when there's no time to prepare.**

That meeting invite just landed, and all you have is a name and a company. Quorum fills the gaps—pulling public context on people and organizations, turning minimal info into a clear pre-meeting memo so you can walk in informed instead of blindsided.

## What it does

- Takes basic meeting info (names, companies, what you need to accomplish)
- Gathers public context about the people and organizations involved
- Synthesizes it into a tight briefing memo you can skim in minutes
- Lets you ask follow-up questions in chat if you need more detail
- Streams progress in real-time so you see what it's researching

## Get started in 5 minutes

### Backend (API server)
```bash
cd backend
uv sync --extra transformer-cpu
# uv sync --extra transformer-gpu # selects the gpu variant of transformers required for prmpt guard
uv run scripts/migrate_db.py
uv run uvicorn app.main:app --reload
```
→ See [Backend README](backend/README.md) for full setup and environment variables.

### Frontend (Web UI)
```bash
cd frontend
npm install
npm run dev
```
→ See [Frontend README](frontend/README.md) for full setup and commands.

## How it's built

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend** | FastAPI, Python | REST API, agent orchestration, database |
| **Frontend** | Vue 3, TypeScript, Vite | Interactive web interface, real-time updates |
| **Agents** | LangGraph, LLMs | Multi-step reasoning pipeline |
| **Database** | PostgreSQL, SQLAlchemy | Persist users, conversations, history |
| **Observability** | LangSmith, OpenTelemetry | Monitor and trace agent behavior |

## Next steps

- **New to the project?** → Read [Architecture](docs/architecture.md) to understand the design
- **Setting up locally?** → See [Backend](backend/README.md) and [Frontend](frontend/README.md) READMEs
- **Want to modify agents?** → Check out [Agent Orchestration](docs/architecture.md#agent-orchestration-flow)

