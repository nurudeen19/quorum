# Quorum Project — Copilot Instructions

## Code Quality & Best Practices

- Prefer simplicity and readability over cleverness.
- Do not over-engineer; implement only what the current requirements demand.
- Follow the DRY principle — avoid duplicated logic across modules.
- Use meaningful, intention-revealing names for variables, functions, and classes.
- Keep functions small and focused; extract reusable helpers when a function grows beyond ~30 lines.
- Write unit tests for all critical functions and integration tests for every API endpoint.
- Consult the official documentation for any third-party library before implementing non-trivial usage.
- Never use `print()` in production code — use the standard `logging` library with appropriate log levels.

## Architecture & Design

- Use a modular, layered architecture.
- All I/O-bound operations (database, HTTP, file) MUST be `async`.
- Use FastAPI's `Depends()` for injecting database sessions, authentication context, and service instances.
- Use Pydantic models for all request validation and response serialization — never return raw ORM objects from endpoints.
- Use `pydantic-settings` (or `BaseSettings`) for all environment and configuration management; never hardcode secrets or config values.

## Python Coding Standards

- Always annotate with strict type hints. Use Python 3.10+ style: `list[str]`, `dict[str, int]`, `str | None`.
- Organise imports into three clearly separated groups: (1) standard library, (2) third-party, (3) local modules.
- Write Google-style docstrings for all public functions, classes, and modules.
- Prefer `pathlib.Path` over `os.path` for filesystem operations.
- Use Pydantic models for structured data; avoid plain `dict` as a substitute for typed objects.
- Avoid mutable default arguments (`def f(items=[])`) — use `None` with a guard instead.

## Database & Async Patterns

- Always use `async with session.begin()` or dependency-injected sessions with explicit commit/rollback boundaries.
- Never call synchronous blocking functions (e.g., `time.sleep`, sync ORM queries) inside an `async` function — use `asyncio.sleep` and async-native equivalents.
- Use `selectinload` / `joinedload` explicitly to avoid N+1 query problems; do not rely on lazy loading with async sessions.
- Keep database migrations atomic and reversible; every `upgrade()` must have a corresponding `downgrade()`.

## API Design

- Version all public APIs under a prefix (e.g., `/api/v1/`).
- Use plural nouns for resource routes (`/users`, `/documents`), not verbs.
- Return consistent envelope shapes for errors (use a shared `ErrorResponse` Pydantic model).
- Document every endpoint with a `summary`, `description`, and response examples in the route decorator.
- Add `Field(alias=..., examples=[...])` to Pydantic fields for accurate Swagger UI documentation.

## Error Handling & Validation

- Use `fastapi.HTTPException` for all client-facing errors (4xx).
- Register global exception handlers for unhandled server errors (5xx) so the client always receives a structured JSON response.
- Always wrap external service calls (LLMs, third-party APIs) in `try/except` with specific exception types; never let raw provider errors reach the client.
- Never expose stack traces, internal paths, or sensitive config values in error responses or logs.
- Log errors at `ERROR` level with context (request ID, user ID where available) but sanitise PII before logging.

## Security

- Validate and sanitise all user-supplied input before passing it to the database or any external service.
- Store passwords using `argon2`; never plain text or reversible encryption.
- Set short JWT expiry times; implement refresh-token rotation.
- Apply rate limiting on auth endpoints.

## Testing Standards

- Maintain a minimum of 80% test coverage across the codebase.
- Use `pytest-asyncio` for async test functions.
- Mock external services (LLMs providers) in unit and integration tests — do not call live APIs in CI.
- Use factory fixtures (e.g., `pytest-factoryboy` or plain fixture functions) to generate test data consistently.
- Name tests descriptively: `test_<function>_<scenario>_<expected_outcome>`.
