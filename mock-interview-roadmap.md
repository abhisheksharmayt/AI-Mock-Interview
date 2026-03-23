# AI Mock Interview Product Roadmap

## Product Goal

Build an AI mock interview platform that starts with resume- and JD-based mock interviews, then evolves into a realtime voice product with long-term performance tracking, coaching insights, and eventually human interviewer support.

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
  - text-based mock interview
  - final feedback report

**Output of this phase**
- A narrow v1 scope
- A clear target user
- A success-metric baseline for the MVP

## Phase 1: Core MVP

**Goal:** Make the mock interview engine work end to end with a text-based interview.

**Build**
- User authentication
- Resume upload
- JD upload
- Resume and JD parsing pipeline
- Interview session creation
- Text chat interview UI
- Backend-generated interview questions
- Follow-up questions based on previous answers
- Transcript storage
- Final report page

**Backend responsibilities**
- Extract skills, projects, and experience from the resume
- Extract role requirements and expected skills from the JD
- Generate an interview plan
- Conduct an interview with roughly 8-15 questions
- Save every turn in the conversation
- Generate final feedback across:
  - communication
  - relevance
  - technical depth
  - confidence
  - improvement areas

**Deliverable**
- A user can upload a resume and JD, complete one full text interview, and receive a useful report

**Do not build yet**
- Voice interview
- Sentiment graph
- Human interviewer mode
- Third-party integration platform

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

**Goal:** Make the interview feel like a live session instead of a simple request-response chat.

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
- Keep the interview engine independent from the transport layer so it can work for both text and voice later

## Phase 4: Voice Layer

**Goal:** Add speech input and spoken AI responses on top of the already working text interview engine.

**Build**
- Microphone input in the frontend
- Speech-to-text pipeline
- Text-to-speech response pipeline
- Streaming transcript updates
- Voice turn management
- Retry and fallback behavior for transcription failures

**Product rule**
- Voice should sit on top of the same interview engine built earlier
- Avoid separate business logic for text interviews and voice interviews

**Deliverable**
- A user can speak to the AI interviewer, hear responses, and follow the transcript in realtime

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
- Treat text interview support as the foundation and voice as an experience layer on top.
- Design the data model early for interview history, structured scoring, and analytics.
- Avoid premature microservices.
- Keep business logic reusable across text, voice, AI-led, and human-led interviews.
