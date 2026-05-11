# Design Decisions

This document records key architectural decisions made in Quorum and their rationales. Each section follows an ADR (Architecture Decision Record) format.

---

## ADR-001: Modular Settings Configuration

### Context

Quorum integrates with multiple external services (LLMs, cache systems, search tools, tracing). Configuration needs to support:
- Independent tuning of each agent (planner, research, synthesizer, reviewer)
- Multiple LLM providers (OpenAI, Groq, Google) with fallbacks
- Different deployment environments (dev, staging, production)
- Optional features (tracing, observability, email)

A single flat configuration file or env vars become unmaintainable.

### Decision

Implement **modular settings hierarchy** using Pydantic `BaseSettings` in `backend/app/config/`:

```
config/
  ├── app_settings.py       # Core app (database, auth, CORS, logging)
  ├── agents.py             # Per-agent LLM configs (models, providers, temps)
  ├── cache.py              # Cache backend selection (memory/Redis/Upstash)
  ├── rate_limits.py        # Rate limiting policies
  └── guardrails.py         # Input validation thresholds
```

**Configuration sources (in order):**
1. Environment variables (`.env`)
2. Hardcoded defaults in config classes
3. No config files (everything via code + env)

### Rationale

- **Separation of concerns:** Each domain owns its config (agents separate from database)
- **Type safety:** Pydantic validates at startup; fail fast on bad config
- **Small `.env`:** Only override what you need; defaults are in code
- **Self-documenting:** Field descriptions explain purpose and valid ranges
- **Testable:** Inject config into services; easy to mock or override
- **Per-agent flexibility:** Each agent can use different models, providers, temperatures independently

### Trade-offs

- **More files:** More structure, but clearer intent
- **Boilerplate:** Pydantic Field definitions are verbose (but worth the clarity)
- **Startup cost:** Settings validated once at startup (negligible, ~10ms)

---

## ADR-002: Conversation History via ORM Models (Not LangGraph Checkpointers)

### Context

LangGraph provides checkpointers to save graph state across invocations. Quorum needs:
- Multi-turn conversations (user questions, agent responses)
- Conversation replay and resumption
- User-facing chat history (queryable, displayable)
- Audit trail (who said what, when)
- Independence from framework versions

### Decision

Manage conversation history with explicit SQLAlchemy ORM models instead of LangGraph checkpointers:

```python
class Conversation(Base):
    """User-owned conversation thread."""
    id: UUID
    user_id: UUID
    title: str | None
    summary: str | None  # Agent-generated summary, refreshed on demand
    created_at: datetime
    updated_at: datetime
    messages: list[Message]  # Full message history

class Message(Base):
    """Individual message in a conversation."""
    id: UUID
    conversation_id: UUID
    sender: str  # "user" or "assistant"
    content: str
    role: MessageRole  # ENUM: USER, ASSISTANT, SYSTEM
    created_at: datetime
```

**How it works:**
1. User submits input → inserted to `Message` table immediately
2. Each agent step → output written to `Message` as it completes
3. `Conversation.summary` → refreshed after N messages (configurable)
4. Optional cache layer → Redis/Upstash reads recent messages for agent context
5. PostgreSQL → source of truth; cache is read-through only

### Rationale

- **Portability:** Change from LangGraph to different orchestration? History is untouched
- **Auditability:** Every message is readable SQL; no opaque binary blobs
- **Queryable:** Build dashboards, analytics, search across conversations
- **User-facing:** Chat UI directly reads `Message` table; no special decoding
- **Framework-independent:** History survives framework version bumps
- **Partial updates:** Stream agent outputs in real-time without waiting for full completion

### Trade-offs

- **Manual management:** Write/read messages explicitly instead of relying on checkpointer
- **Slightly more code:** History logic in `services/history_service.py`; not framework-automagic
- **Consistency:** Must ensure messages are written consistently (solved with service layer)

---

## ADR-003: Multiple Cache Backends (Memory / Redis / Upstash)

### Context

Caching strategy depends on deployment environment:
- **Local dev:** In-memory cache is fastest, zero setup
- **Small/hobby deployments:** Serverless Redis (Upstash) avoids ops burden
- **Production:** Self-hosted Redis for cost control and availability

A single hardcoded backend doesn't fit all use cases.

### Decision

Implement **pluggable cache factory** with three backends:

```python
class CacheSettings(BaseModel):
    cache_backend: Literal["memory", "upstash", "redis"] = "memory"
    cache_max_turns: int = 10  # Rolling window of recent messages
    upstash_redis_url: str | None = None
    upstash_redis_token: str | None = None
    redis_url: str | None = None

cache = CacheFactory.build(cache_settings)
# Returns InMemoryCache, UpstashCache, or RedisCache
```

All backends implement the same interface:
```python
class ConversationCache(ABC):
    async def get(self, conversation_id: UUID) -> ConversationHistorySnapshot
    async def append(self, conversation_id: UUID, message: CachedMessage)
    async def set_agent_summary(self, conversation_id: UUID, summary: str)
```

