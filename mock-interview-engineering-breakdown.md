# AI Mock Interview Platform Engineering Task Breakdown

## 1. Purpose

This document converts the PRD into an engineering execution breakdown. It is written so work can be split into tickets with clear ownership and dependencies.

## 2. Suggested Workstreams

- Backend platform
- Data model and persistence
- LLM and interview orchestration
- File ingestion and parsing
- Realtime session layer
- Voice pipeline
- Analytics and reporting
- Productization and external APIs

## 3. Ticket Format Recommendation

Each task should be created with:
- title
- summary
- owner
- dependency
- acceptance criteria
- estimate
- status

Recommended ticket prefixing:
- `BE` for backend API
- `DB` for schema and migrations
- `AI` for LLM and evaluation logic
- `RT` for realtime work
- `VO` for voice work
- `AN` for analytics
- `PLT` for platform and integration work

## 4. Phase 0: Foundation and Scope Lock

### Goal
Create enough clarity that engineering can execute without reworking the product definition every few days.

### Tasks

#### `PLT-001` Create project conventions
- Define repo structure, naming conventions, and branching strategy
- Define environment variable strategy including how secrets are loaded per environment
- Define local development setup including how to run the stack from scratch
- Define migration workflow — when to create migrations, how to apply them, and how to roll back
- **Depends on:** None
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - A conventions doc or README section exists covering repo layout, branching, and env var strategy
  - A new engineer can set up the project locally by following the guide without asking questions

#### `PLT-002` Create architecture notes
- Document modular monolith boundaries and explain why this structure was chosen over microservices
- Define the responsibility of each service and module
- Define where interview engine logic lives and how it stays decoupled from transport (voice, WebSocket, REST)
- **Depends on:** PLT-001
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - Module boundaries are documented with a clear owner for each domain
  - Interview engine logic location is decided and written down

#### `PLT-003` Define event and schema naming rules
- Standardize API response shape for success and error cases
- Standardize WebSocket event naming convention
- Standardize database table and column naming rules
- **Depends on:** PLT-001
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - A reference doc exists with naming examples for API responses, WebSocket events, and DB fields
  - All existing endpoints and tables conform to the convention

#### `PLT-004` Create backlog labels and milestone mapping
- Define phase labels aligned with PRD phases
- Define workstream labels aligned with this breakdown
- Define priority labels
- **Depends on:** None
- **Estimate:** 0.25 days
- **Status:** Done
- **Acceptance Criteria:**
  - Labels exist in the project management tool
  - All Phase 1 tickets are labeled and assigned to the correct milestone

### Exit Criteria
- Engineering setup conventions exist
- Scope boundaries are documented
- Team can begin implementation with stable names and module boundaries

## 5. Phase 1: Core MVP

### Goal
Ship a complete voice-first personalized interview flow.

> **Constraint:** Because the product is voice-first, the minimum required realtime and voice tasks from Phases 3 and 4 must be pulled forward into MVP execution. Do not defer all voice and WebSocket work — the product is not shippable without them.

### Workstream A: Backend Bootstrap

#### `BE-001` Initialize FastAPI application
- Create the FastAPI app entrypoint with lifespan management
- Add config loading from environment variables using pydantic-settings
- Add a `GET /health` endpoint that returns app status
- Add base router structure with versioned prefix (`/api/v1`)
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - App starts without errors
  - `GET /api/v1/health` returns 200
  - Routers are registered and reachable

#### `BE-002` Set up project settings
- Add environment-specific settings class using pydantic BaseSettings
- Add secrets loading via `.env` file for local and environment variables for production
- Add a single config object imported across the app
- **Depends on:** BE-001
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - Config object loads values from `.env` in development and from real env vars in production
  - Missing required config values raise a clear error at startup

#### `BE-003` Add logging and error handling
- Add structured request logging using loguru or equivalent
- Add a global exception handler that catches unhandled errors and returns a standard error response
- Add a standard API error response format used across all endpoints
- **Depends on:** BE-001
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - All requests are logged with method, path, and status code
  - Unhandled exceptions return a JSON error response instead of a 500 stack trace
  - Error response shape is consistent across all endpoints

#### `BE-004` Add database connection layer
- Configure async Postgres connection using asyncpg
- Add async session factory and a `get_db_session` FastAPI dependency
- Add Alembic migration setup with an initial migration
- **Depends on:** BE-002
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - App connects to Postgres on startup
  - `get_db_session` dependency injects a valid async session into route handlers
  - `alembic upgrade head` runs without errors on a fresh database

#### `BE-005` Add Redis integration
- Configure Redis client using the URL from config
- Add a reusable cache helper and a queue config placeholder for future Celery use
- **Depends on:** BE-002
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - App connects to Redis on startup
  - Cache helper can get and set keys
  - Connection failure on startup raises a clear error
- **Note:** Redis LIST operations for voice transcript buffering are extended in `RT-REDIS-001`. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) for the full approach.

### Workstream B: Auth and User Core

