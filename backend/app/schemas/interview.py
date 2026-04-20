from datetime import datetime
from typing import Any, Optional
from app.common.enums import InterviewerType, InterviewType, InterviewMode
from app.models.base import BaseModel
from uuid import UUID
from sqlmodel import SQLModel


class InterviewSessionCreate(BaseModel):
    resume_id: UUID
    job_description_id: UUID
    template_id: Optional[UUID] = None
    interviewer_type: InterviewerType = InterviewerType.ai
    mode: InterviewMode = InterviewMode.voice
    company_name: str
    role: str
    interview_type: InterviewType
    question_count: int
    title: Optional[str] = None
    interview_context_json: Optional[dict[str, Any]] = None


class InterviewSession(BaseModel):
    id: UUID
    user_id: UUID
    resume_id: UUID
    job_description_id: UUID
    template_id: Optional[UUID] = None
    interviewer_type: InterviewerType = InterviewerType.ai
    mode: InterviewMode = InterviewMode.voice
    company_name: str
    role: str
    interview_type: InterviewType

class PromptContext(SQLModel):
    candidate_name: str
    role: str
    company_name: str
    resume_summary: str
    years_of_experience: int
    key_skills: list[str]
    jd_highlights: str