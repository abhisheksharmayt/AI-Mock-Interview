# Resume Parsing Service

## Overview

After a resume is uploaded, the system automatically parses it in the background and stores the structured output in the `parsed_resumes` table. The upload API returns immediately — parsing happens asynchronously so users aren't kept waiting.

---

## Flow

```
POST /api/v1/resume/upload
        │
        ├── Validate file extension (.pdf / .docx)
        ├── Upload raw file to S3
        ├── Create records in `files` + `resumes` tables
        │     parse_status = pending
        │
        └── Schedule background task → return HTTP 200
                │
                ▼
        [Background Task]
                │
                ├── parse_status = processing
                ├── Download file bytes from memory
                ├── Extract plain text
                │     .pdf  → pdfplumber
                │     .docx → python-docx
                │     .doc  → not supported → skip to failed
                │
                ├── Send text to OpenAI API (gpt-4o)
                │     → returns structured JSON
                │
                ├── Insert row into `parsed_resumes`
                └── parse_status = completed
                                  (or failed on any error)
```

---

## parse_status States

| Status | Meaning |
|--------|---------|
| `pending` | Upload done, parsing not started yet |
| `processing` | Text extraction + AI parsing in progress |
| `completed` | `parsed_resumes` row populated successfully |
| `failed` | Error during extraction or AI call — see API logs |

---

## Supported File Formats

| Extension | Supported | Notes |
|-----------|-----------|-------|
| `.pdf` | Yes | Uses `pdfplumber` |
| `.docx` | Yes | Uses `python-docx` |
| `.doc` | No | Old binary format — upload succeeds, parsing fails gracefully with `parse_status = failed` |

---

## parsed_resumes Table

One row per resume. Populated after successful parsing.

| Column | Type | Description |
|--------|------|-------------|
| `resume_id` | UUID | FK to `resumes.id` (unique — one parsed output per resume) |
| `full_text` | Text | Complete raw text extracted from the file |
| `candidate_summary` | Text | AI-generated 2-3 sentence summary of the candidate |
| `total_years_experience` | Decimal(4,1) | Estimated total years of work experience |
| `skills_json` | JSONB | Array of skill objects |
| `experience_json` | JSONB | Array of work experience entries |
| `education_json` | JSONB | Array of education entries |
| `projects_json` | JSONB | Array of project entries |
| `certifications_json` | JSONB | Array of certification entries |
| `parse_metadata_json` | JSONB | Parser metadata (model used, duration, etc.) |

### JSON shapes

**skills_json**
```json
[
  { "name": "Python", "level": "expert" },
  { "name": "FastAPI", "level": "intermediate" }
]
```

**experience_json**
```json
[
  {
    "company": "Acme Corp",
    "title": "Software Engineer",
    "start_date": "2021-06",
    "end_date": "2024-01",
    "description": "Built REST APIs using FastAPI..."
  }
]
```

**education_json**
```json
[
  {
    "institution": "IIT Delhi",
    "degree": "B.Tech",
    "field": "Computer Science",
    "graduation_year": "2021"
  }
]
```

**projects_json**
```json
[
  {
    "name": "AI Mock Interview",
    "description": "A platform for AI-powered mock interviews",
    "tech_stack": ["FastAPI", "PostgreSQL", "Claude API"]
  }
]
```

**certifications_json**
```json
[
  {
    "name": "AWS Solutions Architect",
    "issuer": "Amazon",
    "year": "2023"
  }
]
```

**parse_metadata_json**
```json
{
  "model": "gpt-4o",
  "extraction_method": "pdfplumber",
  "parsed_at": "2026-04-09T10:30:00Z"
}
```

---

## Key Files

| File | Role |
|------|------|
| `backend/app/utils/resume_text_extractor.py` | Extracts plain text from PDF/DOCX bytes |
| `backend/app/utils/ai_resume_parser.py` | Calls OpenAI API, returns structured dict |
| `backend/app/services/resume.py` | `parse_resume_background()` — orchestrates the full parse flow |
| `backend/app/repositories/resume.py` | `create_parsed_resume()`, `update_resume_parse_status()` |
| `backend/app/models/resume.py` | `ParsedResume` SQLModel table definition |
| `backend/app/schemas/resume.py` | `ParsedResumeCreate` Pydantic schema |

---

## Background Task — How It Works

FastAPI's `BackgroundTasks` runs the parsing function **after** the HTTP response is sent. This means:

- The user gets an instant `200 OK` on upload
- Parsing runs in the same process/event loop in the background
- The background task creates its **own database session** (the request session is already closed by then)

```
Request lifecycle:
  → upload_resume() called
  → file uploaded to S3, DB record created
  → background task registered
  → HTTP 200 returned to client   ←── client is unblocked here
  → parse_resume_background() runs
```

> **Note:** If the server restarts mid-parse, the resume will be stuck at `processing`. A future improvement can add a startup job to reset stuck resumes back to `pending`.

---

## OpenAI API Prompt Design

The raw extracted text is sent to `gpt-4o` with a structured prompt asking it to return a JSON object. The model is instructed to:

- Extract all skills with proficiency level where inferable
- Extract each work experience with company, title, dates, and description
- Extract education with institution, degree, field, and graduation year
- Extract projects and certifications
- Write a short candidate summary (2-3 sentences)
- Estimate total years of experience as a decimal number

The response is parsed as JSON and mapped directly to the `ParsedResumeCreate` schema before being inserted into the database.

---

## Error Handling

| Scenario | Outcome |
|----------|---------|
| Unsupported `.doc` format | `parse_status = failed`, no `parsed_resumes` row |
| PDF has no extractable text (scanned image) | `full_text` is empty, OpenAI returns best-effort output |
| OpenAI API key invalid / rate limited | Exception caught, `parse_status = failed`, logged |
| DB insert fails | Exception caught, `parse_status = failed`, logged |

All errors are logged with `loguru` including the `resume_id` for easy debugging:

```bash
docker compose logs -f api | grep "resume_id"
```

---

## Adding a New File Format

To support a new format (e.g. `.txt`):

1. Add the extension to `allowed_extensions` in `ResumeService`
2. Add a handler branch in `resume_text_extractor.py`
3. No other changes needed — the rest of the pipeline is format-agnostic
