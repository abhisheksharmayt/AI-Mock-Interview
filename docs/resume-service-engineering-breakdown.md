# Resume Service Engineering Task Breakdown

## 1. Purpose

This document converts the resume service scope into an engineering execution breakdown. It covers resume upload, background parsing via OpenAI, parsed data persistence, and production deployment on AWS EC2 using Docker.

## 2. Workstreams

- Backend API and service layer
- Data model and persistence
- File ingestion and text extraction
- AI parsing and structured output
- Containerisation and deployment

## 3. Ticket Format

Each task is created with:
- title
- summary
- owner
- dependency
- acceptance criteria
- estimate
- status

Ticket prefixes used:
- `BE` for backend API and service layer
- `DB` for schema and migrations
- `AI` for parsing and LLM logic
- `PLT` for platform, infra, and deployment

---

## 4. Phase 1: Resume Upload (Complete)

### Goal
Allow authenticated users to upload a resume file which is stored in S3 and recorded in the database with a `pending` parse status.

### Workstream A: Data Model

#### `DB-001` Create files table
- Link to user
- Store storage key, original filename, mime type, size
- Store file kind enum (resume, job_description, audio, report_export)
- Add user_id and kind indexes
- **Status:** Done

#### `DB-002` Create resumes table
- Link to user and files
- Store parse_status enum (pending, processing, completed, failed)
- Store is_default flag
- Add user_id and parse_status indexes
- **Status:** Done

#### `DB-003` Create parsed_resumes table
- Link to resumes with cascade delete
- Store full_text, candidate_summary, total_years_experience
- Store skills_json, experience_json, education_json, projects_json, certifications_json as JSONB
- Store parse_metadata_json as JSONB
- Enforce unique constraint on resume_id (one parsed output per resume)
- **Status:** Done

### Workstream B: API and Storage

#### `BE-001` Add storage abstraction
- Use MinIO in development (ENV=dev)
- Use real AWS S3 in production (ENV=prod)
- Upload, download, and delete object methods
- **Status:** Done

#### `BE-002` Add resume upload endpoint
- `POST /api/v1/resume/upload`
- Validate file extension (.pdf, .docx, .doc only)
- Upload file bytes to S3 under resumes/ prefix
- Create File and Resume records in a single transaction
- Roll back S3 object if DB insert fails
- Return 400 for invalid extension, 503 for storage failure
- **Status:** Done

#### `BE-003` Add JD create endpoint
- `POST /api/v1/resume/jd`
- Accept raw text, title, company name, role
- Save to job_descriptions table
- **Status:** Done

### Exit Criteria
- Authenticated user can upload a PDF or DOCX
- File stored in S3, File and Resume records created
- parse_status starts as pending
- Invalid file types and storage failures handled gracefully

---

## 5. Phase 2: Resume Parsing Pipeline

### Goal
Automatically extract structured data from uploaded resumes using text extraction and OpenAI, storing results in parsed_resumes.

### Workstream A: Text Extraction

#### `AI-001` Add text extraction dependencies
- Add pdfplumber to requirements.txt for PDF parsing
- Add python-docx to requirements.txt for DOCX parsing
- **Dependency:** None
- **Estimate:** 0.5 days
- **Status:** To Do

#### `AI-002` Implement resume text extractor utility
- Create utils/resume_text_extractor.py
- .pdf → extract text using pdfplumber via BytesIO
- .docx → extract text using python-docx via BytesIO
- .doc → raise ValueError with message (format not supported)
- Empty or scanned PDFs return empty string without raising
- **Dependency:** AI-001
- **Estimate:** 1 day
- **Status:** To Do

### Workstream B: AI Structured Extraction

#### `AI-003` Add OpenAI dependency and config
- Add openai to requirements.txt
- Add OPENAI_API_KEY to Configs class via os.getenv
- **Dependency:** None
- **Estimate:** 0.5 days
- **Status:** To Do

#### `AI-004` Design extraction prompt
- Prompt instructs gpt-4o to return a JSON object with:
  - skills_json: array of {name, level}
  - experience_json: array of {company, title, start_date, end_date, description}
  - education_json: array of {institution, degree, field, graduation_year}
  - projects_json: array of {name, description, tech_stack}
  - certifications_json: array of {name, issuer, year}
  - candidate_summary: 2-3 sentence summary of the candidate
  - total_years_experience: decimal or null
- Use response_format=json_object to guarantee valid JSON output
- **Dependency:** AI-003
- **Estimate:** 1 day
- **Status:** To Do

