from datetime import datetime
from typing import Any
from app.common.enums import InterviewerType
from app.models.base import BaseModel
from uuid import UUID


class InterviewSessionCreate(BaseModel):
    resume_id: UUID
    job_description_text: str
    company_name: str
    role: str
    interview_type: str
    question_count: int