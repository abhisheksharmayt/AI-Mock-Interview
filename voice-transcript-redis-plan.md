# Voice Transcript Storage Plan — Redis + Postgres

## 1. Purpose

This document defines the engineering approach for storing interview transcript data during a voice session. It covers the Redis scratchpad pattern for in-flight STT chunks and the per-turn Postgres write strategy for durable transcript storage.

This plan is a dependency for tickets: `DB-006`, `DB-012`, `VO-002`, `VO-003`, `RT-004`, `AI-008`

---

## 2. Context and Decision

Voice mode generates high-frequency STT fragments (partial transcripts every 100–300ms while the user speaks). Writing each fragment to Postgres would produce 5–10 DB writes per second per user — unacceptable for an interview session.

**Decision:** Use Redis as a scratchpad for in-flight audio chunks only. Write one final completed turn to Postgres per speaker exchange.

This is **not** a write-behind cache pattern. Redis is not a buffer for deferred Postgres writes. It is a temporary assembly area for partial STT data. Postgres is the source of truth for all completed turns.

---

## 3. Redis Key Schema

Two keys per active session. No other Redis keys are needed for transcript storage in MVP.

```
interview:chunks:{session_id}   → LIST
interview:turns:{session_id}    → LIST
```

### `interview:chunks:{session_id}` — LIST

Stores partial STT fragments as the user speaks. Ephemeral. Cleared after each utterance is assembled.

Each entry is a JSON string:
```json
{
  "chunk_id": "uuid",
  "text": "so I was working on",
  "is_final": false,
  "provider_seq": 3,
  "timestamp": "2026-04-14T10:23:11.312Z"
}
```

TTL: **1 hour** (sliding, refreshed on each RPUSH)

### `interview:turns:{session_id}` — LIST

Stores completed turns (AI questions + candidate answers) in order. Used to build AI context window without re-querying Postgres on every turn.

Each entry is a JSON string:
```json
{
  "turn_id": "uuid",
  "session_id": "uuid",
  "sequence_no": 4,
  "speaker_type": "assistant",
  "turn_kind": "question",
  "content_text": "Tell me about a time you debugged a production issue.",
  "is_final": true,
  "latency_ms": 312,
  "metadata_json": { "model": "claude-sonnet-4-6", "tokens": 48 },
  "created_at": "2026-04-14T10:23:11Z"
}
```

TTL: **4 hours** (sliding, refreshed on each RPUSH)

---

## 4. Write Flow (Per Turn)

### Step 1 — STT streaming (candidate speaks)

```
Audio chunk arrives (WebSocket / HTTP stream)
    ↓
STT provider returns partial transcript
    ↓
RPUSH interview:chunks:{session_id}  ← Redis only, no Postgres
EXPIRE interview:chunks:{session_id} 3600
    ↓
Broadcast partial transcript to frontend via WebSocket (transcript_updated event)
```

### Step 2 — Utterance complete (silence detected)

```
Silence threshold reached / end-of-utterance detected
    ↓
LRANGE interview:chunks:{session_id} 0 -1  ← assemble final text
    ↓
Final candidate turn text assembled
    ↓
INSERT INTO interview_turns (Postgres) ← one write, sync
RPUSH interview:turns:{session_id}     ← add to context cache
EXPIRE interview:turns:{session_id} 14400
DELETE interview:chunks:{session_id}   ← reset for next utterance
```

### Step 3 — AI responds

```
LRANGE interview:turns:{session_id} -6 -1  ← last 6 turns for LLM context
    ↓
Call LLM with context → get next question
    ↓
INSERT INTO interview_turns (Postgres) ← AI turn, sync
RPUSH interview:turns:{session_id}     ← add to context cache
EXPIRE interview:turns:{session_id} 14400
    ↓
Run TTS → return audio + transcript to frontend
```

---

## 5. Session Lifecycle

### On session start (`POST /api/v1/interview/start`)

```python
# No Redis keys created yet — lazy init on first chunk
# Create interview_sessions row in Postgres with status=in_progress
```