#### `AI-005` Implement AI resume parser utility
- Create utils/ai_resume_parser.py
- async function parse_resume_with_ai(raw_text: str) -> dict
- Call gpt-4o with the extraction prompt
- Parse and validate the JSON response
- Raise exception on API error or malformed response
- Log model used and parsed_at in parse_metadata_json
- **Dependency:** AI-004
- **Estimate:** 1 day
- **Status:** To Do

### Workstream C: Persistence

#### `DB-004` Add ParsedResumeCreate schema
- Add ParsedResumeCreate Pydantic model to schemas/resume.py
- Fields: resume_id, full_text, candidate_summary, total_years_experience, skills_json, experience_json, education_json, projects_json, certifications_json, parse_metadata_json
- **Dependency:** DB-003
- **Estimate:** 0.5 days
- **Status:** To Do

#### `DB-005` Add parsed resume repository methods
- Add ResumeRepository.create_parsed_resume(data: ParsedResumeCreate)
- Add ResumeRepository.update_resume_parse_status(resume_id, status)
- Both wrapped in try/except with rollback
- **Dependency:** DB-004
- **Estimate:** 1 day
- **Status:** To Do

### Workstream D: Background Task Orchestration

#### `BE-004` Implement parse_resume_background function
- Standalone async function in services/resume.py (not a class method)
- Creates its own AsyncSession via AsyncSessionLocal
- Transitions: pending → processing → completed (or failed)
- Calls extract_text then parse_resume_with_ai
- Inserts ParsedResume record on success
- Catches all exceptions, sets parse_status=failed, logs resume_id
- Failed parse never leaves a partial parsed_resumes row
- **Dependency:** AI-002, AI-005, DB-005
- **Estimate:** 1 day
- **Status:** To Do

#### `BE-005` Wire BackgroundTasks into upload flow
- Add BackgroundTasks dependency to ResumeService.upload_resume
- Call background_tasks.add_task(parse_resume_background, resume.id, file_content, extension) after DB record created
- **Dependency:** BE-004
- **Estimate:** 0.5 days
- **Status:** To Do

#### `BE-006` Add BackgroundTasks to upload router
- Inject BackgroundTasks into POST /resume/upload handler
- Pass it to ResumeService
- **Dependency:** BE-005
- **Estimate:** 0.5 days
- **Status:** To Do

### Exit Criteria
- Upload returns 200 before parsing begins
- parse_status transitions: pending → processing → completed or failed
- parsed_resumes row populated with all structured fields on success
- .doc files and API failures fail gracefully with parse_status=failed
- All errors logged with resume_id

---

## 6. Phase 3: Containerisation and Deployment

### Goal
Package the backend as a Docker image and deploy to AWS EC2 with a containerised PostgreSQL and real AWS S3.

### Workstream A: Config Cleanup

#### `PLT-001` Move hardcoded values to environment variables
- Read DATABASE_URL from os.getenv in db/database.py (currently hardcoded)
- Add DATABASE_URL, AWS_REGION, ENV to Configs class
- **Dependency:** None
- **Estimate:** 0.5 days
- **Status:** To Do

#### `PLT-002` Write .env.example
- Document all required env vars with placeholders:
  - JWT_SECRET_KEY
  - ENV (dev or prod)
  - API_PREFIX
  - OPENAI_API_KEY
  - DATABASE_URL
  - AWS_REGION
  - S3_RESUME_BUCKET
- **Dependency:** PLT-001
- **Estimate:** 0.5 days
- **Status:** To Do

### Workstream B: Docker

#### `PLT-003` Write Dockerfile for backend
- Base image: python:3.13-slim
- Copy requirements.txt and install dependencies
- Copy application code
- Start with: uvicorn app.main:app --host 0.0.0.0 --port 8000
- **Dependency:** PLT-001
- **Estimate:** 0.5 days
- **Status:** To Do

#### `PLT-004` Write .dockerignore
- Exclude: .env, .env.prod, __pycache__, .venv, .git, *.pyc
- **Dependency:** PLT-003
- **Estimate:** 0.25 days
- **Status:** To Do

#### `PLT-005` Write docker-compose.yml for local development
- api service: FastAPI, env_file backend/.env, depends on db and minio with health checks
- db service: postgres:16-alpine, named volume, healthcheck
- minio service: MinIO on port 9000 (API) and 9001 (console)
- **Dependency:** PLT-003
- **Estimate:** 1 day
- **Status:** To Do