### Rationale

- **Flexibility:** Same code runs on dev (memory), hobby tier (Upstash), production (Redis)
- **Low ops:** Upstash is managed Redis; no infrastructure to maintain
- **Cost-effective:** Pay only for what you use at each stage
- **Fallback:** If cache is down, automatically fall back to database reads (slower but works)
- **No code changes:** Switch backends by changing env vars

### Trade-offs

- **Multiple implementations:** Each backend has its own class (but small)
- **Upstash pricing:** Small overhead for serverless (acceptable for MVP)
- **Cache invalidation:** Must handle TTL and manual invalidation carefully

---

## ADR-004: Multiple LLM Providers with Per-Agent Fallbacks

### Context

Using a single LLM provider creates risks:
- Provider outage → entire system down
- Pricing varies; switching providers requires code changes
- Different models excel at different tasks (reasoning, speed, cost)
- Need to handle provider rate limits gracefully

### Decision

Support **multiple LLM providers** with **per-agent primary + fallback chain**:

**Supported providers:**
- OpenAI (GPT-4o-mini, GPT-4 Turbo)
- Groq (Llama 3.3 70B, fast inference)
- Google (Gemini)
- OpenRouter (proxy gateway)

**Per-agent configuration:**
```python
class AgentLLMConfig(BaseModel):
    model: str                          # Primary model
    model_provider: ModelProvider       # Primary provider
    fallback_model: str | None          # Fallback model
    fallback_model_provider: ModelProvider | None
    temperature: float
    max_tokens: int
```

**Example: Planner agent**
```python
planner_model="llama-3.3-70b-versatile"
planner_model_provider="groq"            # Fast, cheap
planner_fallback_model="gpt-4o-mini"
planner_fallback_model_provider="openai" # Reliable fallback
```

### Rationale

- **Resilience:** If Groq is rate-limited, automatically use OpenAI
- **Cost optimization:** Use cheaper provider (Groq) first; fall back to premium (OpenAI) if needed
- **Task-specific:** Each agent can use best-fit provider (researcher needs accuracy, planner needs speed)
- **Graceful degradation:** Single provider failure doesn't crash system
- **Easy to tune:** Change providers by updating environment variables

### Trade-offs

- **API key management:** 4+ provider API keys to configure and secure
- **Testing complexity:** Mock multiple providers in tests
- **Model variance:** Different models produce slightly different output styles
- **Latency:** Fallback adds latency if primary provider fails

---

## ADR-005: Provider Abstraction Layer

### Context

Different LLM providers have different:
- API formats
- Token counting methods
- Rate limit handling
- Response streaming
- Feature support (structured output, function calling, etc.)

Hardcoding provider details in agents creates tight coupling.

### Decision

Use **AgentFactory** to abstract away provider specifics:

```python
class AgentFactory:
    @staticmethod
    def get_llm_client(provider: ModelProvider, model: str) -> BaseChatModel:
        if provider == "openai":
            return ChatOpenAI(model=model, api_key=settings.openai_api_key)
        elif provider == "groq":
            return ChatGroq(model=model, api_key=settings.groq_api_key)
        elif provider == "google":
            return ChatGoogleGenerativeAI(model=model, api_key=settings.google_api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")
```

All agents use factory-provided clients. No direct LLM API calls from agent code.

### Rationale

- **Swappable:** Add new provider → register in factory; agent code unchanged
- **Testable:** Mock factory, test agent logic without hitting real APIs
- **Centralized:** Provider-specific logic in one place (factory)
- **Future-proof:** Can upgrade provider without touching agents
- **No duplication:** Each agent doesn't re-implement provider logic

### Trade-offs

- **Dependency on LangChain:** Still bound to LangChain's abstraction
- **Limited features:** Lowest-common-denominator API (some provider features hidden)

---

## ADR-006: Structured Pydantic Schemas for All Agent I/O

### Context

Agent outputs are unpredictable JSON. Without structure:
- Parsing agent responses is brittle
- Optional fields cause crashes
- Format changes break downstream code
- Frontend doesn't know response shape

### Decision

Validate all agent inputs/outputs against strict Pydantic models:

```python
# Input to planner
class PlannerInput(BaseModel):
    meeting_context: str
    goal: str

# Output from planner
class ResearchPlan(BaseModel):
    questions: list[str]
    scope: str
    estimated_duration_minutes: int

# Output from research
class ResearchFindings(BaseModel):
    findings: list[Finding]
    sources: list[str]

class Finding(BaseModel):
    category: str
    content: str
    confidence: float  # 0-1
```

**In agent code:**
```python
output_dict = await llm.invoke(prompt)
findings = ResearchFindings(**output_dict)  # Validates, raises if invalid
await callback.emit_message(findings.model_dump_json())
```

### Rationale

