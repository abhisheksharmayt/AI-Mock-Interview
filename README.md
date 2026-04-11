# AI Mock Interview Platform

> Work in progress.

AI-powered mock interview platform that delivers personalized, voice-first interviews based on a candidate's resume and job description.

## Stack

- **Backend:** FastAPI, PostgreSQL, SQLAlchemy (async), Alembic
- **AI:** OpenAI API
- **Storage:** AWS S3 / MinIO (local)
- **Auth:** JWT

## Local Setup

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
alembic upgrade head
uvicorn app.main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## Environment Variables

See [`backend/.env.example`](backend/.env.example).
