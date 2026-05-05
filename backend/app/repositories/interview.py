from uuid import UUID
from app.schemas.interview import InterviewSession, InterviewSessionCreate
from app.common.enums import InterviewStatus
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from sqlalchemy import update
from app.models.interview import InterviewSession as InterviewSessionModel


class InterviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_interview_session(
        self,
        interview_session: InterviewSessionCreate,
        status: InterviewStatus,
        interview_context_json: str,
        user_id: str,
    ) -> InterviewSession:
        try:
            session_model = InterviewSessionModel(
                user_id=user_id,
                resume_id=interview_session.resume_id,
                job_description_id=interview_session.job_description_id,
                status=status,
                interview_type=interview_session.interview_type.value,
                title=interview_session.title,
                interview_context_json=interview_context_json,
            )
            self.db.add(session_model)
            await self.db.commit()
            await self.db.refresh(session_model)
            return session_model
        except Exception:
            await self.db.rollback()
            logger.exception("Error while creating interview session")
            raise

    async def update_session_status(
        self, session_id: UUID, status: InterviewStatus
    ) -> None:
        try:
            stmt = (
                update(InterviewSessionModel)
                .where(InterviewSessionModel.id == session_id)
                .values(status=status)
            )
            await self.db.execute(stmt)
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            logger.exception("Error while updating interview session status")
            raise
