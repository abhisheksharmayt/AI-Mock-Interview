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
- Define repo conventions
- Define environment variable strategy
- Define local development setup
- Define branching and migration workflow

#### `PLT-002` Create architecture notes
- Document modular monolith boundaries
- Define service/module responsibilities
- Define where interview engine logic lives

#### `PLT-003` Define event and schema naming rules
- Standardize API response shape
- Standardize WebSocket event naming
- Standardize database naming rules

#### `PLT-004` Create backlog labels and milestone mapping
- Define phase labels
- Define workstream labels
- Define priority labels

### Exit Criteria
- Engineering setup conventions exist
- Scope boundaries are documented
- Team can begin implementation with stable names and module boundaries

## 5. Phase 1: Core MVP

### Goal
Ship a complete voice-first personalized interview flow.

### Workstream A: Backend Bootstrap

#### `BE-001` Initialize FastAPI application
- Create FastAPI app entrypoint
- Add config loading
- Add health endpoint
- Add base router structure

#### `BE-002` Set up project settings
- Add environment-specific settings
- Add secrets loading strategy
- Add app configuration object

#### `BE-003` Add logging and error handling
- Add structured request logging
- Add global exception handler
- Add standard API error response format

#### `BE-004` Add database connection layer
- Configure Postgres connection
- Add session management
- Add migration setup

#### `BE-005` Add Redis integration
- Configure Redis client
- Add reusable cache and queue config

### Workstream B: Auth and User Core

#### `BE-006` Create user model
- Add user table
- Add basic profile fields
- Add created and updated timestamps

#### `BE-007` Implement auth flows
- Signup endpoint
- Login endpoint
- Token generation and validation
- Auth dependency for protected routes

#### `BE-008` Add current user endpoint
- Return authenticated user profile

### Workstream C: Resume and JD Intake

#### `DB-001` Create resume table
- Link to user
- Store file path or object key
- Store parse status

#### `DB-002` Create JD table
- Link to user
- Store original text or file path
- Store parse status

#### `BE-009` Add resume upload endpoint
- Validate file type
- Upload to storage
- Save metadata

#### `BE-010` Add JD create endpoint
- Support pasted text
- Support optional file upload path later
- Save metadata

#### `BE-011` Add storage abstraction
- Local storage for development
- S3-compatible interface for future production use

### Workstream D: Parsing Pipeline

#### `AI-001` Define parsed resume schema
- Skills
- Experience entries
- Projects
- Education
- Seniority clues

#### `AI-002` Define parsed JD schema
- Role title
- Required skills
- Preferred skills
- Responsibilities
- Seniority expectation

#### `AI-003` Implement resume parsing service
- Extract text
- Normalize sections
- Generate structured resume output

#### `AI-004` Implement JD parsing service
- Normalize JD text
- Extract role requirements
- Generate structured JD output

#### `DB-003` Create parsed resume table or JSON storage
- Store normalized parser output

#### `DB-004` Create parsed JD table or JSON storage
- Store normalized parser output

#### `AI-005` Add parser job orchestration
- Trigger parse after upload
- Track parse states
- Retry failed parses

### Workstream E: Interview Context and Session Model

#### `DB-005` Create interview session table
- User association
- Resume association
- JD association
- Status fields
- Start and end timestamps
- Default mode set to voice

#### `DB-006` Create interview turn table
- Session association
- Speaker type
- Message content
- Sequence order
- Timestamp

#### `DB-007` Create report table
- Session association
- Structured summary fields
- Final report payload

#### `AI-006` Define interview context schema
- Resume summary
- JD summary
- Target skills
- Focus areas
- Interview type

#### `AI-007` Build interview plan generator
- Generate sections
- Generate topic ordering
- Set estimated question counts

#### `AI-008` Build interview session orchestrator
- Start interview
- Generate opening question
- Accept candidate answer
- Generate follow-up question
- Check completion conditions