### On session end (`POST /api/v1/interview/{session_id}/end` or completion signal)

```python
# 1. Final Postgres flush — not needed since we write sync per turn
# 2. Update interview_sessions.status = completed, completed_at = now()
# 3. Delete Redis keys
await redis.delete(
    f"interview:turns:{session_id}",
    f"interview:chunks:{session_id}",
)
# 4. Trigger report generation
```

### On session abandon / crash

Redis TTL handles cleanup automatically (4h for turns, 1h for chunks). If the session is left `in_progress` in Postgres and TTL fires, a cleanup job can mark it `abandoned`. This is a Phase 3 concern — not needed for MVP.

---

## 6. Redis Configuration (MVP)

Use Redis defaults for MVP. No AOF config changes required.

When moving to production, enable:
```
appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes
```

---

## 7. Code Location

| Concern | Location |
|---|---|
| Redis LIST helpers (rpush, lrange, delete, expire) | `backend/app/cache/redis_client.py` |
| Chunk assembly logic | `backend/app/services/voice_service.py` |
| Turn persistence | `backend/app/services/interview_service.py` |
| Session cleanup on close | `backend/app/services/interview_service.py` |
| Context window builder | `backend/app/services/interview_orchestrator.py` |

---

## 8. Engineering Tickets

### `RT-REDIS-001` Extend Redis client with LIST operations

- Add `rpush`, `lrange`, `delete`, `expire` pipeline helpers to `redis_client.py`
- Add per-session key builders as constants or a helper: `chunks_key(session_id)`, `turns_key(session_id)`
- Do not change existing `set_cache` / `get_cache` string helpers — leave them intact
- **Depends on:** BE-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - `rpush_with_ttl(key, value, ttl)` appends to a LIST and refreshes TTL atomically via pipeline
  - `lrange_all(key)` returns all entries in the LIST
  - `delete_keys(*keys)` deletes one or more keys in a single call
  - All operations are async

### `RT-REDIS-002` Implement STT chunk buffer

- On each partial STT result: `RPUSH interview:chunks:{session_id}` + refresh TTL
- On utterance complete: `LRANGE` to assemble, then `DELETE` the key
- Return the assembled final text string
- **Depends on:** RT-REDIS-001, VO-003
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Partial chunks are buffered in Redis without any Postgres writes
  - Assembled text matches the concatenation of all final chunk texts in order
  - Chunk key is deleted after assembly

### `RT-REDIS-003` Implement turn context cache

- After each completed turn (AI or candidate): `RPUSH interview:turns:{session_id}` + refresh TTL
- Expose `get_recent_turns(session_id, n=6)` using `LRANGE -n -1` for LLM context building
- **Depends on:** RT-REDIS-001, DB-006
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - `get_recent_turns` returns the last N turns in order without a Postgres query
  - Turn cache is updated immediately after each INSERT into `interview_turns`

### `RT-REDIS-004` Add session cleanup on close

- On session complete or abandon: delete `interview:turns:{session_id}` and `interview:chunks:{session_id}`
- Call this from the session close path in `interview_service.py`
- **Depends on:** RT-REDIS-001, DB-005
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Both keys are deleted when a session is closed cleanly
  - Cleanup does not raise an error if keys have already expired

---

## 9. What Is Explicitly Out of Scope (MVP)

- ARQ background workers — not needed, turns are written sync
- Write-behind / deferred Postgres flush — not needed
- `interview:pending` queue — not needed
- Redis AOF config changes — defer to production hardening
- Keyspace notifications for abandoned sessions — Phase 3
- Redis Streams — not needed, single producer/consumer per session

---

## 10. Upgrade Path

When concurrent users or multi-region deployment becomes a concern:

1. Add ARQ worker for async Postgres writes (replace sync INSERT per turn)
2. Add `interview:pending:{session_id}` LIST as write-behind queue
3. Enable Redis AOF persistence
4. Consider Redis Streams if real-time evaluation pipeline needs fan-out to multiple consumers