#### `BE-006` Create user model
- Add user table with id, email, hashed password, full name
- Add created_at and updated_at timestamps
- Add unique index on email
- **Depends on:** BE-004
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - User table exists in the database after migration
  - Email uniqueness is enforced at the DB level

#### `BE-007` Implement auth flows
- Signup endpoint — validate email uniqueness, hash password, create user
- Login endpoint — verify credentials, return JWT access token
- Token generation and validation using HS256
- Auth dependency for protected routes that extracts and validates the token
- **Depends on:** BE-006
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - `POST /api/v1/auth/signup` creates a user and returns a token
  - `POST /api/v1/auth/login` returns a token for valid credentials and 401 for invalid ones
  - Protected routes return 401 when no token or an invalid token is provided

#### `BE-008` Add current user endpoint
- `GET /api/v1/user/me` returns the authenticated user's profile
- Uses the auth dependency to identify the caller
- **Depends on:** BE-007
- **Estimate:** 0.25 days
- **Status:** Done
- **Acceptance Criteria:**
  - Returns 200 with user profile for a valid token
  - Returns 401 for missing or expired token

### Workstream C: Resume and JD Intake

#### `DB-001` Create resume and file tables
- Create a files table linked to user storing storage key, original filename, mime type, file size, and file kind enum
- Create a resumes table linked to user and file storing parse_status enum (pending, processing, completed, failed) and is_default flag
- Add indexes on user_id and parse_status
- **Depends on:** BE-006
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - Both tables exist after migration
  - parse_status defaults to pending on insert
  - Foreign key constraints are enforced

#### `DB-002` Create JD table
- Create a job_descriptions table linked to user storing company_name, role, and raw_text
- JD is text-only input — no file upload in v1
- company_name and role are required fields, not optional metadata
- **Depends on:** BE-006
- **Estimate:** 0.5 days
- **Status:** Migration update needed — add `role not null`, make `company_name not null`, drop `title`/`source_url`/`parse_status`
- **Acceptance Criteria:**
  - Table exists after migration
  - company_name and role fields are non-nullable
  - Raw text field can hold large JD content without truncation

#### `BE-009` Add resume upload endpoint
- `POST /api/v1/resume/upload` accepts a file upload
- Validate file extension — allow only .pdf and .docx
- Upload file bytes to S3 under the resumes/ prefix
- Create File and Resume records in a single transaction
- Roll back the S3 object if the DB insert fails
- Trigger background parse task after record is created
- Return 400 for invalid extension, 503 for storage failure
- **Depends on:** DB-001, BE-011
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - Valid file uploads return 200 with resume id
  - File is present in S3 and a Resume record exists with parse_status=pending
  - Invalid file types return 400
  - S3 object is cleaned up if the DB insert fails

#### `BE-010` Add JD create endpoint
- `POST /api/v1/resume/jd` accepts company_name, role, and raw_text (all required)
- Save to job_descriptions table
- Return the created JD record id
- **Depends on:** DB-002
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - Valid request creates a JD record and returns it
  - Missing company_name, role, or raw_text returns 422

#### `BE-011` Add storage abstraction
- Abstract S3 operations behind an `AmazonUtils` class with upload, download, and delete methods
- Use MinIO for local development and real AWS S3 in production, controlled by the ENV config value
- **Depends on:** BE-002
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - Files can be uploaded and downloaded via the abstraction in both local and production environments
  - Delete is called on cleanup paths without raising unhandled errors

#### `BE-012` Add resume list and status endpoints
- `GET /api/v1/resume` returns all resumes for the current user — used to populate the home screen resume list inline
- `GET /api/v1/resume/{id}` returns a single resume record including current parse_status
- Return 404 if the resume does not exist or does not belong to the current user
- **Depends on:** BE-009
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - List endpoint returns all resumes for the current user ordered by created_at desc
  - Detail endpoint returns 200 with resume record including parse_status field
  - Returns 404 for unknown or unauthorized resume id
  - Frontend uses the list to show resumes inline on the home screen

### Workstream D: Parsing Pipeline

#### `AI-001` Define parsed resume schema
- Define the structured output schema for a parsed resume including skills, experience entries, projects, education, certifications, candidate summary, and total years of experience
- Each field should have a clear type and handle missing data gracefully with empty arrays or null
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - Pydantic schema exists and can be validated from an OpenAI JSON response
  - Missing optional fields do not raise validation errors

#### `AI-003` Implement resume parsing service
- Extract text from the uploaded file using pdfplumber for PDF and python-docx for DOCX
- Call OpenAI with the extraction prompt and parse the structured JSON response
- Store the result in the parsed_resumes table
- Transition parse_status: pending → processing → completed or failed
- **Depends on:** AI-001, DB-003
- **Estimate:** 2 days
- **Status:** Done
- **Acceptance Criteria:**
  - A valid PDF or DOCX produces a populated parsed_resumes row
  - parse_status is set to completed on success and failed on any error
  - No partial rows are left on failure

