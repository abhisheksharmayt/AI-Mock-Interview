# Voice Transcript Storage Plan — S3 + Postgres + In-Memory Buffer

## 1. Purpose

This document defines the engineering approach for storing interview transcript data during a voice session. It covers the in-memory buffer pattern for in-flight STT chunks, the per-turn Postgres write strategy, and the S3 JSON archive that provides durability across abrupt disconnects.

This plan is a dependency for tickets: `DB-006`, `DB-012`, `VO-002`, `VO-003`, `RT-004`, `AI-006`, `AI-007`, `AI-008`, `AI-009`, `BE-013`, `S3-TR-001`, `S3-TR-002`, `S3-TR-003`, `S3-TR-004`

---

## 2. Context and Decision

Voice mode generates high-frequency STT fragments (partial transcripts every 100–300ms while the user speaks). Writing each fragment to Postgres would produce 5–10 DB writes per second per user — unacceptable for an interview session.

**Decision:** Use an in-memory buffer (Python list in the WebSocket handler) as a scratchpad for in-flight audio chunks. Write one final completed turn to Postgres per speaker exchange. After every completed turn, also write/update an S3 JSON file so the full transcript is durable even if the connection drops before the session is formally closed.

This is **not** a write-behind cache pattern. Postgres is the source of truth for all completed turns. S3 JSON is a portable, durable per-session archive that mirrors Postgres turns and is always up-to-date.

**Redis is not used for transcript storage.** Redis (`set_cache`/`get_cache`) remains available for other basic caching needs but has no role in the interview transcript flow.

---

## 3. S3 Transcript Schema

### Key Pattern

```
transcripts/{session_id}.json
```

Stored in the same S3 bucket as resumes (`settings.S3_BUCKET`).

### JSON Structure

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "...",
  "status": "in_progress",
  "started_at": "2026-04-17T10:00:00Z",
  "updated_at": "2026-04-17T10:05:00Z",
  "turns": [
    {
      "turn_id": "...",
      "sequence_no": 1,
      "speaker_type": "interviewer",
      "turn_kind": "question",
      "content_text": "Tell me about yourself.",
      "is_final": true,
      "latency_ms": null,
      "created_at": "2026-04-17T10:00:05Z"
    },
    {
      "turn_id": "...",
      "sequence_no": 2,
      "speaker_type": "candidate",
      "turn_kind": "answer",
      "content_text": "I have five years of backend experience...",
      "is_final": true,
      "latency_ms": null,
      "created_at": "2026-04-17T10:01:30Z"
    }
  ]
}
```

The `updated_at` field is refreshed on every `append_turn` call. `status` is `in_progress` during the session and `completed` (or `abandoned`) after close.

---

## 4. Full Interview Flow (Post Session Start)

### Phase 1 — Session Bootstrap (HTTP)

```
POST /api/v1/interview/start
  { resume_id, interview_type, jd, company_name, role }
         ↓
1. Load parsed_resume from DB
2. Create job_descriptions row
3. Select prompt template by interview_type
   (behavioral.txt / technical.txt / resume_based.txt)
4. Inject dynamic values into template:
   - {{candidate_name}}, {{role}}, {{company_name}}
   - {{resume_summary}}, {{key_skills}}, {{years_of_experience}}
   - {{jd_highlights}}
5. Create interview_sessions row
   - status = in_progress
   - interview_context_json = { rendered_system_prompt, resume_summary, role, company }
   - transcript_s3_key = None (set in step 6)
6. Create S3 transcript doc → transcripts/{session_id}.json
   - UPDATE interview_sessions SET transcript_s3_key = 'transcripts/{session_id}.json'
7. Call LLM (system prompt only) → opening question text
8. TTS → convert opening question to audio
9. INSERT AI turn → interview_turns (Postgres)
10. Append AI turn → S3 transcript JSON
         ↓
Response: { session_id, question_text, audio_url }
```

---

### Phase 2 — Live Voice Turn Cycle (WebSocket)

WebSocket: `WS /ws/interview/{session_id}`

```
─── Candidate receives opening question audio ───

CANDIDATE SPEAKS:
  Audio chunks arrive via WebSocket
      ↓
  STT partial results
      ↓
  Append to in-memory chunk buffer (Python list, local to WS handler)
  Send {"type": "transcript_partial", "text": "..."} → frontend (live caption)
      ↓
  Silence threshold / end-of-utterance detected
      ↓
  Assemble final text from in-memory buffer → clear buffer
      ↓
  INSERT candidate turn → interview_turns (Postgres)  ← one write, sync
  Append turn → S3 transcript JSON                    ← durability write

