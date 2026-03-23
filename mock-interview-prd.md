# AI Mock Interview Platform PRD

## 1. Document Overview

**Product Name:** AI Mock Interview Platform

**Document Type:** Product Requirements Document (PRD)

**Primary Goal:** Build a mock interview platform that starts with resume- and JD-based AI interviews and evolves into a realtime voice interview, coaching, analytics, and integration-ready product.

**Intended Use of This Document:** This PRD is written to be execution-friendly. Each phase includes clear outcomes, scope, milestones, and ticket-ready implementation items so development work can be planned incrementally.

## 2. Product Vision

Job seekers should be able to:
- Upload their resume
- Upload or paste a job description
- Take a tailored mock interview
- Receive useful, structured feedback
- Track progress over time
- Eventually practice with voice and later with human interviewers

Organizations and external platforms should eventually be able to:
- Integrate the interview engine through APIs
- Create interview sessions for candidates
- Retrieve reports and evaluation summaries

## 3. Problem Statement

Candidates often prepare using generic question lists, which do not reflect their own resume, the target role, or their performance over time. Existing preparation tools frequently lack:
- personalization based on resume and JD
- structured performance tracking
- realistic interview flow
- actionable feedback
- a path from AI-led interviews to recruiter or human-led workflows

## 4. Product Goals

### Primary Goals
- Deliver personalized mock interviews based on a candidate's resume and target JD
- Generate structured interview reports that are useful for improvement
- Build a system that can grow from text interviews to voice interviews
- Design the data model so performance can be tracked across sessions

### Secondary Goals
- Add realtime transcript and live interview feel
- Add speech input and spoken AI responses
- Add coaching intelligence and performance trends
- Make the platform integration-ready for third parties

## 5. Non-Goals for Initial Versions

- Full recruiter ATS replacement
- Perfect sentiment or emotion detection
- Marketplace for interviewers
- Multi-language support at launch
- Enterprise-grade multi-tenant billing in v1
- Heavy microservice decomposition from day one

## 6. Primary Users

### User Type 1: Candidate
- Wants role-specific mock interviews
- Wants resume-aware and JD-aware questions
- Wants feedback and progress tracking

### User Type 2: Admin or Platform Owner
- Wants to monitor interview usage
- Wants to review system quality and reports
- Will later need controls for templates, rubrics, and integrations

### User Type 3: External Integrator (Future)
- Wants to create interviews programmatically
- Wants to retrieve evaluation output
- Wants embeddable interview infrastructure

## 7. Key Product Principles

- Start with a narrow but complete workflow
- Build business logic once and reuse it across text and voice
- Store structured evaluation data early
- Treat realtime voice as an experience layer, not the core business logic
- Keep architecture modular but avoid premature service splitting

## 8. User Journey

### Candidate Journey
1. User signs up or logs in
2. User uploads resume
3. User uploads or pastes JD
4. System parses both documents
5. System creates a personalized interview plan
6. User starts an interview
7. AI asks questions and follow-up questions
8. User answers
9. System stores transcript and evaluation data
10. User sees a final report
11. User returns later to view progress across interviews

## 9. Functional Scope by Phase

---

## Phase 0: Product Definition

### Objective
Define a narrow v1 that is useful and implementable.

### In Scope
- target user selection
- interview type definition
- v1 scope freeze
- success metrics definition

### Out of Scope
- engineering implementation
- advanced analytics
- integrations

### Phase Achievement
- Product direction is frozen for MVP
- Team knows exactly what v1 includes and excludes

### Milestones

#### Milestone 0.1: Define Target User and Interview Type
**Achievement**
- One primary user segment is selected
- One initial interview format is selected

**Acceptance Criteria**
- Primary user persona is written down
- First interview format is clearly defined

**Ticket Candidates**
- Write target user persona doc
- Define interview categories for MVP
- Choose the first supported interview type

#### Milestone 0.2: Define MVP Metrics and Scope
**Achievement**
- MVP scope is documented and locked
- Success metrics are decided

**Acceptance Criteria**
- MVP in-scope list exists
- MVP non-goals list exists
- Metrics list exists

**Ticket Candidates**
- Define MVP scope doc
- Define non-goals doc
- Define product success metrics

---

## Phase 1: Core MVP

### Objective
Ship a complete text-based interview experience based on resume and JD.

### In Scope
- auth
- resume upload
- JD upload
- parsing pipeline
- interview generation
- text-based interview UI
- transcript persistence
- final report generation

