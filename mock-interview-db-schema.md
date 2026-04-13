# AI Mock Interview Platform Database Schema Draft

## 1. Purpose

This schema draft is designed for a FastAPI + Postgres architecture and supports:
- resume upload
- JD upload
- personalized interview generation
- voice-first AI interviews
- transcript storage
- audio metadata storage
- structured scoring
- performance analytics
- future human interviewer support
- future external integrations

This is a product-oriented schema, not a final migration file. It is intended to guide implementation.

## 2. Design Principles

- Use UUIDs for primary keys
- Keep interview business logic reusable across voice, transcript, AI, and human-led sessions
- Treat voice as the default interview mode and transcript as a support layer
- Store structured outputs for analytics, not only free text
- Separate raw session events from normalized transcript and report data
- Add future-proofing for orgs, API keys, and webhook integrations without forcing them into MVP flows

## 3. Suggested Postgres Extensions

- `uuid-ossp` or `pgcrypto` for UUID generation
- `citext` for case-insensitive email fields if preferred
- `pg_trgm` later for fuzzy search if needed

## 4. Core Enums

These can be implemented as Postgres enums or constrained string fields.

### `user_role`
- `candidate`
- `admin`
- `reviewer`

### `file_kind`
- `resume`
- `job_description`
- `audio`
- `report_export`

### `parse_status`
- `pending`
- `processing`
- `completed`
- `failed`

### `interview_status`
- `draft`
- `ready`
- `in_progress`
- `completed`
- `abandoned`
- `failed`

### `interview_mode`
- `text`
- `voice`
- `hybrid`

### `interviewer_type`
- `ai`
- `human`

### `participant_role`
- `candidate`
- `ai_interviewer`
- `human_interviewer`
- `reviewer`

### `speaker_type`
- `candidate`
- `assistant`
- `system`
- `reviewer`

### `turn_kind`
- `question`
- `answer`
- `follow_up`
- `system_message`
- `feedback`

### `evaluation_scope`
- `turn`
- `session`

### `session_event_type`
- `session_created`
- `session_started`
- `question_generated`
- `answer_received`
- `transcript_updated`
- `audio_generated`
- `report_generated`
- `session_completed`
- `error`

### `webhook_status`
- `active`
- `disabled`

## 5. Core Tables

## `users`

Primary user account table.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `email` | `varchar unique not null` | use `citext` if available |
| `password_hash` | `varchar not null` | |
| `full_name` | `varchar` | |
| `role` | `user_role not null default 'candidate'` | |
| `is_active` | `boolean not null default true` | |
| `last_login_at` | `timestamptz` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- unique index on `email`
- index on `role`

## `user_profiles`

Optional extension table to avoid bloating `users`.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id unique not null` | |
| `headline` | `varchar` | |
| `target_role` | `varchar` | |
| `years_of_experience` | `numeric(4,1)` | |
| `current_company` | `varchar` | |
| `preferred_interview_type` | `varchar` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

## 6. File and Document Intake

## `files`

Generic uploaded file registry.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id not null` | |
| `kind` | `file_kind not null` | |
| `storage_provider` | `varchar not null` | `local`, `s3`, `r2` |
| `storage_key` | `varchar not null` | object key or local path |
| `original_filename` | `varchar` | |
| `mime_type` | `varchar` | |
| `size_bytes` | `bigint` | |
| `checksum` | `varchar` | optional dedupe |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `user_id`
- index on `kind`

## `resumes`

Represents the business concept of a resume, linked to an uploaded file.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id not null` | |
| `file_id` | `uuid fk -> files.id not null` | |
| `title` | `varchar` | user-friendly label |
| `version_label` | `varchar` | optional |
| `parse_status` | `parse_status not null default 'pending'` | |
| `is_default` | `boolean not null default false` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `user_id`
- index on `parse_status`

## `job_descriptions`

Stores either pasted JD content or uploaded JD files.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id not null` | |
| `company_name` | `varchar not null` | required — entered by user at session start |
| `role` | `varchar not null` | required — the role the user is applying for |
| `raw_text` | `text not null` | pasted JD content — used directly, no parsing needed |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `user_id`
- index on `company_name`
- index on `role`

## 7. Parsed Document Output

## `parsed_resumes`