#### `AI-009` Add completion rules
- Max questions
- Section completion
- Time-based future compatibility

### Workstream F: Reporting

#### `AI-010` Define report schema
- Summary
- Strengths
- Weaknesses
- Improvement areas
- Category scores placeholder

#### `AI-011` Build report generation service
- Consume transcript
- Generate final structured report

#### `BE-012` Add interview start endpoint
- Create session
- Return first question and voice session configuration

#### `BE-013` Add interview answer endpoint
- Save user answer transcript or audio reference
- Return next question

#### `BE-014` Add interview session detail endpoint
- Return transcript, audio metadata, and session metadata

#### `BE-015` Add final report endpoint
- Return generated report

### Exit Criteria
- User can authenticate
- User can upload resume and JD
- Resume and JD are parsed into normalized structures
- User can complete a voice interview
- User can retrieve a final report

**Execution Note**
- Because the product is voice-first, pull the minimum required realtime and voice tasks from Phases 3 and 4 into MVP execution.

## 6. Phase 2: Structured Evaluation Layer

### Goal
Make interview output measurable and comparable.

### Workstream A: Evaluation Data Model

#### `DB-008` Create skill taxonomy table
- Skill name
- Skill group
- Display metadata

#### `DB-009` Create question evaluation table
- Session
- Turn or question reference
- Skill
- Score
- Rationale
- Improvement note

#### `DB-010` Create interview aggregate score table
- Session
- Score category
- Score value

### Workstream B: Rubric and Scoring Engine

#### `AI-012` Define scoring rubric config
- Technical depth
- Relevance
- Communication
- Confidence
- Completeness

#### `AI-013` Map interview questions to skills
- Tag each question with target skill and category

#### `AI-014` Build answer evaluator
- Score each answer against rubric
- Return rationale and improvement note

#### `AI-015` Build report aggregation logic
- Convert question-level evaluations into final category scores

#### `BE-016` Add evaluation retrieval endpoint
- Return full structured evaluation for a session

### Exit Criteria
- Each interview produces question-level scores
- Final reports include structured scoring categories
- Data model supports future trends

## 7. Phase 3: Realtime Product Experience

### Goal
Harden the live session experience for voice interviews.

### Workstream A: Realtime Infrastructure

#### `RT-001` Add WebSocket connection manager
- Track active interview sessions
- Authenticate connections
- Route session events

#### `RT-002` Define realtime event contract
- Session started
- AI message created
- User message received
- Transcript updated
- Session completed
- Error event

#### `RT-003` Implement interview event publisher
- Broadcast session events to frontend

### Workstream B: Resilience

#### `DB-011` Create session event table
- Persist event payloads if needed for replay

#### `RT-004` Add autosave support
- Save partial state after each turn

#### `RT-005` Add reconnect support
- Rejoin session
- Recover active transcript
- Recover last known state

#### `BE-017` Add session restore endpoint
- Return current session state snapshot

### Exit Criteria
- Frontend can consume a live interview stream
- Session survives refresh and reconnect
- Partial work is not lost

## 8. Phase 4: Voice Layer

### Goal
Improve voice input and spoken AI output reliability.

### Workstream A: Speech Input

#### `VO-001` Define audio upload and stream strategy
- Decide chunking strategy
- Define accepted formats
- Define max duration and size rules

#### `VO-002` Build speech ingestion interface
- Accept audio chunks or recorded blobs
- Associate audio with interview session

#### `VO-003` Integrate STT provider
- Convert speech to transcript
- Return partial and final transcript states if supported

#### `DB-012` Create transcript chunk table
- Session
- Turn
- Transcript text
- Timestamp boundaries
- Provider metadata

#### `VO-004` Add STT retry and fallback handling
- Handle transient failures
- Mark failed chunks

### Workstream B: Spoken AI Output

#### `VO-005` Integrate TTS provider
- Convert AI response text into audio