- **Type safety:** mypy catches schema mismatches at development time
- **Early validation:** Bad LLM output caught immediately, not downstream
- **API contract:** Frontend knows exact response shape
- **Auto-documentation:** Schemas appear in OpenAPI docs
- **Serialization:** `.model_dump_json()` is always correct

### Trade-offs

- **LLM must output valid JSON:** Mitigated by detailed prompts with examples
- **Schema rigidity:** Breaking changes require version migration
- **Retry on parse failure:** Need logic to retry agent if output doesn't match schema

---

## ADR-007: Async/Await Throughout

### Context

I/O operations (database, LLM calls, search API) are slow. Synchronous code blocks the process.

### Decision

All I/O is **async**:
- Database: `asyncpg` + SQLAlchemy async
- HTTP: `httpx` async client
- LLM calls: LangChain's async methods
- File I/O: `aiofiles` (when used)

**Example: Concurrent research tool invocation**
```python
async def research(self, query: str):
    results = await asyncio.gather(
        self.web_search(query),
        self.company_api(query),
        self.news_api(query),
    )
    return merge_results(results)
```

### Rationale

- **Scalability:** Single process handles 100s of concurrent users (not 1 per thread)
- **Responsive:** UI updates don't wait for slow API calls
- **Efficient:** Small memory footprint per connection
- **Cost:** Cheap VMs handle high concurrency

### Trade-offs

- **No blocking code:** All libraries must support async
- **Debugging:** Async stack traces can be confusing
- **Learning curve:** Async/await concepts unfamiliar to some developers

---

## ADR-008: Immutable Message Log

### Context

Conversations grow over time. How to store messages?
- Update existing messages? (Wrong; breaks audit trail)
- Delete messages? (Wrong; lose history)
- Insert and never modify? (Right; preserves history)

### Decision

Treat conversation messages as **immutable, append-only log**:

```python
class Message(Base):
    id: UUID
    conversation_id: UUID
    sender: str
    content: str
    role: MessageRole
    created_at: datetime
```

- Insert on every user message and agent output
- Never update existing messages
- Pagination via `created_at` for easy retrieval
- Optional archival/pruning for very old messages

### Rationale

- **Auditability:** Every change is recorded with timestamp
- **Reversibility:** Can replay history from any point
- **Concurrency:** No update conflicts (inserts are atomic)
- **Simple queries:** Pagination by timestamp

### Trade-offs

- **Storage:** Keeps full history (OK; storage is cheap)
- **No edits:** Users can't correct messages (acceptable; add new message instead)

---

## ADR-009: Optional Observability (LangSmith, OpenTelemetry)

### Context

Debugging agent behavior is hard without visibility. Options:
1. No tracing (blind debugging)
2. Always-on tracing (expensive, adds latency)
3. Optional tracing (pay for what you need)

### Decision

Make observability **optional but complete**:

```python
# In .env
LANGSMITH_TRACING_ENABLED=false      # Default: off
LANGSMITH_API_KEY=...                # Only needed if enabled
OTEL_EXPORTER_OTLP_ENDPOINT=...      # OpenTelemetry (optional)
```

When enabled, automatically trace:
- Every agent step (input, output, latency)
- LLM calls (model, tokens, response time)
- Tool invocations (search API, etc.)

### Rationale

- **Local dev:** Works without tracing (no setup needed)
- **Cost control:** Only pay for tracing in production
- **Observability infrastructure optional:** Deployment works with or without it
- **Instrumentation automatic:** No code changes to enable/disable

### Trade-offs

- **Feature detection:** Code must check if tracing is enabled
- **Incomplete telemetry:** Local dev has no traces (acceptable for dev)

---

## ADR-010: Rate Limiting (3-Tier Strategy)

### Context

Prevent abuse and resource exhaustion. Options:
1. No rate limiting (vulnerable to attacks)
2. Single global limit (too coarse)
3. Per-IP + per-user + per-action (comprehensive)

### Decision

Implement **three-tier rate limiting**:

1. **IP-based (SlowAPI):** 100 requests/minute per IP (unauthenticated)
   - Prevents bot/scan attacks from single IP

2. **Per-user:** 1000 requests/minute per authenticated user
   - Prevents accidental overuse by legitimate user

3. **Business-logic specific:** 10 briefing requests/hour per user
   - Limits expensive operations (briefing generation)
   - Stored in database (survives restart)

### Rationale

- **Layered defense:** Catches attackers at different levels
- **Legitimate use allowed:** Generous limits for real users
- **Expensive ops protected:** Briefing generation limited separately
- **Persistent:** User limits survive process restart

### Trade-offs

- **Complexity:** Three different limit mechanisms
- **False positives:** Risk of blocking shared IPs (corporate networks)

---

## References

- ADR format: https://adr.github.io/
- LangGraph: https://python.langchain.com/docs/langgraph/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- asyncpg: https://magicstack.github.io/asyncpg/
- LangSmith: https://www.langsmith.com/