Normalized parsed resume output.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `resume_id` | `uuid fk -> resumes.id unique not null` | one current parsed output |
| `full_text` | `text` | raw extracted text |
| `candidate_summary` | `text` | model-generated summary |
| `total_years_experience` | `numeric(4,1)` | nullable |
| `skills_json` | `jsonb not null default '[]'` | normalized skills array |
| `experience_json` | `jsonb not null default '[]'` | jobs/roles |
| `projects_json` | `jsonb not null default '[]'` | projects |
| `education_json` | `jsonb not null default '[]'` | education |
| `certifications_json` | `jsonb not null default '[]'` | optional |
| `parse_metadata_json` | `jsonb not null default '{}'` | parser details |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- unique index on `resume_id`
- gin index later on `skills_json` if needed


## 8. Interview Planning and Sessions

## `interview_templates`

Optional reusable config for interview types.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `name` | `varchar unique not null` | |
| `description` | `text` | |
| `interviewer_type` | `interviewer_type not null default 'ai'` | |
| `mode` | `interview_mode not null default 'voice'` | |
| `config_json` | `jsonb not null default '{}'` | rounds, timing, tone |
| `is_active` | `boolean not null default true` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

## `interview_sessions`

Primary interview session record.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id not null` | candidate owner |
| `resume_id` | `uuid fk -> resumes.id not null` | |
| `job_description_id` | `uuid fk -> job_descriptions.id not null` | |
| `template_id` | `uuid fk -> interview_templates.id` | optional |
| `status` | `interview_status not null default 'draft'` | |
| `mode` | `interview_mode not null default 'voice'` | voice only in v1 |
| `interview_type` | `varchar not null` | e.g. behavioral, technical, resume-based |
| `interviewer_type` | `interviewer_type not null default 'ai'` | |
| `title` | `varchar` | e.g. Backend Engineer Mock Interview |
| `interview_context_json` | `jsonb not null default '{}'` | resume + JD summary context |
| `plan_json` | `jsonb not null default '{}'` | generated interview plan |
| `question_count` | `int not null default 0` | |
| `duration_seconds` | `int` | completed session duration |
| `started_at` | `timestamptz` | |
| `completed_at` | `timestamptz` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `user_id`
- index on `status`
- index on `mode`
- index on `created_at desc`

## `session_participants`

Future-proof participant table for AI, candidate, human interviewer, reviewer.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `user_id` | `uuid fk -> users.id` | nullable for AI participant |
| `role` | `participant_role not null` | |
| `display_name` | `varchar` | |
| `external_ref` | `varchar` | useful for future integrations |
| `joined_at` | `timestamptz` | |
| `left_at` | `timestamptz` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `session_id`
- index on `role`

## `interview_turns`

Normalized transcript turn table. Central to text and voice flows.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `participant_id` | `uuid fk -> session_participants.id` | nullable if system-generated early |
| `speaker_type` | `speaker_type not null` | |
| `turn_kind` | `turn_kind not null` | |
| `sequence_no` | `int not null` | strictly ordered within session |
| `content_text` | `text not null` | final normalized text |
| `is_final` | `boolean not null default true` | useful for streaming states |
| `latency_ms` | `int` | optional |
| `metadata_json` | `jsonb not null default '{}'` | prompts, tokens, model info |
| `created_at` | `timestamptz not null default now()` | |

**Constraints**
- unique (`session_id`, `sequence_no`)

**Indexes**
- index on `session_id`
- index on `speaker_type`
- index on `created_at`

## `session_events`

Raw event log for realtime or replay support.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `event_type` | `session_event_type not null` | |
| `sequence_no` | `bigint not null` | event ordering |
| `payload_json` | `jsonb not null` | |
| `created_at` | `timestamptz not null default now()` | |

**Constraints**
- unique (`session_id`, `sequence_no`)

**Indexes**
- index on `session_id`
- index on `event_type`

## 9. Voice and Transcript Detail

## `transcript_chunks`

Stores partial or time-bounded transcript chunks, mainly for voice mode.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `turn_id` | `uuid fk -> interview_turns.id` | nullable until final turn created |
| `participant_id` | `uuid fk -> session_participants.id` | |
| `chunk_index` | `int not null` | |
| `text` | `text not null` | |
| `is_final` | `boolean not null default false` | |
| `start_ms` | `int` | |
| `end_ms` | `int` | |
| `provider_name` | `varchar` | STT provider |
| `provider_metadata_json` | `jsonb not null default '{}'` | |
| `created_at` | `timestamptz not null default now()` | |

**Constraints**
- unique (`session_id`, `participant_id`, `chunk_index`)

**Indexes**
- index on `session_id`
- index on `turn_id`

## `audio_assets`

Stores metadata for input or output audio tied to a session or turn.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `turn_id` | `uuid fk -> interview_turns.id` | |
| `participant_id` | `uuid fk -> session_participants.id` | |
| `file_id` | `uuid fk -> files.id not null` | points to audio file |
| `direction` | `varchar not null` | `input` or `output` |
| `duration_ms` | `int` | |
| `mime_type` | `varchar` | |
| `provider_name` | `varchar` | TTS/STT provider |
| `provider_metadata_json` | `jsonb not null default '{}'` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `session_id`
- index on `turn_id`

## 10. Evaluation and Reporting

## `skills`

Optional normalized skill taxonomy.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `name` | `varchar unique not null` | |
| `category` | `varchar` | e.g. backend, communication |
| `description` | `text` | |
| `created_at` | `timestamptz not null default now()` | |

## `session_questions`

Useful if you want a normalized table distinct from turns.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `turn_id` | `uuid fk -> interview_turns.id unique not null` | the AI question turn |
| `question_text` | `text not null` | |
| `question_type` | `varchar` | behavioral, technical, project, follow-up |
| `target_skill_id` | `uuid fk -> skills.id` | |
| `difficulty_level` | `varchar` | |
| `section_name` | `varchar` | opening, technical, closing |
| `metadata_json` | `jsonb not null default '{}'` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `session_id`
- index on `target_skill_id`

## `evaluations`

Generic evaluation records for turn-level and session-level scoring.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `turn_id` | `uuid fk -> interview_turns.id` | nullable for session-level |
| `question_id` | `uuid fk -> session_questions.id` | nullable |
| `scope` | `evaluation_scope not null` | |
| `skill_id` | `uuid fk -> skills.id` | nullable |
| `score_key` | `varchar not null` | e.g. `technical_depth` |
| `score_value` | `numeric(5,2)` | |
| `max_score` | `numeric(5,2)` | |
| `label` | `varchar` | e.g. good, average |
| `rationale` | `text` | |
| `improvement_note` | `text` | |
| `evaluator_metadata_json` | `jsonb not null default '{}'` | model/provider details |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `session_id`
- index on `turn_id`
- index on `skill_id`
- index on `score_key`

## `reports`

Final interview report for user-facing retrieval.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id unique not null` | one current final report |
| `overall_score` | `numeric(5,2)` | |
| `summary_text` | `text` | |
| `strengths_json` | `jsonb not null default '[]'` | |
| `weaknesses_json` | `jsonb not null default '[]'` | |
| `improvement_areas_json` | `jsonb not null default '[]'` | |
| `category_scores_json` | `jsonb not null default '{}'` | |
| `readiness_score` | `numeric(5,2)` | |
| `report_version` | `int not null default 1` | |
| `report_payload_json` | `jsonb not null default '{}'` | full structured payload |
| `generated_at` | `timestamptz not null default now()` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

