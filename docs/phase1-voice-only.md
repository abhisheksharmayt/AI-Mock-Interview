# Phase 1 — Voice Interview (No Transcription)

## Context
Get the end-to-end voice interview loop working first — session creation, opening question, candidate speaks, AI responds — with turns held in-memory only. No Postgres turn writes, no S3. This is the fastest path to a functional product. Transcription is added in Phase 2.

## Prerequisites (Must Be Done Before Phase 1)

These gaps exist in the codebase and must be resolved first:

### P0 — Fix `InterviewSessionCreate` schema (`backend/app/schemas/interview.py`)
The existing schema has `resume_text: str` and `job_description_text: str` but `InterviewSession` model requires `resume_id: UUID` and `job_description_id: UUID` (non-nullable FKs). Replace with:
```python
class InterviewSessionCreate(BaseModel):
    resume_id: UUID
    interview_type: str
    jd_raw_text: str
    company_name: str
    role: str
    question_count: int = 10
```

### P1 — Ensure DB tables exist
`InterviewSession` and `InterviewTurn` models are defined but no Alembic migrations exist. Run SQLModel `create_all()` or manually create tables before any interview endpoints are tested:
```python
# One-time in a script or startup hook:
from sqlmodel import SQLModel
from app.db.database import engine
SQLModel.metadata.create_all(engine)
```

### P2 — Implement `BE-012` (resume list endpoints)
`GET /api/v1/resume` and `GET /api/v1/resume/{id}` are still To Do. The interview start flow requires the frontend to have a `resume_id` — without this endpoint there is no way to fetch it. Add to `backend/app/routers/resume.py` before wiring up `POST /interview/start`.

---

## What Already Exists (Reuse)
- `InterviewSession` model — `backend/app/models/interview.py:32`
- `InterviewTurn` model — `backend/app/models/interview.py:126`
- `InterviewSessionCreate` schema — `backend/app/schemas/interview.py`
- `AmazonUtils` (for TTS audio upload) — `backend/app/utils/amazon_utils.py`
- `parse_resume_with_ai` pattern — `backend/app/utils/openai_utils.py` (reuse OpenAI call pattern)
- `get_current_user` dependency — `backend/app/core/dependencies.py`
- `get_db_session` dependency — `backend/app/db/database.py`
- Service/repository/router patterns from `backend/app/services/resume.py`, `backend/app/repositories/resume.py`
- `configs.py` — `S3_RESUME_BUCKET`, `OPENAI_API_KEY`

## Files to Create / Modify

### 1. `backend/app/prompts/behavioral.txt` (new)
### 2. `backend/app/prompts/technical.txt` (new)
### 3. `backend/app/prompts/resume_based.txt` (new)
Prompt templates with placeholders: `{{candidate_name}}`, `{{role}}`, `{{company_name}}`, `{{resume_summary}}`, `{{key_skills}}`, `{{years_of_experience}}`, `{{jd_highlights}}`

### 4. `backend/app/utils/openai_utils.py` (modify)
Add two new functions following the existing `parse_resume_with_ai` pattern:
- `generate_interview_question(system_prompt: str, turns: list[dict]) -> tuple[bool, str | None]`
  — sends system prompt + recent turns, returns `(done, question_text)`
- `text_to_speech(text: str) -> bytes`
  — calls OpenAI TTS API, returns audio bytes (mp3)

### 5. `backend/app/services/prompt_renderer.py` (new)
```
PromptRenderer
  render(interview_type: str, context: dict) -> str
```
Reads template file by `interview_type`, substitutes all `{{placeholders}}`, returns rendered string. Raises if any required placeholder is missing.

### 6. `backend/app/services/interview_context.py` (new)
```
InterviewContextAssembler
  build(resume_id, jd_id, user_id, db) -> dict
```
Queries `parsed_resumes`, `job_descriptions`, `users` tables and returns the context dict for `PromptRenderer`. Fails fast if resume `parse_status != completed`.

### 7. `backend/app/repositories/interview.py` (new)
```
InterviewRepository(db: AsyncSession)
  create_session(data) -> InterviewSession
  get_session(session_id, user_id) -> InterviewSession | None
  update_session(session_id, **fields) -> InterviewSession
```
No turn persistence in Phase 1.

### 8. `backend/app/services/interview.py` (new)
```
InterviewService
  start_session(user, resume_id, jd_id, interview_type, db) -> dict
    1. InterviewContextAssembler.build(...)
    2. PromptRenderer.render(interview_type, context)
    3. InterviewRepository.create_session(status=in_progress, interview_context_json=rendered_prompt)
    4. generate_interview_question(system_prompt, turns=[])
    5. text_to_speech(question_text) → audio bytes
    6. AmazonUtils.upload_file_as_object(audio_bytes, bucket, key=f"audio/{session_id}/0.mp3")
    7. return { session_id, question_text, audio_url }
```

### 9. `backend/app/routers/interview.py` (new)
- `POST /interview/start` → calls `InterviewService.start_session`
- `WS /ws/interview/{session_id}` — WebSocket handler:
  - On connect: verify JWT, load session, init `turns: list[dict] = []`, `chunks: list[str] = []`
  - On `{"type": "audio_chunk", "data": "<base64>"}`:
    - Decode audio, call OpenAI STT (`client.audio.transcriptions.create`) → partial text
    - Append to `chunks`
    - Send `{"type": "transcript_partial", "text": partial_text}` back
  - On `{"type": "end_utterance"}`:
    - Assemble `chunks` → `answer_text`, clear `chunks`
    - Append candidate turn to `turns` in-memory
    - Call `generate_interview_question(system_prompt, turns[-6:])` → `(done, question)`
    - If done: send `{"type": "session_completed"}`, update session `status=completed`, close WS
    - Else: `text_to_speech(question)` → upload audio → send `{"type": "ai_question", "text": ..., "audio_url": ...}`
    - Append AI turn to `turns`
  - On disconnect: update session `status=abandoned` if still in_progress

