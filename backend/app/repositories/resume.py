from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.resume import File, Resume
from app.schemas.resume import FileUpload, ResumeUpload


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
