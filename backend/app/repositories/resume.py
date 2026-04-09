from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.resume import File, JobDescription, Resume
from app.schemas.resume import FileUpload, JobDescriptionCreate, ResumeUpload


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

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