### 10. `backend/app/routers/routes.py` (modify)
Register `interview_router` with prefix `/interview`.

### 11. `backend/app/main.py` (modify)
Register WebSocket route directly on `app` (FastAPI WebSocket routes need to be on the app, not a prefixed sub-router).

## In-Memory Turn Format
```python
{"speaker": "interviewer", "text": "Tell me about yourself."}
{"speaker": "candidate",   "text": "I have 5 years of backend experience..."}
```
Last 6 entries passed to `generate_interview_question` for LLM context.

## Completion Signal
LLM returns structured JSON:
```json
{"done": false, "question": "What was your biggest challenge?"}
{"done": true,  "question": null}
```
`generate_interview_question` parses this and returns `(done: bool, question: str | None)`.

## Verification
1. `POST /api/v1/interview/start` → returns `session_id`, `question_text`, `audio_url`
2. Connect `WS /ws/interview/{session_id}` with JWT token
3. Send `{"type": "audio_chunk", "data": "..."}` → receive `transcript_partial`
4. Send `{"type": "end_utterance"}` → receive `ai_question` with next question + audio URL
5. After max turns → receive `session_completed`
6. `interview_sessions` row has `status=completed` in Postgres

---

## Engineering Breakdown Tickets

Tickets from `mock-interview-engineering-breakdown.md` covered by this phase. Mark these Done on completion.

### BE-012 — Add resume list and status endpoints *(prerequisite)*
- `GET /api/v1/resume` — all resumes for current user, ordered by `created_at desc`
- `GET /api/v1/resume/{id}` — single resume with `parse_status`
- Add to `backend/app/routers/resume.py`, reuse `ResumeRepository`
- **Depends on:** BE-009 ✅
- **Estimate:** 0.5 days

### AI-006 — Build prompt template system
- Create `behavioral.txt`, `technical.txt`, `resume_based.txt` in `backend/app/prompts/`
- Build `PromptRenderer.render(interview_type, context) -> str`
- Rendered prompt stored in `interview_sessions.interview_context_json`
- **Depends on:** AI-001 ✅
- **Estimate:** 1 day

### AI-007 — Build interview context assembler
- `InterviewContextAssembler.build(resume_id, jd_id, user_id, db) -> dict`
- Queries `parsed_resumes`, `job_descriptions`, `users` — fails fast if parse_status != completed
- **Depends on:** AI-006, DB-003 ✅, DB-002 ✅
- **Estimate:** 0.5 days

### AI-008 — Build interview session orchestrator
- `generate_interview_question(system_prompt, turns)` — calls LLM, parses completion signal
- In-memory turns list as context (Phase 1), Postgres query in Phase 2
- **Depends on:** AI-007, DB-005 ✅, DB-006 ✅
- **Estimate:** 2 days

### AI-009 — Add completion guardrails
- Enforce max turn count hard stop regardless of LLM completion signal
- **Depends on:** AI-008
- **Estimate:** 0.25 days

### BE-013 — Add interview start endpoint
- `POST /api/v1/interview/start` — creates session, calls LLM for opening question, runs TTS, returns `{session_id, question_text, audio_url}`
- Returns 409 if resume not parsed, 404 if resume not owned by user
- **Depends on:** AI-008, DB-005 ✅
- **Estimate:** 1 day

### RT-001 — Add WebSocket connection manager
- `WS /ws/interview/{session_id}` — authenticate via JWT, track active connection, clean up on disconnect
- **Depends on:** BE-007 ✅
- **Estimate:** 1.5 days

### RT-002 — Define realtime event contract
- Document payload shapes: `transcript_partial`, `ai_question`, `session_completed`, `error`
- All events include `type` field
- **Depends on:** RT-001
- **Estimate:** 0.5 days

### RT-003 — Implement interview event publisher
- Broadcast events to the correct WS connection during active interview
- **Depends on:** RT-002, AI-008
- **Estimate:** 1 day

### VO-001 — Define audio stream strategy
- Audio streamed as base64 chunks via WebSocket; silence detection client-side triggers `end_utterance`
- Accepted format: PCM/WAV/WebM; max chunk size TBD
- **Depends on:** None
- **Estimate:** 0.5 days

### VO-002 — Build speech ingestion interface
- Accept `audio_chunk` messages via WS, buffer in-memory list, assemble on `end_utterance`
- **Depends on:** VO-001, DB-006 ✅
- **Estimate:** 1 day

### VO-003 — Integrate STT provider
- Call `client.audio.transcriptions.create` (OpenAI Whisper) on assembled audio bytes
- Return partial text per chunk for live captions
- **Depends on:** VO-002
- **Estimate:** 1.5 days

### VO-005 — Integrate TTS provider
- Call OpenAI TTS API, upload mp3 bytes to S3 under `audio/{session_id}/{seq}.mp3`
- Return `audio_url` pre-signed or direct path
- **Depends on:** AI-008
- **Estimate:** 1.5 days
