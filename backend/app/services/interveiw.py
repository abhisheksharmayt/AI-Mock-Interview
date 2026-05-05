from app.schemas.interview import (
    InterviewSessionCreate,
    InterviewSession,
    PromptContext,
)
from app.common.enums import InterviewStatus, InterviewType, ParseStatus
from app.repositories.resume import ResumeRepository
from app.services.prompt import PromptRenderer
from app.repositories.interview import InterviewRepository
from app.utils.openai_utils import generate_interview_question
from app.utils.cartesia_utils import CartesiaSessionManager
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, HTTPException
from app.db.database import get_db_session
from uuid import UUID
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user
from app.core.configs import configs
from loguru import logger
from app.utils.amazon_utils import AmazonUtils


class InterviewService:

    def __init__(
        self,
        db: AsyncSession = Depends(get_db_session),
        user: UserResponse = Depends(get_current_user)
    ):
        self.db = db
        self.interview_repo = InterviewRepository(db)
        self.interview_context_assembler = InterviewContextAssembler(db,user)
        self.cartesia_session_manager = CartesiaSessionManager()
        self.amazon_utils = AmazonUtils()
        self.user = user
    
    async def create_interview_session(
        self, interview_session_create: InterviewSessionCreate
    ) -> InterviewSession:
        try:
            interview_context_json = await self.interview_context_assembler.build(
                resume_id=interview_session_create.resume_id,
                jd_id=interview_session_create.job_description_id,
                interview_type=interview_session_create.interview_type,
            )

            interview_session = await self.interview_repo.create_interview_session(
                interview_session_create,
                status=InterviewStatus.in_progress,
                interview_context_json={"prompt": interview_context_json},
                user_id = self.user.id
            )

            first_question = generate_interview_question(
                prompt=interview_session.interview_context_json["prompt"],
                turns=[],
            )
            
            session_id_str = str(interview_session.id)
            audio_key = f"interview_session_{session_id_str}/0.wav"

            self.cartesia_session_manager.get_or_create(session_id_str)
            audio_bytes = self.cartesia_session_manager.text_to_speech(session_id_str, first_question)
            self.cartesia_session_manager.close(session_id_str)

            self.amazon_utils.upload_file_as_object(
                audio_bytes,
                configs.S3_RESUME_BUCKET,
                audio_key,
            )
            audio_url = self.amazon_utils.generate_presigned_url(configs.S3_RESUME_BUCKET, audio_key)

            return {
                "session_id": interview_session.id,
                "question_text": first_question,
                "audio_url": audio_url,
            }
        except Exception:
            logger.exception("Error while creating interview session")
            raise


class InterviewContextAssembler:
    def __init__(
        self,
        db: AsyncSession,
        user: UserResponse,
    ):
        self.db = db
        self.user = user
        self.resume_repo = ResumeRepository(db)

    async def build(
        self,
        resume_id: UUID,
        jd_id: UUID,
        interview_type: InterviewType,
        prompt_renderer: PromptRenderer = PromptRenderer(),
    ) -> str:
        try:
            resume = await self.resume_repo.get_resume_by_id(resume_id)
            if resume.parse_status != ParseStatus.completed:
                raise HTTPException(
                    status_code=409, detail=f"Resume {resume.title} is not parsed"
                )
            parsed_resume =  await self.resume_repo.get_parsed_resume_by_id(resume_id)
            logger.info(f"parsed resume {parsed_resume}")
            jd = await self.resume_repo.get_jd_by_id(jd_id)
            context = PromptContext(
                candidate_name=self.user.full_name,
                resume_summary=parsed_resume.full_text,
                role=jd.role,
                company_name=jd.company_name,
                years_of_experience=int(parsed_resume.total_years_experience),
                key_skills=parsed_resume.skills_json,
                jd_highlights=jd.raw_text,
            )
            rendered_prompt = prompt_renderer.render(
                interview_type=interview_type, context=context
            )

            return rendered_prompt

        except HTTPException as e:
            raise e
        except Exception:
            logger.exception("Error while building interview context")
            raise