AI RESPONDS:
      ↓
  SELECT * FROM interview_turns WHERE session_id = ? ORDER BY sequence_no DESC LIMIT 6
  (last 6 turns for LLM context — no Redis, direct Postgres query)
      ↓
  Call LLM (rendered system prompt + recent turns)
      ↓
  ┌────────────────────────────────────────┐
  │  LLM returns next question             │ → continue turn cycle
  │  LLM signals completion                │ → go to Phase 3
  └────────────────────────────────────────┘
      ↓ (next question path)
  TTS → audio
  INSERT AI turn → interview_turns (Postgres)
  Append AI turn → S3 transcript JSON
  Send { question_text, audio_url } via WebSocket
      ↓
  Repeat from CANDIDATE SPEAKS
```

---

### Phase 3 — Session Close

```
LLM signals completion  OR  max turn count reached  OR  WebSocket disconnects
         ↓
1. Send session_completed event to frontend via WebSocket (if connection alive)
2. UPDATE interview_sessions SET status=completed, completed_at=now()
3. Finalize S3 transcript JSON → set status=completed, updated_at=now()
4. Close WebSocket connection
5. Trigger report generation (async background task)
         ↓
Frontend polls: GET /api/v1/interview/{session_id}/report
```

---

### Safety Nets

| Scenario | Handler |
|---|---|
| LLM never signals completion | Max turn count hard stop |
| Candidate silent too long | Silence timeout → send reprompt event via WS |
| WebSocket disconnects mid-session | S3 JSON has all turns up to last completed one; reconnect reads from Postgres |
| Server restarts mid-utterance | In-memory buffer lost (~seconds of in-progress speech); candidate must re-speak; all *completed* turns are safe in Postgres + S3 |
| Session left in_progress after crash | Cleanup job marks as abandoned; S3 transcript already reflects all turns written |

---

## 5. Prompt Template System

### Template Location

```
backend/app/prompts/
    behavioral.txt
    technical.txt
    resume_based.txt
```

### Template Variables

Each template contains placeholders injected at session start:

| Variable | Source |
|---|---|
| `{{candidate_name}}` | `users.full_name` |
| `{{role}}` | `job_descriptions.role` |
| `{{company_name}}` | `job_descriptions.company_name` |
| `{{resume_summary}}` | `parsed_resumes.candidate_summary` |
| `{{key_skills}}` | `parsed_resumes.skills_json` (top N) |
| `{{years_of_experience}}` | `parsed_resumes.total_years_experience` |
| `{{jd_highlights}}` | `job_descriptions.raw_text` (first 500 chars or LLM-extracted) |

### LLM Decision Responsibility

The LLM controls the interview using the rendered system prompt. It decides:
- Which topic to cover next
- Whether to follow up or move on
- When the interview is complete (via a structured completion signal)

Max turn count is the only hard guardrail enforced by the application — not the LLM.

### Rendered Prompt Storage

The final rendered system prompt is stored in `interview_sessions.interview_context_json` at session start. Every LLM call for that session uses this stored prompt — no re-rendering mid-session.

---

## 6. Write Flow (Per Turn)

### Step 1 — STT streaming (candidate speaks)

```
Audio chunk arrives (WebSocket)
    ↓
STT provider returns partial transcript
    ↓
Append text to in-memory buffer (list in WS handler scope)
    ↓
Send {"type": "transcript_partial", "text": "..."} to frontend via WebSocket
```

### Step 2 — Utterance complete (silence detected)

```
Silence threshold reached / end-of-utterance detected
    ↓
Assemble final text by joining in-memory buffer entries
    ↓
Clear in-memory buffer
    ↓
INSERT INTO interview_turns (Postgres)  ← one write, sync
TranscriptS3Service.append_turn(s3_key, turn)  ← read-modify-write on S3 JSON
```

### Step 3 — AI responds

```
SELECT last 6 turns FROM interview_turns WHERE session_id = ?  ← Postgres query
    ↓
Call LLM with context → get next question
    ↓
INSERT INTO interview_turns (Postgres)  ← AI turn, sync
TranscriptS3Service.append_turn(s3_key, turn)  ← update S3 JSON
    ↓
