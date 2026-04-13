# AI Mock Interview Product Roadmap

## Product Goal

Build an AI mock interview platform that starts with resume- and JD-based voice-first interviews with live transcript support, then evolves into stronger coaching, long-term performance tracking, and eventually human interviewer support.

## Phase 0: Product Definition

**Goal:** Define the initial product clearly enough to avoid building unnecessary infrastructure.

**Decisions to make**
- Choose the first target user segment: freshers, experienced engineers, PMs, designers, or a broader job-seeker audience.
- Choose the first interview type: behavioral, resume-based, JD-based, technical screening, or a hybrid flow.
- Define success metrics:
  - interview completion rate
  - report generation rate
  - repeat interviews per user
  - average session duration
- Freeze v1 scope:
  - resume upload
  - JD upload
  - voice-first mock interview
  - live transcript
  - final feedback report

**Output of this phase**
- A narrow v1 scope
- A clear target user
- A success-metric baseline for the MVP

## Phase 1: Core MVP

**Goal:** Make the mock interview engine work end to end with a voice-only interview.

**Home screen**
- Resume section: list of uploaded resumes shown inline on screen, with option to upload a new one (PDF or DOCX)
- Interview Sessions section: list of past sessions; clicking one shows JD, company, role, and session details
- Start Interview: entry point for a new session

**Start Interview flow**
- User picks a resume from their uploaded list
- User selects an interview type (behavioral, resume-based, technical screening)
- User pastes the job description text
- User enters the company name and the role they are applying for
- User starts the interview immediately — no additional setup steps

**Build**
- User authentication
- Resume upload and resume list API
- JD intake via paste (no file upload for JD in v1)
- Company name and role fields tied to each interview session
- Resume parsing pipeline (JD is raw text — no parsing needed)
- Interview session creation linked to selected resume and JD
- Interview type selection
- Microphone input flow (voice only — no text input mode in v1)
- Speech-to-text pipeline
- Text-to-speech response pipeline
- Live transcript support
- Backend-generated interview questions
- Follow-up questions based on previous answers
- Transcript storage
- Interview sessions list and detail view
- Final report page

**Backend responsibilities**
- Extract skills, projects, and experience from the resume
- Use raw JD text directly as interview context — no JD parsing step
- Generate an interview plan using resume + JD + company + role context
- Conduct an interview with roughly 8-15 questions
- Save every turn in the conversation
- Generate final feedback across:
  - communication
  - relevance
  - technical depth
  - confidence
  - improvement areas

**Deliverable**
- A user can upload a resume, start a voice interview for a specific company and role, complete the session, and receive a useful report. Past sessions are visible on the home screen.

**Do not build yet**
- Text or hybrid interview modes
- Advanced voice analytics
- Sentiment graph
- Human interviewer mode
- Third-party integration platform

**Execution note**
- Voice is the only supported interview mode in v1. Pull the minimum required STT and TTS work forward so the product is shippable from day one.

## Phase 2: Structured Evaluation Layer

**Goal:** Turn free-form feedback into clean, structured evaluation data.

**Build**
- Scoring rubric per interview
- Section-wise scoring
- Skill tags for each question
- Standardized answer evaluation schema
- Interview summary generation
- Benchmark metadata for later comparisons

**Store structured data such as**
- Question type
- Skill being tested
- Answer score
- Follow-up depth
- Strengths
- Weaknesses

**Deliverable**
- Each interview produces structured analytics, not only a free-text summary

**Why this phase matters**
- Future dashboards and performance comparisons depend on consistent structured data

## Phase 3: Realtime Product Experience

**Goal:** Make the live voice interview feel stable and responsive.

**Build**
- FastAPI WebSocket session channel
- Live transcript updates on the frontend
- Typing and response state
- Timer per question or round
- Interruption-safe session state
- Autosave and reconnect support

**Deliverable**
- A live interview experience with streamed transcript and stable session state

**Note**
- Keep the interview engine independent from the transport layer so it can work cleanly with voice and later human-led sessions

## Phase 4: Voice Layer

**Goal:** Improve voice reliability, turn management, and spoken response quality on top of the MVP.

**Build**
- Improved microphone input handling
- Speech-to-text retry and fallback behavior
- Text-to-speech response pipeline hardening
- Streaming transcript updates
- Voice turn management
- Retry and fallback behavior for transcription failures

**Product rule**
- Voice should use the same interview engine built earlier
- Avoid separate business logic for voice interviews and later interaction modes

**Deliverable**
- A user can speak to the AI interviewer, hear reliable responses, and follow the transcript in realtime

## Phase 5: Interview History and Performance Tracking

**Goal:** Create long-term user value and retention through progress tracking.

**Build**
- Interview history page
- Performance trends over time
- Score trends by category
- Role-readiness tracking
- Skill progression charts
- Comparison across multiple interviews

**Metrics to show**
- Communication trend
- Technical clarity trend
- Answer completeness trend
- Role readiness trend
- Strongest and weakest skill areas

**Deliverable**
- Users can see measurable improvement across multiple interviews

## Phase 6: Advanced Coaching Intelligence

**Goal:** Make the product feel like a coach, not only an interviewer.

**Build**
- Personalized recommendations
- Targeted practice suggestions
- Weak-topic drills
- Answer rewrite suggestions
- Model-generated ideal answer examples
- Confidence, filler-word, hesitation, and pacing indicators

**Important product framing**
- Avoid presenting a simplistic "sentiment graph" as the core feature
- Prefer actionable coaching signals such as:
  - confidence
  - hesitation
  - pace
  - relevance
  - clarity

**Deliverable**
- Feedback becomes more actionable and tailored to the individual user

## Phase 7: Human Interviewer Readiness

**Goal:** Prepare the platform architecture for future human-led interviews.

**Build foundations**
- A generic interview session model
- Participant roles:
  - candidate
  - AI interviewer
  - human interviewer
- Scheduling model
- Session recording model
- Permission model
- Reviewer notes
- Replay and transcript review

**Architecture requirement**
- Separate AI interview logic from general session infrastructure
- Ensure transcripts, recordings, and reports work for both AI and human sessions

**Deliverable**
- The platform is ready to support real-person interviews without a major rewrite

## Phase 8: Productization and External Integrations

**Goal:** Turn the platform into a product other companies or platforms can integrate.

**Build**
- API keys
- Organization and tenant model
- Usage limits
- Webhook events
- Public API documentation
- Interview creation API
- Report retrieval API
- Candidate session API
- Admin analytics

**Potential integration targets**
- Bootcamps
- Colleges
- Hiring platforms
- Internal learning and development teams
- Assessment partners

**Deliverable**
- External systems can create interviews, retrieve results, and embed your interview workflows

## Recommended Build Order

1. Phase 0: Product Definition
2. Phase 1: Core MVP
3. Phase 2: Structured Evaluation Layer
4. Phase 3: Realtime Product Experience
5. Phase 4: Voice Layer
6. Phase 5: Interview History and Performance Tracking
7. Phase 6: Advanced Coaching Intelligence
8. Phase 7: Human Interviewer Readiness
9. Phase 8: Productization and External Integrations

## PM Notes

- Start with the narrowest version that proves the product value.
- Treat voice as the foundation and transcript as a supporting layer.
- Design the data model early for interview history, structured scoring, and analytics.
- Avoid premature microservices.
- Keep business logic reusable across voice, transcript, AI-led, and human-led interviews.