**Indexes**
- unique index on `session_id`

## 11. Analytics and Longitudinal Tracking

## `analytics_snapshots`

Precomputed analytics for dashboards to avoid heavy live aggregations later.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `user_id` | `uuid fk -> users.id not null` | |
| `snapshot_type` | `varchar not null` | `score_trend`, `skill_trend`, `readiness` |
| `snapshot_date` | `date not null` | |
| `payload_json` | `jsonb not null` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `user_id`
- index on (`user_id`, `snapshot_type`, `snapshot_date`)

This table is optional early on. You can compute analytics from `reports` and `evaluations` first.

## 12. Human Reviewer and Notes

## `reviewer_notes`

Future support for human interviewer or reviewer annotations.

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `session_id` | `uuid fk -> interview_sessions.id not null` | |
| `reviewer_user_id` | `uuid fk -> users.id not null` | |
| `turn_id` | `uuid fk -> interview_turns.id` | nullable for session-wide note |
| `note_text` | `text not null` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `session_id`
- index on `reviewer_user_id`

## 13. Organization and Integrations

These can be added later, but the schema should anticipate them.

## `organizations`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `name` | `varchar not null` | |
| `slug` | `varchar unique not null` | |
| `is_active` | `boolean not null default true` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

## `organization_members`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `organization_id` | `uuid fk -> organizations.id not null` | |
| `user_id` | `uuid fk -> users.id not null` | |
| `member_role` | `varchar not null` | `owner`, `admin`, `viewer` |
| `created_at` | `timestamptz not null default now()` | |

**Constraints**
- unique (`organization_id`, `user_id`)