### Out of Scope
- voice
- realtime graphing
- external APIs
- advanced analytics trends

### Phase Achievement
- A candidate can complete an end-to-end personalized mock interview and receive a report

### Milestones

#### Milestone 1.1: User and File Intake
**Achievement**
- Users can sign up, log in, and submit resume and JD inputs

**Acceptance Criteria**
- User can create an account and authenticate
- User can upload a resume file
- User can upload or paste a JD
- Uploaded files and metadata are stored successfully

**Ticket Candidates**
- Implement auth endpoints
- Implement user model
- Add resume upload API
- Add JD upload or paste API
- Add file storage integration
- Create resume and JD DB tables

#### Milestone 1.2: Parsing and Interview Context Creation
**Achievement**
- System can transform resume and JD into structured interview context

**Acceptance Criteria**
- Resume parsing extracts skills, experience, projects, and role history
- JD parsing extracts responsibilities, must-have skills, and role expectations
- System creates an interview context object for downstream interview generation

**Ticket Candidates**
- Build resume parser service
- Build JD parser service
- Define interview context schema
- Persist normalized parsed data
- Add parser job status tracking

#### Milestone 1.3: Text Interview Engine
**Achievement**
- System can run a complete interview conversation using text

**Acceptance Criteria**
- Interview session can be created
- AI asks an opening question based on context
- User can submit answers turn by turn
- AI can ask follow-up questions
- Interview stops after defined completion logic

**Ticket Candidates**
- Create interview session model
- Create interview turn model
- Build interview orchestration service
- Generate first question from resume and JD context
- Implement follow-up question logic
- Add session completion rules

#### Milestone 1.4: Reporting
**Achievement**
- User receives a useful post-interview summary and improvement feedback

**Acceptance Criteria**
- Report is generated after interview completion
- Report includes strengths, weaknesses, summary, and improvement areas
- Report is persisted and viewable later

**Ticket Candidates**
- Define report schema
- Build report generation service
- Add report retrieval endpoint
- Create report page contract for frontend

---

## Phase 2: Structured Evaluation Layer

### Objective
Move from generic feedback to structured scoring that supports analytics.

### In Scope
- rubric-based scoring
- question tagging
- skill-level evaluation
- normalized report schema

### Out of Scope
- trend graphs across interviews
- live coaching signals

### Phase Achievement
- Each interview produces measurable and comparable evaluation output

### Milestones

#### Milestone 2.1: Evaluation Schema
**Achievement**
- Structured evaluation format exists for all interviews

**Acceptance Criteria**
- Evaluation schema includes question type, skill, score, rationale, and improvement note
- Schema is stored per question and per interview

**Ticket Candidates**
- Define evaluation DB schema
- Define rubric configuration structure
- Persist skill tags and score fields

#### Milestone 2.2: Rubric-Based Scoring
**Achievement**
- Reports become more standardized and less arbitrary

**Acceptance Criteria**
- Every answer is scored against a defined rubric
- Final interview summary aggregates question-level scoring
- Reports can be compared across sessions

**Ticket Candidates**
- Implement rubric engine
- Map questions to skill categories
- Aggregate question scores into final report sections
- Add report confidence metadata

---

## Phase 3: Realtime Product Experience

### Objective
Make interviews feel live using streaming events and stable session state.

### In Scope
- WebSocket support
- live transcript updates
- session timers
- reconnect and autosave behavior

### Out of Scope
- speech input
- TTS output

### Phase Achievement
- Text interviews feel like live sessions, not page refresh workflows

### Milestones

#### Milestone 3.1: Live Session Transport
**Achievement**
- Frontend receives live updates during the interview

**Acceptance Criteria**
- Session events stream over WebSocket
- User sees new AI questions without polling
- User sees in-progress session state changes

**Ticket Candidates**
- Add FastAPI WebSocket interview endpoint
- Define event payload contract
- Add session event serializer
- Add reconnect handling

#### Milestone 3.2: Resilience and UX Stability
**Achievement**
- Interview sessions survive common interruptions

**Acceptance Criteria**
- Session state is recoverable after refresh
- Partial transcript is not lost
- Autosave works during active interviews

**Ticket Candidates**
- Add transcript chunk persistence
- Add autosave behavior
- Add session restoration endpoint
- Add stale-session recovery logic

---

## Phase 4: Voice Layer

### Objective
Add speech input and spoken interviewer responses on top of the text engine.

### In Scope
- microphone input
- STT integration
- TTS integration
- streamed transcript
- voice turn management

