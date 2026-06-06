# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands run from the `backend/` directory with the virtualenv active.

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in secrets before running

# Run dev server (API docs at http://localhost:8000/docs)
uvicorn app.main:app --reload

# Database migrations
alembic upgrade head           # apply all pending migrations
alembic downgrade -1           # rollback one migration
alembic revision -m "desc"     # generate new migration

# Tests
pip install -r requirements-dev.txt
pytest                         # run all tests
pytest tests/test_openai_utils.py  # run a single test file
```

## Architecture

This is a **FastAPI + PostgreSQL + Redis** backend for an AI-powered mock interview platform. There is no frontend in this repo.

### Request flow

```
HTTP/WebSocket → routers/ → services/ → repositories/ (DB) + utils/ (external APIs)
```

- **`routers/`** — thin HTTP/WebSocket handlers; delegate immediately to services
- **`services/`** — business logic; orchestrate DB access, AI calls, storage
- **`repositories/`** — data access layer wrapping AsyncSession queries
- **`utils/`** — external API clients (OpenAI, Cartesia TTS, Sarvam STT, AWS S3/MinIO)
- **`models/`** — SQLModel table definitions (also serve as Pydantic models)
- **`schemas/`** — request/response Pydantic models distinct from DB models
- **`core/configs.py`** — `pydantic-settings` config loaded from `.env`
- **`core/dependencies.py`** — FastAPI dependency injection (JWT auth, DB session)

### Interview session lifecycle

1. `POST /api/v1/interview/start` — creates an `InterviewSession` row; `services/prompt.py` assembles `interview_context_json` from the candidate's parsed resume + job description
2. `WebSocket /api/v1/interview/ws/{session_id}?token=...` — real-time interview loop:
   - Audio bytes → **Sarvam** (`utils/sarvam_utils.py`) → transcript text
   - Transcript → **OpenAI** (`utils/openai_utils.py`, streaming) → interviewer reply
   - Reply text → **Cartesia** (`utils/cartesia_utils.py`) → audio bytes → client
   - Each exchange persisted as `InterviewTurn` rows via `repositories/interview.py`
3. Session status transitions through `InterviewStatus` enum: `draft → in_progress → completed/cancelled`

### Key data model relationships

```
User → UserProfile
User → File (resume PDF / JD text, stored in S3/MinIO)
File → Resume (parsed JSON: skills, experience, education)
File → JobDescription
User + Resume + JobDescription → InterviewSession
InterviewSession → InterviewTurn[] (speaker_type: candidate/interviewer/system; turn_kind: question/answer/system_event)
```

### Environment & storage

- `ENV=dev` uses **MinIO** (local S3-compatible); `ENV=prod` uses **AWS S3** — toggled in `utils/amazon_utils.py`
- Redis is used for caching session context (`cache/redis_client.py`, `services/cache.py`)
- Prompt templates live as plain text files in `app/prompts/` (technical, behavioral, resume_based)

### Async patterns

The entire stack is async: `asyncpg` driver, SQLAlchemy `AsyncSession`, `async def` route handlers. Always use `await` for DB operations and propagate async through service/repository layers.
