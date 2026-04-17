# Phase 2 — Add Transcription (v1 Complete)

## Context
Adds durable transcript storage on top of the working voice flow from Phase 1. After every completed turn, turns are written to Postgres (`interview_turns`) and appended to an S3 JSON file (`transcripts/{session_id}.json`). Live partial transcript captions are already streaming from Phase 1 — this phase just adds the persistence layer.

**Depends on:** Phase 1 being complete and working, including all three prerequisites (schema fix, DB tables, BE-012).

## What Phase 1 Provides (Reuse)
- `InterviewSession` with `status` managed in Phase 1
- `InterviewTurn` model — `backend/app/models/interview.py:126` — ready to insert
- WebSocket handler in `backend/app/routers/interview.py` — extend, don't rewrite
- `AmazonUtils` — `backend/app/utils/amazon_utils.py` — extend with JSON helpers
- `InterviewRepository` — `backend/app/repositories/interview.py` — extend with turn methods

## Files to Create / Modify

### 1. `backend/app/utils/amazon_utils.py` (modify) — `S3-TR-001`
Add to `AmazonUtils`:
```python
def upload_json(self, data: dict, bucket: str, key: str) -> None
    # json.dumps(data).encode("utf-8") → BytesIO → upload_fileobj

def download_json(self, bucket: str, key: str) -> dict
    # download_file_as_bytes → json.loads
```

### 2. `backend/app/services/transcript_s3_service.py` (new) — `S3-TR-002`
```
TranscriptS3Service
  create_transcript(session_id, user_id, started_at) -> str
    # uploads initial JSON { session_id, user_id, status: "in_progress", started_at, updated_at, turns: [] }
    # returns s3_key = f"transcripts/{session_id}.json"

  append_turn(s3_key, turn: InterviewTurn) -> None
    # download_json → append turn dict → upload_json (read-modify-write)

  finalize_transcript(s3_key, completed_at) -> None
    # download_json → set status="completed", updated_at=completed_at → upload_json
```
Bucket: `settings.S3_RESUME_BUCKET` (same bucket as resumes).

Turn dict shape appended to `turns[]`:
```json
{
  "turn_id": "...",
  "sequence_no": 1,
  "speaker_type": "interviewer",
  "turn_kind": "question",
  "content_text": "Tell me about yourself.",
  "is_final": true,
  "latency_ms": null,
  "created_at": "2026-04-17T10:00:05Z"
}
```

### 3. `backend/app/models/interview.py` (modify) — `S3-TR-003`
Add to `InterviewSession` (after `completed_at`):
```python
transcript_s3_key: Optional[str] = Field(
    default=None,
    sa_column=Column(String(512), nullable=True),
)
```

Migration SQL (run manually, no Alembic yet):
```sql
ALTER TABLE interview_sessions ADD COLUMN transcript_s3_key VARCHAR(512);
```

### 4. `backend/app/repositories/interview.py` (modify) — `S3-TR-003`
Add to `InterviewRepository`:
```python
async def create_turn(
    self,
    session_id: UUID,
    speaker_type: SpeakerType,
    turn_kind: TurnKind,
    sequence_no: int,
    content_text: str,
    latency_ms: int | None = None,
) -> InterviewTurn

async def get_recent_turns(self, session_id: UUID, n: int = 6) -> list[InterviewTurn]
    # SELECT ... ORDER BY sequence_no DESC LIMIT n → reversed to chronological order
```

### 5. `backend/app/routers/interview.py` (modify) — `S3-TR-004`
Extend the existing WebSocket handler and `POST /interview/start` from Phase 1.

**In `POST /interview/start`** — after `create_session`:
```python
s3_key = TranscriptS3Service().create_transcript(session_id, user_id, started_at)
await InterviewRepository(db).update_session(session_id, transcript_s3_key=s3_key)
# after generating opening AI question:
turn = await InterviewRepository(db).create_turn(session_id, SpeakerType.interviewer, ...)
TranscriptS3Service().append_turn(s3_key, turn)
```