#### `DB-013` Create audio asset table
- Session
- Turn
- Asset location
- Duration
- Provider metadata

#### `VO-006` Add audio response delivery contract
- Frontend receives AI audio with transcript linkage

### Workstream C: Turn Orchestration

#### `VO-007` Build voice turn state manager
- Listening state
- Thinking state
- Speaking state
- Idle state

#### `VO-008` Add interruption and silence handling
- Detect no input
- Detect premature cutoffs
- Resume or reprompt safely

### Exit Criteria
- Candidate can answer by voice
- AI responds with generated speech
- Transcript and audio stay linked to the correct turns

## 9. Phase 5: Interview History and Performance Tracking

### Goal
Support repeat usage with meaningful progress visibility.

### Workstream A: History

#### `BE-018` Add interview history list endpoint
- Paginated session list
- Basic report summary

#### `BE-019` Add transcript history endpoint
- Fetch transcript for completed interview

#### `BE-020` Add report history endpoint
- Fetch historical report snapshots

### Workstream B: Analytics Aggregation

#### `AN-001` Define analytics aggregation models
- Category trend
- Skill trend
- Readiness score

#### `AN-002` Build score trend aggregation
- Aggregate by date and category

#### `AN-003` Build skill progression aggregation
- Aggregate repeated skill performance

#### `AN-004` Define role-readiness metric
- Combine weighted signals into a readable metric

#### `BE-021` Add analytics dashboard endpoints
- Score trend endpoint
- Skill trend endpoint
- Readiness endpoint

### Exit Criteria
- Users can browse past interviews
- Users can view trends over time

## 10. Phase 6: Advanced Coaching Intelligence

### Goal
Provide specific coaching recommendations.

### Workstream A: Personalized Recommendations

#### `AN-005` Build weakness clustering logic
- Group repeated weak performance areas

#### `AI-016` Build recommendation generator
- Convert weakness clusters into next-step suggestions

#### `AI-017` Build targeted practice topic generator
- Suggest drills by role and weak skill area

#### `BE-022` Add coaching insights endpoint
- Return recommendations and targeted practice suggestions

### Workstream B: Communication Signals

#### `AN-006` Define communication signal schema
- Pace
- Hesitation
- Filler density
- Answer completeness

#### `AN-007` Build transcript-based signal extraction
- Compute transcript-derived metrics

#### `AN-008` Build signal summary generator
- Present signals as coaching aids, not hard truth

### Exit Criteria
- Users receive specific next-step coaching
- Users can view communication-oriented performance signals

## 11. Phase 7: Human Interviewer Readiness

### Goal
Prepare the architecture for AI and human interview support.

### Workstream A: Session Model Generalization

#### `DB-014` Add participant table
- Session
- Role
- User or external identity reference

#### `DB-015` Generalize transcript ownership
- Track which participant produced each turn

#### `BE-023` Refactor session APIs for participant-aware flows
- Return participant metadata

### Workstream B: Human Review Support

#### `DB-016` Create reviewer note table
- Session
- Reviewer
- Note text
- Timestamp

#### `BE-024` Add reviewer note endpoints
- Create and list notes

#### `BE-025` Add replay metadata endpoint
- Return ordered session timeline

### Exit Criteria
- Session model supports both AI-led and human-led participation
- Reviewers can annotate sessions

## 12. Phase 8: Productization and External Integrations

### Goal
Expose the system as an integration-ready product.

### Workstream A: API Product Foundation

#### `DB-017` Create organization table
- Organization identity
- Plan metadata placeholder

#### `DB-018` Create API key table
- Organization
- Key hash
- Status
- Permissions

#### `PLT-005` Add tenant-aware access model
- Scope data by organization

#### `BE-026` Add API key auth middleware
- Authenticate external clients

#### `BE-027` Add public create interview API
- Create interview session externally

#### `BE-028` Add public get report API
- Fetch report externally

### Workstream B: Webhooks and Usage Controls