#### `DB-003` Create parsed resume table
- Store full_text, candidate_summary, total_years_experience
- Store skills_json, experience_json, education_json, projects_json, certifications_json as JSONB
- Enforce unique constraint on resume_id — one parsed output per resume
- Cascade delete when the parent resume is deleted
- **Depends on:** DB-001
- **Estimate:** 0.5 days
- **Status:** Done
- **Acceptance Criteria:**
  - Table exists after migration
  - Inserting a second parsed resume for the same resume_id raises a constraint error

#### `AI-005` Add parser job orchestration
- Trigger resume parse via FastAPI BackgroundTasks after upload
- Track full parse_status lifecycle: pending → processing → completed or failed
- Failed parses set parse_status=failed with no partial rows left in parsed_resumes
- **Note:** FastAPI BackgroundTasks has no built-in retry support. Failed parses require a manual re-trigger. Add a `POST /resume/{id}/reparse` endpoint as a short-term workaround. Migration to Celery or RQ should be considered when retry reliability becomes a requirement.
- **Depends on:** AI-003, BE-009
- **Estimate:** 1 day
- **Status:** Done
- **Acceptance Criteria:**
  - Upload returns 200 before parsing begins
  - parse_status reflects the correct state at each transition
  - A failed parse never leaves the resume stuck in processing state

### Workstream E: Interview Context and Session Model

#### `DB-005` Create interview session table
- Link to user, resume, and job description
- Store session status, interview type, and start and end timestamps
- Interview mode is voice only in v1 — no text or hybrid mode
- **Depends on:** DB-001, DB-002
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Table exists after migration
  - Session is linked to a resume, a JD, and an interview type
  - Mode field defaults to voice and is the only supported value in v1

#### `DB-006` Create interview turn table
- Link to session with sequence order
- Store speaker type (ai or candidate), message content, and timestamp
- **Depends on:** DB-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Turns can be inserted and retrieved in sequence order
  - Speaker type is enforced via an enum
- **Note:** Turns are written to this table once per completed utterance — not per STT chunk. In-flight chunks are buffered in Redis before assembly. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — tickets `RT-REDIS-002`, `RT-REDIS-003`.

#### `DB-007` Create report table
- Link to session
- Store structured summary fields and final report payload as JSONB
- **Depends on:** DB-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Report can be created and retrieved by session id
  - JSONB field stores the full structured report without truncation

#### `AI-006` Build prompt template system
- Create one prompt template file per interview type: `behavioral.txt`, `technical.txt`, `resume_based.txt`
- Templates use placeholder variables injected at session start: `{{candidate_name}}`, `{{role}}`, `{{company_name}}`, `{{resume_summary}}`, `{{key_skills}}`, `{{years_of_experience}}`, `{{jd_highlights}}`
- Build a `PromptRenderer` service that accepts interview_type + context values and returns the rendered system prompt string
- The rendered prompt is stored in `interview_sessions.interview_context_json` — not re-rendered per turn
- **Depends on:** AI-001
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Three template files exist covering all supported interview types
  - `PromptRenderer.render(interview_type, context)` returns a fully substituted prompt string
  - Missing placeholder values raise a clear error at render time, not silently produce broken prompts
  - Rendered prompt is stored on the session row at creation time
- **Note:** See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 5 for full variable list and storage contract.

#### `AI-007` Build interview context assembler
- Assemble the dynamic context object from DB records: parsed resume, JD, user profile
- Pass the context to `PromptRenderer` to produce the final system prompt
- This is the boundary between the data layer and the LLM layer — nothing downstream should query the DB for context
- **Depends on:** AI-006, DB-003, DB-002
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Given a `resume_id`, `jd_id`, and `interview_type`, produces a fully rendered system prompt
  - Fails fast with a clear error if the resume has not been parsed yet
- **Note:** Replaces the prior plan-generation approach. No structured plan is generated upfront — the LLM drives the interview dynamically from the system prompt. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 5.

#### `AI-008` Build interview session orchestrator
- On session start: call LLM with rendered system prompt → get opening question
- On each candidate answer: call LLM with system prompt + last N turns from Redis → get next question or completion signal
- Parse LLM output to detect completion signal vs next question
- Keep the orchestrator decoupled from transport (works with both WebSocket voice and REST)
- **Depends on:** AI-007, DB-005, DB-006, RT-REDIS-003
- **Estimate:** 2 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Orchestrator produces a valid opening question from the rendered system prompt
  - Follow-up questions are contextually relevant to the previous answer
  - Completion signal from LLM is correctly parsed and triggers session close
  - LLM context is read from Redis (`get_recent_turns`) — no Postgres query per turn
