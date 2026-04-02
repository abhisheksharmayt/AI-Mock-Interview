from io import BytesIO

from fastapi import Depends, HTTPException, UploadFile
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.enums import FileKind, ParseStatus
from app.core.configs import configs
from app.core.dependencies import get_current_user
from app.db.database import get_db_session
from app.models.resume import Resume
from app.repositories.resume import ResumeRepository
from app.schemas.resume import FileUpload, ResumeUpload
from app.schemas.user import UserResponse
from app.utils.amazon_utils import AmazonUtils


class ResumeService:
    def __init__(
        self,
        db: AsyncSession = Depends(get_db_session),
        user: UserResponse = Depends(get_current_user),
    ):
        self.user = user
        self.resume_repo = ResumeRepository(db)
        self.allowed_extensions = [".pdf", ".doc", ".docx"]
        self.amazon_utils = AmazonUtils()
        self.resume_path = "resumes/"

    async def upload_resume(self, file: UploadFile) -> Resume:
        logger.info("Uploading resume: {}", file.filename)

        if not any(file.filename.endswith(ext) for ext in self.allowed_extensions):
            raise HTTPException(status_code=400, detail="Invalid file extension")

        file_content = await file.read()
        file_name = file.filename
        file_size = len(file_content)
        storage_key = f"{self.resume_path}{file_name}"

        resume_data = ResumeUpload(
            user_id=self.user.id,
            file_name=file_name,
            file_size=file_size,
            parse_status=ParseStatus.pending,
            is_default=False,
        )
        file_upload_data = FileUpload(
            user_id=self.user.id,
            kind=FileKind.resume,
            storage_key=storage_key,
            original_filename=file_name,
        )

        bucket = configs.S3_RESUME_BUCKET

        try:
            self.amazon_utils.upload_file_as_object(
                BytesIO(file_content), bucket, storage_key
            )
        except Exception as e:
            logger.exception("Error while uploading resume to object storage")
            raise HTTPException(
                status_code=503,
                detail="Could not store file. Please try again.",
            ) from e

        try:
            return await self.resume_repo.create_file_and_resume(
                file_upload_data, resume_data
            )
        except Exception:
            try:
                self.amazon_utils.delete_object(bucket, storage_key)
            except Exception as del_err:
                logger.warning(
                    "Failed to delete orphan object storage key {}: {}",
                    storage_key,
                    del_err,
                )
            raise