#### `DB-019` Create webhook subscription table
- Organization
- Event type
- Destination
- Secret

#### `PLT-006` Build webhook dispatcher
- Deliver signed events
- Retry failed deliveries

#### `PLT-007` Add usage logging
- Track request counts
- Track usage by organization

#### `PLT-008` Add rate limiting
- Apply per key or per organization limits

### Exit Criteria
- External systems can authenticate
- External systems can create interview sessions and retrieve reports
- Webhook notifications and basic usage controls exist

## 13. Cross-Cutting Engineering Tasks

### Testing

#### `PLT-009` Add test structure
- Unit test layout
- Integration test layout
- API test setup

#### `PLT-010` Add seed and fixture strategy
- Dev fixtures
- Test fixtures

#### `PLT-011` Add CI checks
- Lint
- Type or static checks if used
- Tests

### Observability

#### `PLT-012` Add metrics and tracing placeholders
- Request metrics
- Job metrics
- Interview event metrics

#### `PLT-013` Add audit logging for critical flows
- Uploads
- Session creation
- Report generation
- External API usage

### Security

#### `PLT-014` Add file validation and sanitization
- Content type validation
- Size validation

#### `PLT-015` Add authorization policy checks
- User ownership checks
- Org ownership checks

#### `PLT-016` Add secret management policy
- API keys
- storage credentials
- model provider keys

## 14. Suggested Execution Order

### Sprint Order for Early Build
1. `PLT-001` to `PLT-004`
2. `BE-001` to `BE-005`
3. `BE-006` to `BE-011`
4. `AI-001` to `AI-005`
5. `DB-005` to `DB-007`
6. `AI-006` to `AI-011`
7. `RT-001` to `RT-005`
8. `VO-001` to `VO-008`
9. `BE-012` to `BE-015`
10. `DB-008` to `DB-010`
11. `AI-012` to `AI-015`
12. `BE-016`

### After MVP Stabilizes
1. `BE-017`
2. `BE-018` to `BE-021`
3. `AN-005` to `AN-008`
4. `BE-022`

### Productization Later
1. `DB-014` to `BE-025`
2. `DB-017` to `PLT-008`

## 15. Recommended Ticket Grouping for a Solo Builder

If you are building this mostly alone, group tickets into these execution buckets:

### Bucket 1: App Skeleton
- `PLT-001` to `PLT-004`
- `BE-001` to `BE-005`

### Bucket 2: Auth and Uploads
- `BE-006` to `BE-011`
- `DB-001` to `DB-004`

### Bucket 3: Parsing and Interview Engine
- `AI-001` to `AI-009`
- `DB-005` to `DB-007`

### Bucket 4: Voice and Realtime MVP
- `RT-001` to `RT-005`
- `VO-001` to `VO-008`
- `BE-012` to `BE-015`

### Bucket 5: Structured Scoring
- `DB-008` to `DB-010`
- `AI-012` to `AI-015`
- `BE-016`

### Bucket 6: Analytics and Coaching
- `BE-017` to `BE-022`
- `AN-001` to `AN-008`
- `AI-016` to `AI-017`

### Bucket 7: Human and Platform Readiness
- `DB-014` to `BE-028`
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
8. `DB-001` Create resume table
9. `DB-002` Create JD table
10. `BE-009` Add resume upload endpoint
11. `BE-010` Add JD create endpoint
12. `AI-001` Define parsed resume schema

## 17. Definition of Engineering Completion by Stage

### MVP Complete
- Voice interview works end to end
- Resume and JD parsing work
- Final report is generated and persisted

### Evaluation Complete
- Structured scoring exists
- Reports are comparable across sessions

### Realtime Complete
- Interview state streams live
- Session recovery works

### Voice Complete
- Audio in and audio out work reliably
- Transcript and audio stay synchronized

### Analytics Complete
- Users can track performance trends across interviews

### Platform Complete
- Third parties can authenticate, create interviews, and fetch reports
