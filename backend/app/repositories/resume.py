from uuid import UUID
from app.common.enums import ParseStatus
from app.schemas.openai import OpenAIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.resume import File, JobDescription, ParsedResume, Resume
from app.schemas.resume import FileUpload, JobDescriptionCreate, ParsedResumeCreate, ParsedResumeResponse, ResumeUpload


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_file_by_id(self, file_id: UUID) -> File:
        try:
            file_record = await self.db.get(File, file_id)
            if not file_record:
                raise Exception(f"File not found: {file_id}")
            return file_record
        except Exception:
            logger.exception("Error while getting file by id")
            raise

    async def create_file_and_resume(
        self, file_upload_data: FileUpload, resume_upload_data: ResumeUpload
    ) -> Resume:
        try:
            file_record = File(
                user_id=file_upload_data.user_id,
                kind=file_upload_data.kind,
                storage_key=file_upload_data.storage_key,
                original_filename=file_upload_data.original_filename,
            )
            resume_record = Resume(
                user_id=resume_upload_data.user_id,
                file_id=file_record.id,
                title=resume_upload_data.file_name,
                parse_status=resume_upload_data.parse_status,
                is_default=resume_upload_data.is_default,
            )
            self.db.add(file_record)
            self.db.add(resume_record)
            await self.db.commit()
            await self.db.refresh(resume_record)
            logger.info(
                "File and resume records created successfully: resume_id=%s file_id=%s",
                resume_record.id,
                file_record.id,
            )
            return resume_record
        except Exception:
            await self.db.rollback()
            logger.exception("Error while creating file and resume records")
            raise

    async def get_resume_by_id(self, resume_id: UUID) -> Resume:
        try:
            resume_record = await self.db.get(Resume, resume_id)
            if not resume_record:
                raise Exception(f"Resume not found: {resume_id}")
            return resume_record
        except Exception:
            logger.exception("Error while getting resume by id")
            raise

    async def update_resume_parse_status(self, resume_id: UUID, status: ParseStatus) -> Resume:
        try:
            resume_record = await self.db.get(Resume, resume_id)
            if not resume_record:
                raise Exception(f"Resume not found: {resume_id}")
            resume_record.parse_status = status
            await self.db.commit()
            await self.db.refresh(resume_record)
            logger.info(
                "Resume parse status updated successfully: id=%s status=%s", resume_record.id, status,
            )
            return resume_record
        except Exception:
            logger.exception("Error while updating resume parse status")
            raise


    async def create_parsed_resume(self, resume_id: UUID, full_text: str, parsed_resume_data: OpenAIResponse) -> ParsedResumeResponse:
        try:
            data = parsed_resume_data.model_dump()
            parsed_resume_record = ParsedResume(
                resume_id=resume_id,
                full_text=full_text,
                skills_json=data["skills_json"],
                experience_json=data["experience_json"],
                education_json=data["education_json"],
                projects_json=data["projects_json"],
                certifications_json=data["certifications_json"],
                candidate_summary=data["candidate_summary"],
                total_years_experience=data["total_years_experience"],
            )
            self.db.add(parsed_resume_record)
            await self.db.commit()
            await self.db.refresh(parsed_resume_record)
            logger.info(
                "Parsed resume record created successfully: id=%s", parsed_resume_record.id,
            )
            return ParsedResumeResponse.model_validate(parsed_resume_record)
        except Exception:
            await self.db.rollback()
            logger.exception("Error while creating parsed resume record")
            raise

    async def update_resume_parse_status(self, resume_id: UUID, status: ParseStatus) -> Resume:
        try:
            resume_record = await self.db.get(Resume, resume_id)
            if not resume_record:
                raise Exception(f"Resume not found: {resume_id}")
            resume_record.parse_status = status
            await self.db.commit()
            await self.db.refresh(resume_record)
            logger.info(
                "Resume parse status updated successfully: id=%s status=%s", resume_record.id, status,
            )
            return resume_record
        except Exception:
            await self.db.rollback()
            logger.exception("Error while updating resume parse status")
            raise
    
    async def create_jd(self, jd_data: JobDescriptionCreate, user_id: UUID) -> JobDescription:
        try:
            jd_record = JobDescription(
                user_id=user_id,
                title=jd_data.title,
                role=jd_data.role,
                company_name=jd_data.company_name,
                raw_text=jd_data.raw_text,
            )
            self.db.add(jd_record)
            await self.db.commit()
            await self.db.refresh(jd_record)
            logger.info(
                "JD record created successfully: id=%s", jd_record.id,
            )
            return jd_record
        except Exception:
            await self.db.rollback()
            logger.exception("Error while creating JD record")
            raise
    
    async def get_jd_by_id(self, jd_id: UUID) -> JobDescription:
        try:
            jd_record = await self.db.get(JobDescription, jd_id)
            if not jd_record:
                raise Exception(f"JD not found: {jd_id}")
            return jd_record
        except Exception:
            logger.exception("Error while getting JD by id")
            raise