#### `PLT-006` Write docker-compose.prod.yml for EC2
- api service: FastAPI, env_file backend/.env.prod
- db service: postgres:16-alpine, named volume
- No MinIO — uses real AWS S3 via IAM Role
- **Dependency:** PLT-003
- **Estimate:** 0.5 days
- **Status:** To Do

### Workstream C: AWS Setup

#### `PLT-007` Create and configure S3 bucket
- Create bucket in AWS console (e.g. ai-mock-interview-resumes)
- Block all public access
- Note bucket name and region for .env.prod
- **Dependency:** None
- **Estimate:** 0.5 days
- **Status:** To Do

#### `PLT-008` Create EC2 IAM Role for S3 access
- Create IAM Role with trusted entity: EC2
- Attach AmazonS3FullAccess policy (scope to bucket later)
- No access keys needed — boto3 uses instance metadata automatically
- **Dependency:** PLT-007
- **Estimate:** 0.5 days
- **Status:** To Do

#### `PLT-009` Launch and configure EC2 instance
- Ubuntu 22.04, t3.small
- Security Group: port 22 (SSH from your IP), port 8000 (API public)
- Attach IAM Role created in PLT-008
- Install Docker and Docker Compose
- **Dependency:** PLT-008
- **Estimate:** 1 day
- **Status:** To Do

#### `PLT-010` Deploy application to EC2
- Clone repo on EC2
- Create backend/.env.prod from .env.example
- Run: docker compose -f docker-compose.prod.yml up -d --build
- Run: docker compose -f docker-compose.prod.yml exec api alembic upgrade head
- Verify health endpoint responds
- **Dependency:** PLT-006, PLT-009
- **Estimate:** 1 day
- **Status:** To Do

### Exit Criteria
- docker compose up starts full local stack with one command
- Local resume upload stores to MinIO, parses via OpenAI
- EC2 instance serves the API on port 8000
- Production resume upload stores to real S3
- Alembic migrations run on first deploy

---

## 7. Suggested Execution Order

### Sprint 1: Parsing Pipeline
1. `AI-001` Add text extraction dependencies
2. `AI-002` Implement resume text extractor
3. `AI-003` Add OpenAI dependency and config
4. `AI-004` Design extraction prompt
5. `AI-005` Implement AI resume parser
6. `DB-004` Add ParsedResumeCreate schema
7. `DB-005` Add parsed resume repository methods
8. `BE-004` Implement parse_resume_background
9. `BE-005` Wire BackgroundTasks into upload service
10. `BE-006` Add BackgroundTasks to upload router

### Sprint 2: Containerisation and Deployment
1. `PLT-001` Move hardcoded values to env vars
2. `PLT-002` Write .env.example
3. `PLT-003` Write Dockerfile
4. `PLT-004` Write .dockerignore
5. `PLT-005` Write docker-compose.yml (local dev)
6. `PLT-006` Write docker-compose.prod.yml (EC2)
7. `PLT-007` Create S3 bucket
8. `PLT-008` Create EC2 IAM Role
9. `PLT-009` Launch EC2 instance
10. `PLT-010` Deploy application

---

## 8. Ticket Grouping for Solo Builder

### Bucket 1: Parsing (start here)
- `AI-001` → `AI-002` → `AI-003` → `AI-004` → `AI-005`
- `DB-004` → `DB-005`
- `BE-004` → `BE-005` → `BE-006`

### Bucket 2: Deployment
- `PLT-001` → `PLT-002` → `PLT-003` → `PLT-004`
- `PLT-005` → `PLT-006`
- `PLT-007` → `PLT-008` → `PLT-009` → `PLT-010`

---

## 9. Immediate Next Tickets

1. `AI-001` Add pdfplumber and python-docx to requirements.txt
2. `AI-003` Add openai to requirements.txt and OPENAI_API_KEY to Configs
3. `AI-002` Implement resume_text_extractor.py
4. `AI-004` Design extraction prompt
5. `AI-005` Implement ai_resume_parser.py
6. `DB-004` Add ParsedResumeCreate schema
7. `DB-005` Add repository methods for parsed resume
8. `BE-004` Implement parse_resume_background

---

## 10. Definition of Completion

### Parsing Complete
- Upload returns 200 immediately
- parse_status tracks the full lifecycle
- parsed_resumes populated with structured fields after each successful upload
- Failed parses set parse_status=failed with no partial rows

### Deployment Complete
- Single docker compose up runs local stack end to end
- EC2 serves the API with production S3 and containerised Postgres
- Alembic migrations run on deploy
- No secrets or credentials hardcoded in code or Docker images