**In WS handler — on utterance complete**:
```python
# candidate turn
turn = await InterviewRepository(db).create_turn(session_id, SpeakerType.candidate, ...)
TranscriptS3Service().append_turn(session.transcript_s3_key, turn)

# AI question turn
turn = await InterviewRepository(db).create_turn(session_id, SpeakerType.interviewer, ...)
TranscriptS3Service().append_turn(session.transcript_s3_key, turn)
```

**LLM context** (optional upgrade): replace in-memory `turns[-6:]` with:
```python
db_turns = await InterviewRepository(db).get_recent_turns(session_id, 6)
turns_for_llm = [{"speaker": t.speaker_type.value, "text": t.content_text} for t in db_turns]
```

**On session end**:
```python
TranscriptS3Service().finalize_transcript(session.transcript_s3_key, completed_at=datetime.utcnow())
```

## Migration
Before starting Phase 2, run:
```sql
ALTER TABLE interview_sessions ADD COLUMN transcript_s3_key VARCHAR(512);
```

## Verification
1. Complete a full interview session end-to-end
2. `SELECT * FROM interview_turns WHERE session_id = '<id>' ORDER BY sequence_no` → all turns present
3. Download `transcripts/{session_id}.json` from MinIO/S3 → all turns present, `status=completed`
4. Kill the server mid-interview → restart → S3 JSON has all turns up to the last completed one
5. `SELECT transcript_s3_key FROM interview_sessions WHERE id = '<id>'` → populated

---

## Engineering Breakdown Tickets

Tickets from `mock-interview-engineering-breakdown.md` covered by this phase. Mark these Done on completion.

### S3-TR-001 — Add JSON helpers to AmazonUtils
- `upload_json(data, bucket, key)` and `download_json(bucket, key)` on `AmazonUtils`
- **Depends on:** BE-011 ✅
- **Estimate:** 0.25 days

### S3-TR-002 — Build TranscriptS3Service
- `create_transcript`, `append_turn`, `finalize_transcript`
- S3 key: `transcripts/{session_id}.json`
- **Depends on:** S3-TR-001
- **Estimate:** 0.5 days

### S3-TR-003 — Add transcript_s3_key to interview_sessions
- Add nullable `VARCHAR(512)` column; update SQLModel; run migration SQL
- **Depends on:** DB-005 ✅
- **Estimate:** 0.25 days

### S3-TR-004 — Wire S3 + Postgres writes into WebSocket handler
- Per completed turn: `InterviewRepository.create_turn` + `TranscriptS3Service.append_turn`
- On session end: `finalize_transcript`
- **Depends on:** S3-TR-002, S3-TR-003, DB-006 ✅, RT-001
- **Estimate:** 2 days

### RT-004 — Add autosave support
- Each completed turn persisted to Postgres + S3 before next question is sent
- No turns lost on server restart between turns
- **Depends on:** DB-006 ✅, RT-003
- **Estimate:** 1 day

### RT-005 — Add reconnect support
- Client can rejoin active session; session state restored from Postgres turns
- No duplicate turns on reconnect
- **Depends on:** RT-004
- **Estimate:** 1 day

### BE-015 — Add interview sessions list and detail endpoints
- `GET /api/v1/interview` — list all sessions for current user, ordered by `created_at desc`
- `GET /api/v1/interview/{session_id}` — full detail: turns in sequence, JD, company, role
- **Depends on:** DB-005 ✅, DB-006 ✅
- **Estimate:** 0.5 days

### BE-018 — Add session restore endpoint
- `GET /api/v1/interview/{session_id}/state` — current transcript + status + last question
- Used by frontend on reconnect to rebuild session UI
- **Depends on:** RT-004
- **Estimate:** 0.5 days

### BE-020 — Add transcript history endpoint
- `GET /api/v1/interview/{session_id}/transcript` — full stored transcript for a completed session
- Returns turns in sequence order with speaker type and content
- **Depends on:** DB-006 ✅
- **Estimate:** 0.25 days
