from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSession,
    PromptContext,
)
from app.common.enums import InterviewType, ParseStatus
from app.repositories.resume import ResumeRepository
from app.services.prompt import PromptRenderer
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from app.db.database import get_db_session
from uuid import UUID
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user
from loguru import logger


class InterviewService:

    def __init__(
        self,
        db: AsyncSession = Depends(get_db_session),
    ):
        self.db = db

    async def create_interview_session(
        self, interview_session_create: InterviewSessionCreate
    ) -> InterviewSession:
        pass


class InterviewContextAssembler:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db_session),
        user: UserResponse = Depends(get_current_user),
    ):
        self.db = db
        self.user = user
        self.resume_repo = ResumeRepository(db)

    async def build(
        self, resume_id: UUID, jd_id: UUID, prompt_renderer: PromptRenderer
    ) -> PromptContext:
        try:
            resume = await self.resume_repo.get_resume_by_id(resume_id)
            if resume.parse_status != ParseStatus.completed:
                raise HTTPException(
                    status_code=409, detail=f"Resume {resume.title} is not parsed"
                )
            jd = await self.resume_repo.get_jd_by_id(jd_id)
            context = PromptContext(
                candidate_name=self.user.full_name,
                resume_summary=resume.full_text,
                role=jd.role,
                company_name=jd.company_name,
                years_of_experience=resume.total_years_experience,
                key_skills=resume.skills_json,
                jd_highlights=jd.raw_text,
            )
            rendered_prompt = prompt_renderer.render(
                interview_type=InterviewType.behavioral, context=context
            )

            return rendered_prompt
            
        except HTTPException as e:
            raise e
        except Exception:
            logger.exception("Error while building interview context")
            raise