### Out of Scope
- advanced speech analytics
- real-person interview support

### Phase Achievement
- Candidate can complete a voice-based AI interview with transcript visibility

### Milestones

#### Milestone 4.1: Speech Input Pipeline
**Achievement**
- Spoken candidate answers are converted into usable transcript text

**Acceptance Criteria**
- Frontend can capture microphone input
- Backend can process speech input
- Transcript appears in the interview session
- Failure states are handled gracefully

**Ticket Candidates**
- Add mic capture support contract
- Build speech ingestion endpoint or stream handler
- Integrate STT provider
- Persist transcript chunks with timestamps
- Add STT retry and error handling

#### Milestone 4.2: Spoken AI Responses
**Achievement**
- AI interviewer can respond with generated voice output

**Acceptance Criteria**
- AI text response is converted into audio
- Frontend can play AI response audio
- Audio output stays linked to transcript turn

**Ticket Candidates**
- Integrate TTS provider
- Store TTS output metadata
- Add transcript-to-audio mapping
- Add audio playback state events

#### Milestone 4.3: Voice Turn Orchestration
**Achievement**
- Voice interviews feel coherent and usable

**Acceptance Criteria**
- Turn-taking is stable
- User and AI do not overlap unpredictably
- Voice and transcript remain synchronized

**Ticket Candidates**
- Build turn-state manager
- Add interruption handling logic
- Add timeout and silence handling
- Add transcript and audio sync state tracking

---

## Phase 5: Interview History and Performance Tracking

### Objective
Give users a reason to return by showing longitudinal progress.

### In Scope
- interview history
- trend views
- category-wise progress
- role-readiness tracking

### Out of Scope
- advanced personalized coaching engine

### Phase Achievement
- Users can see how they improve over time

### Milestones

#### Milestone 5.1: Interview History
**Achievement**
- Users can review previous interview sessions and reports

**Acceptance Criteria**
- User can list previous interviews
- User can open a prior report
- User can review stored transcript and summary

**Ticket Candidates**
- Add interview history endpoint
- Add report listing endpoint
- Add transcript retrieval endpoint

#### Milestone 5.2: Progress Analytics
**Achievement**
- Users can see score and readiness trends across sessions

**Acceptance Criteria**
- Trends exist for score categories
- Skills can be compared over time
- Repeated practice areas are visible

**Ticket Candidates**
- Build analytics aggregation queries
- Add score trend endpoint
- Add skill trend endpoint
- Define role-readiness metric

---

## Phase 6: Advanced Coaching Intelligence

### Objective
Turn feedback into specific, actionable coaching.

### In Scope
- personalized recommendations
- weak-topic practice suggestions
- answer rewrites
- example ideal answers
- confidence and pacing indicators

### Out of Scope
- formal psychometric assessment
- guaranteed emotion detection

### Phase Achievement
- The platform provides coaching, not only scoring

### Milestones

#### Milestone 6.1: Personalized Feedback Engine
**Achievement**
- Feedback is tailored to the user's repeated weaknesses

**Acceptance Criteria**
- User receives next-step recommendations
- Recommendations are linked to actual performance history
- Suggested practice areas are specific and role-relevant

**Ticket Candidates**
- Build recommendation generator
- Add weakness clustering logic
- Add practice-topic suggestion service

#### Milestone 6.2: Communication Signal Layer
**Achievement**
- Users get more detailed interview-quality signals

**Acceptance Criteria**
- System can compute communication indicators such as hesitation, pace, filler density, or answer completeness
- Metrics are presented as coaching signals, not absolute truth

**Ticket Candidates**
- Define communication signal schema
- Compute transcript-based pacing metrics
- Compute filler word metrics
- Build coaching signal summary generator

---

## Phase 7: Human Interviewer Readiness

### Objective
Prepare architecture and workflows for real-person interview support.

### In Scope
- participant roles
- scheduling model
- permission model
- notes and replay support

### Out of Scope
- full marketplace operations
- billing for interviewers

### Phase Achievement
- The system can evolve from AI-only sessions to human-supported sessions without rewrite

### Milestones

#### Milestone 7.1: Generalized Session Model
**Achievement**
- Interview sessions support different participant types

**Acceptance Criteria**
- Session can represent AI interviewer and human interviewer roles
- Transcript and report models work for both session types

**Ticket Candidates**
- Refactor participant model
- Refactor session role model
- Generalize transcript ownership fields

#### Milestone 7.2: Human Review Workflow
**Achievement**
- Human interviewers or reviewers can participate and annotate sessions