- **Note:** Full turn cycle documented in [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 4, Phase 2.

#### `AI-009` Add completion guardrails
- Enforce max turn count as a hard stop regardless of LLM completion signal
- If max turns reached without LLM signalling completion, close the session and generate the report with what exists
- Add a placeholder for time-based completion in a future phase
- **Depends on:** AI-008
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Interview stops at the configured max question count even if LLM does not signal completion
  - Session status is updated to completed and report generation is triggered in both paths

### Workstream F: Reporting

#### `AI-010` Define report schema
- Define the structured report output including summary, strengths, weaknesses, improvement areas, and category score placeholders
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Pydantic schema exists for the report
  - Schema includes at least summary, strengths, weaknesses, and improvement areas

#### `AI-011` Build report generation service
- Consume the full interview transcript
- Call OpenAI to generate a structured report conforming to the report schema
- Persist the report to the report table
- **Depends on:** AI-010, DB-007
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - A completed interview session produces a persisted report
  - Report includes all required fields from the schema
  - Generation failure does not leave the session in an inconsistent state

#### `BE-013` Add interview start endpoint
- `POST /api/v1/interview/start` accepts resume_id, interview_type, jd (raw text), company_name, and role
- Creates a JD record, assembles context, renders system prompt, creates session row, calls LLM for opening question, runs TTS, returns result — all in one request
- Voice is the only supported mode — no mode parameter required from the client
- **Depends on:** AI-008, DB-005
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns session_id, question_text, and audio_url for the opening question
  - Session row is created with status=in_progress, mode=voice, and rendered system prompt stored in interview_context_json
  - Opening AI turn is persisted in interview_turns before the response is returned
  - Returns 422 if any required field is missing
  - Returns 404 if the resume does not belong to the current user
  - Returns 409 if the resume parse_status is not completed
- **Note:** Full bootstrap sequence documented in [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 4, Phase 1.

#### `BE-014` Add interview answer endpoint
- `POST /api/v1/interview/{session_id}/answer` accepts the candidate's answer transcript or audio reference
- Saves the turn and returns the next question or a completion signal
- **Depends on:** AI-008, DB-006
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Answer is persisted as a turn in the correct sequence
  - Returns the next AI question or a completion flag
  - Returns 404 for unknown or unauthorized session id

#### `BE-015` Add interview sessions list and detail endpoints
- `GET /api/v1/interview` returns all sessions for the current user — used to populate the home screen sessions list inline
- `GET /api/v1/interview/{session_id}` returns the full session detail: JD content, company name, role, interview type, transcript turns in sequence, and session metadata
- **Depends on:** DB-005, DB-006
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - List endpoint returns all sessions ordered by created_at desc
  - Detail endpoint returns transcript turns in sequence order
  - Both endpoints return 404 for unknown or unauthorized ids
  - Detail response includes company_name, role, and jd raw text from the linked JD record

#### `BE-016` Add final report endpoint
- `GET /api/v1/interview/{session_id}/report` returns the generated report for a completed session
- **Depends on:** AI-011, DB-007
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns report for completed sessions
  - Returns 404 if no report exists yet

### Exit Criteria
- User can authenticate
- User can upload a resume and see all uploaded resumes inline on the home screen
- Resume is parsed into a normalized structure asynchronously
- User can see past interview sessions inline on the home screen and click into session details
- User can pick a resume, select an interview type, paste a JD with company name and role, and start a voice interview immediately
- Voice is the only supported interview mode
- User can complete a voice interview end to end
- User can retrieve a final report

## 6. Phase 2: Structured Evaluation Layer

### Goal
Make interview output measurable and comparable across sessions.

### Workstream A: Evaluation Data Model

#### `DB-008` Create skill taxonomy table
- Store skill name, skill group, and display metadata
- Seeded with a base set of common engineering and behavioral skills
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Table exists with a base seed of skills
  - Skills are grouped into meaningful categories

#### `DB-009` Create question evaluation table
- Link to session and turn or question reference
- Store skill, score, rationale text, and improvement note
- **Depends on:** DB-006, DB-008
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - One evaluation row per question per session
  - Score field has a defined range enforced at the application level

#### `DB-010` Create interview aggregate score table
- Link to session
- Store score category and score value
- One row per category per session
- **Depends on:** DB-009
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Aggregate scores can be read back and compared across sessions

### Workstream B: Rubric and Scoring Engine

#### `AI-012` Define scoring rubric config
- Define rubric dimensions: technical depth, relevance, communication, confidence, completeness
- Each dimension should have a scoring range and description
- **Depends on:** None
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Rubric config exists as a structured object or config file
  - Each dimension has a defined scoring scale

#### `AI-013` Map interview questions to skills
- Tag each generated question with a target skill and category from the taxonomy
- Store the mapping as part of the interview turn or question record
- **Depends on:** AI-012, DB-008
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Every question has at least one skill tag
  - Skill tags reference the taxonomy table

#### `AI-014` Build answer evaluator
- Score each candidate answer against the rubric dimensions
- Return a rationale string and an improvement note per answer
- **Depends on:** AI-012, AI-013
- **Estimate:** 2 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Every answer produces a score, rationale, and improvement note
  - Scores fall within the defined rubric range

#### `AI-015` Build report aggregation logic
- Convert question-level evaluations into final category scores
- Aggregate into the interview aggregate score table
- **Depends on:** AI-014, DB-010
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Final report includes aggregated scores for each rubric category
  - Scores are reproducible given the same question-level evaluations

#### `BE-017` Add evaluation retrieval endpoint
- `GET /api/v1/interview/{session_id}/evaluation` returns full structured evaluation for a session
- **Depends on:** AI-015
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns per-question scores and aggregate category scores
  - Returns 404 for unknown or unauthorized session id

### Exit Criteria
- Each interview produces question-level scores with rationale
- Final reports include structured scoring categories
- Data model supports future trend analysis across sessions

## 7. Phase 3: Realtime Product Experience

### Goal
Harden the live session experience for voice interviews using streaming events and stable session state.

### Workstream A: Realtime Infrastructure

#### `RT-001` Add WebSocket connection manager
- Track active interview sessions by session id
- Authenticate WebSocket connections using the existing JWT auth
- Route session events to the correct connection
- **Depends on:** BE-007
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Authenticated WebSocket connections are established and tracked
  - Unauthenticated connection attempts are rejected
  - Connections are cleaned up on disconnect

#### `RT-002` Define realtime event contract
- Define payload shapes for: session started, AI message created, user message received, transcript updated, session completed, error event
- **Depends on:** RT-001
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Event payloads are documented and consistent
  - All events include a type field and a session id

#### `RT-003` Implement interview event publisher
- Broadcast session events to the correct WebSocket connection during an active interview
- **Depends on:** RT-002, AI-008
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Frontend receives AI question events in real time without polling
  - Events are delivered to the correct session connection only

### Workstream B: Resilience

#### `DB-011` Create session event table
- Persist event payloads for potential replay or audit
- **Depends on:** DB-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Events are persisted with session id, event type, payload, and timestamp

#### `RT-004` Add autosave support
- Save partial session state after each turn so progress is not lost mid-interview
- **Depends on:** DB-006, RT-003, RT-REDIS-003
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Each completed turn is persisted before the next question is sent
  - No turns are lost if the server restarts between turns
- **Note:** Turn persistence is synchronous — Postgres INSERT happens immediately after utterance assembly, not deferred. Redis holds the context cache only. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 4.

#### `RT-005` Add reconnect support
- Allow a client to rejoin an active session after a disconnect
- Recover the current transcript and the last known session state on reconnect
- **Depends on:** RT-004
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Client can reconnect to an active session and receive the current state
  - No duplicate turns are created on reconnect

#### `BE-018` Add session restore endpoint
- `GET /api/v1/interview/{session_id}/state` returns a snapshot of the current session including transcript and status
- **Depends on:** RT-004
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns current transcript, session status, and last question for active sessions

### Exit Criteria
- Frontend can consume a live interview stream over WebSocket
- Session survives browser refresh and reconnect
- Partial transcript and turn data are not lost

## 8. Phase 4: Voice Layer

### Goal
Improve voice input and spoken AI output reliability on top of the MVP foundation.

### Workstream A: Speech Input

#### `VO-001` Define audio upload and stream strategy
- Decide whether audio is uploaded as complete blobs or streamed in chunks
- Define accepted formats, max duration, and max file size rules
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Strategy is documented and agreed on before implementation begins

#### `VO-002` Build speech ingestion interface
- Accept audio chunks or recorded blobs associated with an interview session and turn
- **Depends on:** VO-001, DB-006, RT-REDIS-001
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Audio can be submitted and linked to the correct session and turn
- **Note:** Partial STT results from this interface are buffered in Redis (`interview:chunks:{session_id}`) — not written to Postgres. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 4, Step 1.

#### `VO-003` Integrate STT provider
- Convert speech input to transcript text
- Return partial and final transcript states where the provider supports it
- **Depends on:** VO-002, RT-REDIS-002
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Spoken input produces a text transcript associated with the correct turn
  - Partial transcripts are surfaced to the frontend as available
- **Note:** Partial STT results go to Redis chunk buffer. Only the final assembled text triggers a Postgres INSERT into `interview_turns`. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 4, Steps 1–2.

#### `DB-012` Create transcript chunk table
- Store transcript chunks linked to session and turn with timestamp boundaries and provider metadata
- **Depends on:** DB-006
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Chunks are stored with enough metadata to reconstruct the full transcript in order
- **Note:** In MVP, in-flight STT chunks live in Redis only (`interview:chunks:{session_id}`) and are never persisted to this table during the live session. This table is for post-session audit / communication signal analysis (Phase 6). If chunk persistence during voice sessions becomes a requirement before Phase 6, revisit after `RT-REDIS-002` is stable. See [`voice-transcript-redis-plan.md`](./voice-transcript-redis-plan.md) — Section 9.

#### `VO-004` Add STT retry and fallback handling
- Handle transient STT provider failures with retry logic
- Mark failed chunks so the session can continue rather than crash
- **Depends on:** VO-003
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Transient failures are retried at least once before marking as failed
  - A failed chunk does not terminate the session

### Workstream B: Spoken AI Output

#### `VO-005` Integrate TTS provider
- Convert AI response text into audio
- Return audio to the frontend linked to the current turn
- **Depends on:** AI-008
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Every AI question produces an audio response
  - Audio is returned before the next input is accepted

#### `DB-013` Create audio asset table
- Store audio asset location, duration, and provider metadata linked to session and turn
- **Depends on:** DB-006
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Audio assets are stored and retrievable by turn

#### `VO-006` Add audio response delivery contract
- Define how the frontend receives AI audio with transcript linkage
- Audio and transcript for each turn must stay synchronized
- **Depends on:** VO-005, DB-013
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Frontend receives audio and transcript together for each AI turn
  - Mismatched audio and transcript states do not occur

### Workstream C: Turn Orchestration

#### `VO-007` Build voice turn state manager
- Manage transitions between listening, thinking, speaking, and idle states
- Expose current state to the frontend via WebSocket events
- **Depends on:** RT-003, VO-003, VO-005
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - State transitions are deterministic and logged
  - Frontend receives state change events in the correct order

#### `VO-008` Add interruption and silence handling
- Detect extended silence and reprompt the candidate
- Handle premature audio cutoffs gracefully without crashing the session
- **Depends on:** VO-007
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Silence beyond a configured threshold triggers a reprompt
  - Cutoffs are handled without leaving the session in a broken state

### Exit Criteria
- Candidate can answer by voice and receive a spoken AI response
- Transcript and audio remain linked to the correct turns
- Voice turn state is stable and visible to the frontend

## 9. Phase 5: Interview History and Performance Tracking

### Goal
Support repeat usage with meaningful progress visibility so users have a reason to return.

### Workstream A: History

#### `BE-019` Add interview history list endpoint
- `GET /api/v1/interviews` returns a paginated list of the user's past sessions with a basic report summary per session
- **Depends on:** DB-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns paginated sessions in reverse chronological order
  - Each item includes session id, date, status, and a one-line summary if a report exists

#### `BE-020` Add transcript history endpoint
- `GET /api/v1/interview/{session_id}/transcript` returns the full stored transcript for a completed interview
- **Depends on:** DB-006
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns turns in sequence order with speaker type and content

#### `BE-021` Add report history endpoint
- `GET /api/v1/interviews/reports` returns a list of historical report summaries across all sessions
- **Depends on:** DB-007
- **Estimate:** 0.25 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns reports for all completed sessions for the current user

### Workstream B: Analytics Aggregation

#### `AN-001` Define analytics aggregation models
- Define the data shapes for category trend, skill trend, and role readiness score
- **Depends on:** DB-010
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Aggregation models are defined as Pydantic schemas

#### `AN-002` Build score trend aggregation
- Aggregate category scores by date across all completed sessions for a user
- **Depends on:** AN-001
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns a time-series of scores per category

#### `AN-003` Build skill progression aggregation
- Aggregate repeated skill performance across sessions to show improvement or decline
- **Depends on:** AN-001
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns per-skill trend data across multiple sessions

#### `AN-004` Define role-readiness metric
- Combine weighted signals from rubric scores into a single readable readiness percentage
- **Depends on:** AN-002, AN-003
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Readiness metric is computed and explainable — not a black box number

#### `BE-022` Add analytics dashboard endpoints
- `GET /api/v1/analytics/score-trend` returns score trend data
- `GET /api/v1/analytics/skill-trend` returns skill progression data
- `GET /api/v1/analytics/readiness` returns the role readiness metric
- **Depends on:** AN-002, AN-003, AN-004
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - All three endpoints return correct aggregated data for the current user

### Exit Criteria
- Users can browse past interviews and reports
- Users can view score and skill trends over time

## 10. Phase 6: Advanced Coaching Intelligence

### Goal
Provide specific, actionable coaching recommendations rather than only scoring.

### Workstream A: Personalized Recommendations

#### `AN-005` Build weakness clustering logic
- Group repeated weak performance areas across sessions to identify patterns
- **Depends on:** AN-003
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns a ranked list of weak areas with recurrence count

#### `AI-016` Build recommendation generator
- Convert identified weakness clusters into specific next-step suggestions
- Suggestions should be role-relevant and tied to actual performance data
- **Depends on:** AN-005
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns at least 3 actionable recommendations per user
  - Recommendations reference specific skill gaps

#### `AI-017` Build targeted practice topic generator
- Suggest specific practice drills by role and weak skill area
- **Depends on:** AI-016
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns suggested practice topics that are specific enough to act on

#### `BE-023` Add coaching insights endpoint
- `GET /api/v1/coaching/insights` returns recommendations and targeted practice suggestions
- **Depends on:** AI-016, AI-017
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns recommendations and practice topics for the current user

### Workstream B: Communication Signals

#### `AN-006` Define communication signal schema
- Define schema for pace, hesitation, filler density, and answer completeness
- Signals should be presented as coaching aids, not hard judgements
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Schema is defined and documented with a clear explanation of what each signal means

#### `AN-007` Build transcript-based signal extraction
- Compute communication metrics from the stored transcript text
- **Depends on:** AN-006, DB-012
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Filler word density and answer completeness can be computed from a stored transcript

#### `AN-008` Build signal summary generator
- Summarize extracted signals into a coaching-friendly format
- **Depends on:** AN-007
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Output reads as coaching feedback, not raw metric output

### Exit Criteria
- Users receive specific next-step coaching recommendations
- Users can view communication-oriented performance signals as coaching aids

## 11. Phase 7: Human Interviewer Readiness

### Goal
Prepare the architecture for AI and human interview support without a rewrite.

### Workstream A: Session Model Generalization

#### `DB-014` Add participant table
- Store session, participant role (candidate, ai_interviewer, human_interviewer), and user or external identity reference
- **Depends on:** DB-005
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Participant rows can be created for both AI and human roles
  - Existing sessions are migrated without data loss

#### `DB-015` Generalize transcript ownership
- Update the interview turn table to track which participant produced each turn
- **Depends on:** DB-014
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Every turn references a participant record
  - Existing transcript data is migrated correctly

#### `BE-024` Refactor session APIs for participant-aware flows
- Update session endpoints to return participant metadata alongside transcript data
- **Depends on:** DB-014, DB-015
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Session detail endpoint returns participant list and turn ownership
  - Existing clients are not broken by the change

### Workstream B: Human Review Support

#### `DB-016` Create reviewer note table
- Store reviewer id, session id, note text, and timestamp
- **Depends on:** DB-014
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Notes can be created and listed for a session

#### `BE-025` Add reviewer note endpoints
- `POST /api/v1/interview/{session_id}/notes` creates a reviewer note
- `GET /api/v1/interview/{session_id}/notes` lists all notes for a session
- **Depends on:** DB-016
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Notes are scoped to the session and only visible to authorized reviewers

#### `BE-026` Add replay metadata endpoint
- `GET /api/v1/interview/{session_id}/replay` returns an ordered session timeline including turns, audio references, and reviewer notes
- **Depends on:** DB-015, DB-016
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns a chronologically ordered timeline usable for replay

### Exit Criteria
- Session model supports both AI-led and human-led participation
- Reviewers can annotate sessions
- Replay timeline is available for completed sessions

## 12. Phase 8: Productization and External Integrations

### Goal
Expose the system as an integration-ready product for third parties.

### Workstream A: API Product Foundation

#### `DB-017` Create organization table
- Store organization identity and plan metadata placeholder
- **Depends on:** None
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Table exists and can be linked to users

#### `DB-018` Create API key table
- Link to organization, store key hash, status, and permissions
- Never store the raw key — only the hash
- **Depends on:** DB-017
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Keys can be created, revoked, and validated by hash lookup

#### `PLT-005` Add tenant-aware access model
- Scope all data access by organization so one tenant cannot access another's data
- **Depends on:** DB-017
- **Estimate:** 1.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - All data queries are filtered by org id when the caller is an org-scoped API key

#### `BE-027` Add API key auth middleware
- Authenticate external clients using hashed API key lookup
- Return 401 for missing or invalid keys
- **Depends on:** DB-018
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Valid API key grants access to scoped endpoints
  - Invalid or revoked keys return 401

#### `BE-028` Add public create interview API
- `POST /api/v1/public/interview` allows external clients to create an interview session for a candidate
- **Depends on:** BE-027, AI-008
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - External client can create a session and receive a session id
  - Session is scoped to the caller's organization

#### `BE-029` Add public get report API
- `GET /api/v1/public/interview/{session_id}/report` allows external clients to fetch a completed report
- **Depends on:** BE-027, AI-011
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Returns report for sessions owned by the caller's organization
  - Returns 404 for sessions not owned by the caller

### Workstream B: Webhooks and Usage Controls

#### `DB-019` Create webhook subscription table
- Store organization, event type, destination URL, and signing secret
- **Depends on:** DB-017
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Subscriptions can be created per event type per organization

#### `PLT-006` Build webhook dispatcher
- Deliver signed webhook payloads to subscriber destination URLs
- Retry failed deliveries with exponential backoff
- **Depends on:** DB-019
- **Estimate:** 2 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Events are delivered with a signature header the receiver can verify
  - Failed deliveries are retried and marked after max retries

#### `PLT-007` Add usage logging
- Track request counts and usage by organization for billing and rate limit enforcement
- **Depends on:** PLT-005
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Every API key request is logged with timestamp, endpoint, and org id

#### `PLT-008` Add rate limiting
- Apply per-key or per-organization rate limits to public API endpoints
- **Depends on:** PLT-007
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Requests exceeding the limit return 429 with a Retry-After header

### Exit Criteria
- External systems can authenticate using API keys
- External systems can create interview sessions and retrieve reports
- Webhook notifications and basic usage controls are in place

## 13. Cross-Cutting Engineering Tasks

### Testing

#### `PLT-009` Add test structure
- Define unit test layout for services and utilities
- Define integration test layout for endpoints using a real test database
- Add API test setup with a test client and auth helpers
- **Depends on:** BE-004
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - At least one unit test and one integration test exist and pass in CI

#### `PLT-010` Add seed and fixture strategy
- Define dev fixtures for local development with realistic data
- Define test fixtures for repeatable integration tests
- **Depends on:** PLT-009
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Running a seed script populates a local dev database with usable data
  - Test fixtures are isolated and do not leak between tests

#### `PLT-011` Add CI checks
- Run linting on every pull request
- Run type or static checks if used
- Run the full test suite on every pull request
- **Depends on:** PLT-009
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - CI fails on lint errors or test failures
  - CI passes on a clean branch before merge

### Observability

#### `PLT-012` Add metrics and tracing placeholders
- Add request metrics (latency, status codes)
- Add job metrics for background parse tasks
- Add interview event metrics (sessions started, completed, failed)
- **Depends on:** BE-003
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - Key metrics are emitted and visible in a local metrics sink

#### `PLT-013` Add audit logging for critical flows
- Log uploads, session creation, report generation, and external API usage with user or org id and timestamp
- **Depends on:** BE-003
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Audit log entries are written for each critical action
  - Entries include enough context to reconstruct who did what and when

### Security

#### `PLT-014` Add file validation and sanitization
- Validate content type header matches the actual file content, not just the extension
- Enforce max file size at the upload endpoint
- **Depends on:** BE-009
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Files with mismatched content types are rejected
  - Files exceeding the size limit return 413

#### `PLT-015` Add authorization policy checks
- Enforce user ownership on all resume, session, and report endpoints
- Enforce org ownership on all public API endpoints
- **Depends on:** BE-007, PLT-005
- **Estimate:** 1 day
- **Status:** To Do
- **Acceptance Criteria:**
  - A user cannot read or modify another user's data
  - An org API key cannot access another org's sessions or reports

#### `PLT-016` Add secret management policy
- Define how API keys, storage credentials, and model provider keys are stored and rotated
- No secrets should be hardcoded or committed to the repository
- **Depends on:** BE-002
- **Estimate:** 0.5 days
- **Status:** To Do
- **Acceptance Criteria:**
  - Secret management policy is documented
  - No secrets exist in the codebase or git history

## 14. Suggested Execution Order

### Sprint Order for Early Build
1. `PLT-001` to `PLT-004`
2. `BE-001` to `BE-005`
3. `BE-006` to `BE-012`
4. `AI-001` to `AI-005`
5. `DB-005` to `DB-007`
6. `AI-006` to `AI-011`
7. `RT-001` to `RT-005`
8. `VO-001` to `VO-008`
9. `BE-013` to `BE-016`
10. `DB-008` to `DB-010`
11. `AI-012` to `AI-015`
12. `BE-017`

### After MVP Stabilizes
1. `BE-018`
2. `BE-019` to `BE-022`
3. `AN-005` to `AN-008`
4. `BE-023`

### Productization Later
1. `DB-014` to `BE-026`
2. `DB-017` to `PLT-008`

## 15. Recommended Ticket Grouping for a Solo Builder

If you are building this mostly alone, group tickets into these execution buckets:

### Bucket 1: App Skeleton
- `PLT-001` to `PLT-004`
- `BE-001` to `BE-005`

### Bucket 2: Auth and Uploads
- `BE-006` to `BE-012`
- `DB-001` to `DB-004`

### Bucket 3: Parsing and Interview Engine
- `AI-001` to `AI-009`
- `DB-005` to `DB-007`

### Bucket 4: Voice and Realtime MVP
- `RT-001` to `RT-005`
- `VO-001` to `VO-008`
- `BE-013` to `BE-016`

### Bucket 5: Structured Scoring
- `DB-008` to `DB-010`
- `AI-012` to `AI-015`
- `BE-017`

### Bucket 6: Analytics and Coaching
- `BE-018` to `BE-023`
- `AN-001` to `AN-008`
- `AI-016` to `AI-017`

### Bucket 7: Human and Platform Readiness
- `DB-014` to `BE-029`
- `PLT-005` to `PLT-016`

## 16. Immediate Next Tickets to Create

If you want to start implementation now, create these first 12 tickets:

1. `PLT-001` Create project conventions
2. `BE-001` Initialize FastAPI application
3. `BE-002` Set up project settings
4. `BE-004` Add database connection layer
5. `BE-005` Add Redis integration
6. `BE-006` Create user model
7. `BE-007` Implement auth flows
8. `DB-001` Create resume and file tables
9. `DB-002` Create JD table
10. `BE-009` Add resume upload endpoint
11. `BE-010` Add JD create endpoint
12. `AI-001` Define parsed resume schema

## 17. Definition of Engineering Completion by Stage

### MVP Complete
- Voice interview works end to end
- Resume is parsed asynchronously into a normalized structure
- JD is stored as text and parsed synchronously
- Final report is generated and persisted
- User can poll parse status via the resume status endpoint

### Evaluation Complete
- Structured scoring exists per question and per session
- Reports are comparable across sessions

### Realtime Complete
- Interview state streams live over WebSocket
- Session recovery works after reconnect

### Voice Complete
- Audio in and audio out work reliably
- Transcript and audio stay synchronized to the correct turns

### Analytics Complete
- Users can track performance trends across interviews
- Role readiness metric is computed and visible

### Platform Complete
- Third parties can authenticate, create interviews, and fetch reports
- Webhook notifications and rate limiting are in place