Run TTS → return audio + transcript to frontend
```

---

## 7. Session Lifecycle

### On session start (`POST /api/v1/interview/start`)

```python
# 1. Create interview_sessions row (transcript_s3_key = None initially)
# 2. TranscriptS3Service.create_transcript(session_id, user_id, started_at)
#    → uploads initial JSON to S3, returns s3_key
# 3. UPDATE interview_sessions SET transcript_s3_key = s3_key
```

### On session end (completion signal or WS disconnect)

```python
# 1. UPDATE interview_sessions SET status=completed, completed_at=now()
# 2. TranscriptS3Service.finalize_transcript(s3_key, completed_at=now())
#    → downloads JSON, sets status=completed, re-uploads
# 3. Trigger report generation background task
```

### On session abandon / crash

S3 JSON is written after every completed turn, so it always reflects the latest durable state. A cleanup job can mark abandoned sessions in Postgres; the S3 archive is already complete for all turns written before the crash.

---

## 8. WebSocket Message Protocol

```
// Client → Server
{"type": "audio_chunk", "data": "<base64-encoded PCM>"}
{"type": "end_utterance"}   // optional explicit signal (silence detection preferred)

// Server → Client
{"type": "transcript_partial", "text": "tell me about..."}         // live captions
{"type": "transcript_final", "sequence_no": 2, "turn_id": "..."}   // turn persisted to Postgres + S3
{"type": "session_completed"}                                       // interview finished
{"type": "error", "message": "..."}
```

---

## 9. Code Locations

| Concern | Location |
|---|---|
| S3 JSON helpers (`upload_json`, `download_json`) | `backend/app/utils/amazon_utils.py` |
| Transcript S3 service (create / append / finalize) | `backend/app/services/transcript_s3_service.py` |
| In-memory chunk assembly | `backend/app/routers/interview_ws.py` (local to WS handler) |
| Turn persistence | `backend/app/services/interview_service.py` |
| LLM context builder (last N turns from Postgres) | `backend/app/services/interview_orchestrator.py` |
| Session close / cleanup | `backend/app/services/interview_service.py` |

---

## 10. Engineering Tickets

### `S3-TR-001` Add JSON helpers to AmazonUtils

- Add `upload_json(data: dict, bucket: str, key: str) -> None` — serializes to UTF-8 JSON bytes and uploads
- Add `download_json(bucket: str, key: str) -> dict` — downloads and deserializes
- **Depends on:** BE-011
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - `upload_json` followed by `download_json` round-trips a dict without data loss
  - Both methods work against MinIO in local dev and AWS S3 in production

### `S3-TR-002` Build TranscriptS3Service

- `create_transcript(session_id, user_id, started_at) -> str` — creates initial JSON, returns s3_key
- `append_turn(s3_key, turn) -> None` — read-modify-write: download JSON, append turn, re-upload
- `finalize_transcript(s3_key, completed_at) -> None` — download JSON, set status=completed, re-upload
- **Depends on:** S3-TR-001
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - After `create_transcript`, downloading the S3 key returns a valid JSON doc with an empty `turns` array
  - Each `append_turn` call adds the turn to the array and refreshes `updated_at`
  - `finalize_transcript` sets `status` to `completed`
  - If the S3 key does not exist, `append_turn` raises a clear error

### `S3-TR-003` Add transcript_s3_key to interview_sessions

- Add `transcript_s3_key VARCHAR(512)` column to `interview_sessions`
- Migration SQL: `ALTER TABLE interview_sessions ADD COLUMN transcript_s3_key VARCHAR(512);`
- Update `InterviewSession` SQLModel: add `transcript_s3_key: Optional[str]` field
- **Depends on:** DB-005
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Column exists after migration
  - Column is nullable (sessions in draft state before S3 doc is created)
  - `transcript_s3_key` is populated on the session row immediately after `create_transcript`

### `S3-TR-004` WebSocket handler with in-memory buffer + S3 per-turn write

- `WS /ws/interview/{session_id}` — authenticate via JWT, load session
- On connect: call `TranscriptS3Service.create_transcript(...)` if `transcript_s3_key` is None
- On `audio_chunk`: append STT partial to in-memory list, send `transcript_partial` to client
- On utterance complete: assemble from buffer, clear buffer, INSERT Postgres, `append_turn` to S3, send `transcript_final`
- On disconnect / completion: `finalize_transcript`, update session status
- **Depends on:** S3-TR-002, S3-TR-003, DB-006, RT-001
- **Estimate:** 2 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Client receives `transcript_partial` events for each STT chunk
  - After utterance complete, `interview_turns` has the new row and S3 JSON includes it
  - Simulating a disconnect mid-interview and re-downloading the S3 JSON shows all completed turns
  - Reconnecting to an in-progress session does not duplicate turns

---

## 11. What Is Explicitly Out of Scope (MVP)

- Redis LIST operations for transcript buffering
- ARQ background workers — turns are written sync
- Write-behind / deferred Postgres flush
- S3 cross-region replication
- Per-chunk S3 writes (only per-turn)
- `transcript_chunks` Postgres table during live sessions (Phase 6 only — post-session audit)
- Redis AOF / persistence config for transcript data
- Redis Streams