**Acceptance Criteria**
- Human reviewer can add notes
- Session replay is possible
- Review notes can coexist with AI-generated analysis

**Ticket Candidates**
- Add reviewer note model
- Add replay metadata support
- Add human reviewer permissions

---

## Phase 8: Productization and External Integrations

### Objective
Turn the platform into a reusable API product for third parties.

### In Scope
- API keys
- org or tenant model
- public APIs
- webhooks
- usage controls

### Out of Scope
- enterprise procurement workflows
- custom enterprise billing

### Phase Achievement
- External platforms can integrate interview creation, execution, and result retrieval

### Milestones

#### Milestone 8.1: Public API Foundation
**Achievement**
- Platform exposes stable external APIs

**Acceptance Criteria**
- External client can authenticate using API key or OAuth pattern
- External client can create an interview session
- External client can fetch results

**Ticket Candidates**
- Add API key model
- Add API key auth middleware
- Build public create interview endpoint
- Build public get report endpoint
- Add API usage logging

#### Milestone 8.2: Integration Readiness
**Achievement**
- Product can notify external systems and operate in multi-organization contexts

**Acceptance Criteria**
- Webhook events exist for important lifecycle actions
- Organization scoping is enforced
- Rate limits and usage tracking are available

**Ticket Candidates**
- Add organization model
- Add tenant scoping middleware
- Add webhook event model
- Add webhook dispatcher
- Add rate limit middleware

---

## 10. System-Level Functional Requirements

### Resume and JD Processing
- System must accept resume uploads
- System must accept JD upload or paste input
- System must parse both inputs into normalized structured data

### Interview Engine
- System must generate personalized questions
- System must ask follow-up questions based on previous answers
- System must persist every interview turn
- System must generate final report output

### Evaluation
- System must score interviews using a structured schema
- System must support skill-based evaluation
- System must support future trend calculations across interviews

### Realtime
- System must support streamed events for active interviews
- System must preserve active session state
- System must recover interrupted sessions where possible

### Voice
- System must support STT integration
- System must support TTS integration
- System must keep transcript and audio associated with each turn

### Productization
- System must support public API authentication
- System must support tenant-aware API usage
- System must support webhook notifications

## 11. Non-Functional Requirements

### Reliability
- Active interview sessions should not lose state during common refresh or reconnect scenarios
- Background jobs should be retryable

### Performance
- Text interview interaction should feel responsive
- Realtime transcript updates should arrive with low visible delay

### Security
- User files and transcripts must be stored securely
- Access to interviews and reports must be scoped to the authorized user or tenant
- API keys must be stored and handled securely

### Maintainability
- Business logic should be modular
- Interview orchestration should be reusable across text and voice modes
- Schemas should be stable and documented

## 12. Suggested MVP Tech Shape

### Recommended Initial Stack
- Backend: FastAPI
- Database: Postgres
- Cache and queue: Redis
- Background jobs: Celery or RQ
- ORM: SQLAlchemy or SQLModel
- Storage: S3-compatible object storage
- Realtime: FastAPI WebSockets

### Recommended Architectural Style
- Modular monolith
- Separate modules for:
  - auth
  - uploads
  - parsing
  - interviews
  - transcripts
  - evaluation
  - analytics
  - integrations

## 13. Suggested Development Order

1. Phase 0
2. Phase 1
3. Phase 2
4. Phase 3
5. Phase 4
6. Phase 5
7. Phase 6
8. Phase 7
9. Phase 8

## 14. Ticketing Guidance

Use this PRD to create tickets in three layers:

### Product Tickets
- define personas
- define rubric rules
- define report structure
- define metrics and dashboards

### Backend Tickets
- build endpoints
- define schemas
- implement workers
- add storage and persistence

### Platform Tickets
- add auth hardening
- add tenant model
- add API key flows
- add webhook support

## 15. Definition of Success

### MVP Success
- Users can complete an end-to-end interview
- Reports are useful enough that users want to retry
- Data model is clean enough to support future analytics

### Product Success
- Users return for repeated interviews
- Performance tracking becomes meaningful over time
- Voice experience feels natural enough to use repeatedly
- External platforms can integrate the interview engine with low friction

## 16. Immediate Next Step Recommendation

Start execution with the following implementation order:
- finalize Phase 0 scope in one page
- build Phase 1 backend data model
- build upload and parsing flow
- build text interview orchestration
- build report generation

After that, create engineering tickets directly from Milestones 1.1 to 1.4.