## `api_keys`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `organization_id` | `uuid fk -> organizations.id not null` | |
| `name` | `varchar not null` | |
| `key_prefix` | `varchar not null` | for lookup |
| `key_hash` | `varchar not null` | never store raw key |
| `permissions_json` | `jsonb not null default '{}'` | |
| `last_used_at` | `timestamptz` | |
| `expires_at` | `timestamptz` | |
| `revoked_at` | `timestamptz` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `organization_id`
- unique index on `key_prefix`

## `webhook_subscriptions`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `organization_id` | `uuid fk -> organizations.id not null` | |
| `target_url` | `text not null` | |
| `event_types_json` | `jsonb not null default '[]'` | |
| `secret_hash` | `varchar not null` | |
| `status` | `webhook_status not null default 'active'` | |
| `created_at` | `timestamptz not null default now()` | |
| `updated_at` | `timestamptz not null default now()` | |

## `webhook_deliveries`

| Column | Type | Notes |
|---|---|---|
| `id` | `uuid pk` | |
| `subscription_id` | `uuid fk -> webhook_subscriptions.id not null` | |
| `event_type` | `varchar not null` | |
| `payload_json` | `jsonb not null` | |
| `http_status` | `int` | |
| `attempt_count` | `int not null default 0` | |
| `last_attempt_at` | `timestamptz` | |
| `delivered_at` | `timestamptz` | |
| `created_at` | `timestamptz not null default now()` | |

**Indexes**
- index on `subscription_id`
- index on `event_type`
- index on `delivered_at`

## 14. Relationship Summary

### MVP-critical relationships
- `users` 1 -> many `resumes`
- `users` 1 -> many `job_descriptions`
- `users` 1 -> many `interview_sessions`
- `resumes` 1 -> 1 `parsed_resumes`
- `interview_sessions` 1 -> many `interview_turns`
- `interview_sessions` 1 -> many `transcript_chunks`
- `interview_sessions` 1 -> many `audio_assets`
- `interview_sessions` 1 -> 1 `reports`
- `interview_sessions` 1 -> many `evaluations`

### Future-facing relationships
- `interview_sessions` 1 -> many `session_participants`
- `organizations` 1 -> many `api_keys`
- `organizations` 1 -> many `webhook_subscriptions`

## 15. MVP Schema Recommendation

If you want to stay lean initially, build these tables first:

- `users`
- `user_profiles`
- `files`
- `resumes`
- `job_descriptions`
- `parsed_resumes`
- `interview_sessions`
- `session_participants`
- `interview_turns`
- `transcript_chunks`
- `audio_assets`
- `evaluations`
- `reports`

You can defer these until later:

- `session_events`
- `skills`
- `session_questions`
- `analytics_snapshots`
- `reviewer_notes`
- `organizations`
- `api_keys`
- `webhook_subscriptions`
- `webhook_deliveries`

## 16. Suggested Implementation Order

### Step 1: Account and file intake
- `users`
- `user_profiles`
- `files`
- `resumes`
- `job_descriptions`

### Step 2: Parsing output
- `parsed_resumes`

### Step 3: Interview engine
- `interview_sessions`
- `session_participants`
- `interview_turns`
- `transcript_chunks`
- `audio_assets`

### Step 4: Evaluation and report
- `evaluations`
- `reports`

### Step 5: Realtime and voice hardening
- `session_events`

### Step 6: Analytics and integrations
- `skills`
- `session_questions`
- `analytics_snapshots`
- `organizations`
- `api_keys`
- `webhook_subscriptions`
- `webhook_deliveries`

## 17. Notes on JSONB vs Fully Normalized Tables

Use `jsonb` early for:
- parser output
- interview context
- report payloads
- provider metadata

Use normalized tables early for:
- users
- resumes
- job descriptions
- interview sessions
- turns
- evaluations
- reports

Reason:
- `jsonb` gives you speed while you are still learning and iterating on output shape
- normalized tables are better for data you will query often and build features around

## 18. Recommendation for Your First Migration Set

For the first build, I would create these migrations first:

1. `users` ✅
2. `user_profiles`
3. `files` ✅
4. `resumes` ✅
5. `job_descriptions` ✅ (migration update needed: add `role not null`, make `company_name not null`, drop `title`/`source_url`/`parse_status`)
6. `parsed_resumes` ✅
7. `interview_sessions`
8. `session_participants`
9. `interview_turns`
10. `transcript_chunks`
11. `audio_assets`
12. `evaluations`
13. `reports`

This is enough to support:
- auth
- uploads
- resume parsing
- voice interviews
- transcript storage
- audio metadata storage
- final reports
- structured scoring
